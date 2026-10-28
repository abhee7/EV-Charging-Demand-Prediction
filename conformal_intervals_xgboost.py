"""Conformalized quantile regression (CQR) intervals for the existing quantile XGBoost setup.

Protocol (test targets are never used for fitting or calibration):
  1. Fit quantile XGBoost [0.05, 0.5, 0.95] on TRAIN rows only (index < 70% split).
  2. Run the existing recursive 24h forecast over the VALIDATION windows; compute CQR
     conformity scores  s = max(lo - y, y - hi).
  3. q_hat = ceil((n+1)(1-alpha))/n empirical quantile of the scores, alpha = 0.10.
  4. Apply the SAME train-only model to the 45 TEST windows (history = actuals before each
     window, as in the existing pipeline) and widen:  [lo - q_hat, hi + q_hat].
Writes ONLY to results/conformal_prediction_intervals/."""
import os, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import xgboost
from xgboost import XGBRegressor
warnings.filterwarnings("ignore")

INPUT_FILE = "data/processed/model_data.csv"
OUT = "results/conformal_prediction_intervals"; FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)
LOCAL_TZ = "America/Los_Angeles"; TARGET = "demand_kWh"
QUANTILES = [0.05, 0.5, 0.95]; NOMINAL = 0.90; ALPHA = 1 - NOMINAL
FEATURES = ["lag_1","lag_2","lag_24","lag_48","lag_168","lag_336","rolling_mean_24",
            "rolling_std_24","rolling_mean_168","rolling_std_168","hour","day_of_week",
            "day_of_month","month","week_of_year","is_weekend","is_business_hour"]
PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8,
              colsample_bytree=0.8, objective="reg:quantileerror",
              quantile_alpha=np.array(QUANTILES), random_state=42, n_jobs=-1)

df = pd.read_csv(INPUT_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
df = df.sort_values("timestamp").reset_index(drop=True)
n = len(df); train_end = int(n*0.70); validation_end = int(n*0.85)

def make_features(history, timestamp):     # identical to train_models.py
    history = np.asarray(history, dtype=float)
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None: ts = ts.tz_localize("UTC")
    lt = ts.tz_convert(LOCAL_TZ)
    f = {"lag_1":history[-1],"lag_2":history[-2],"lag_24":history[-24],"lag_48":history[-48],
         "lag_168":history[-168],"lag_336":history[-336],
         "rolling_mean_24":np.mean(history[-24:]),"rolling_std_24":np.std(history[-24:],ddof=1),
         "rolling_mean_168":np.mean(history[-168:]),"rolling_std_168":np.std(history[-168:],ddof=1),
         "hour":lt.hour,"day_of_week":lt.dayofweek,"day_of_month":lt.day,"month":lt.month,
         "week_of_year":int(lt.isocalendar().week),"is_weekend":int(lt.dayofweek>=5),
         "is_business_hour":int(8<=lt.hour<18)}
    return pd.DataFrame([[f[c] for c in FEATURES]], columns=FEATURES)

def recursive_quantile_forecast(model, history_values, start_timestamp):
    """Same recursion as the baseline interval experiment: median is fed back (clipped at 0);
    returns RAW sorted quantiles (no clipping) so conformity scores are not distorted."""
    history = list(np.asarray(history_values, dtype=float)); out = []; ts = pd.Timestamp(start_timestamp)
    for _ in range(24):
        q = np.sort(model.predict(make_features(history, ts))[0].astype(float))
        out.append(q); history.append(max(0.0, q[1])); ts += pd.Timedelta(hours=1)
    return np.array(out)

def windows(a, b):
    w = []; c = a
    while c + 24 <= b: w.append((c, c+24)); c += 24
    return w

# ---- 1. fit on TRAIN only ----
train = df.iloc[:train_end].dropna(subset=FEATURES)
assert train.index.max() < train_end
model = XGBRegressor(**PARAMS).fit(train[FEATURES], train[TARGET])

# ---- 2. validation scores (validation targets only; test untouched) ----
val_windows = windows(train_end, validation_end)
vrows = []
for w, (s, e) in enumerate(val_windows, 1):
    q = recursive_quantile_forecast(model, df[TARGET].values[:s], df.timestamp[s])
    for h in range(24):
        y = df[TARGET][s+h]; vrows.append(dict(window=w, horizon=h+1, y=y, lo=q[h,0], med=q[h,1], hi=q[h,2]))
V = pd.DataFrame(vrows)
V["score"] = np.maximum(V.lo - V.y, V.y - V.hi)
n_cal = len(V)
level = min(1.0, np.ceil((n_cal + 1) * (1 - ALPHA)) / n_cal)
q_hat = float(np.quantile(V.score.values, level, method="higher"))
val_cov_before = float(((V.y >= V.lo) & (V.y <= V.hi)).mean())
val_cov_after = float(((V.y >= V.lo - q_hat) & (V.y <= V.hi + q_hat)).mean())
print(f"XGBoost {xgboost.__version__} | calibration n={n_cal} ({len(val_windows)} windows) | q_hat={q_hat:.4f} kWh")
print(f"validation coverage before={val_cov_before:.3f} after={val_cov_after:.3f}")

# ---- 3/4. test evaluation (test targets used ONLY for scoring) ----
test_windows = windows(validation_end, n)
assert len(test_windows) == 45
rows = []
for w, (s, e) in enumerate(test_windows, 1):
    q = recursive_quantile_forecast(model, df[TARGET].values[:s], df.timestamp[s])
    for h in range(24):
        rows.append(dict(forecast_window=w, horizon=h+1, timestamp=df.timestamp[s+h], actual_demand=df[TARGET][s+h],
                         raw_lower=max(0.0, q[h,0]), median_prediction=max(0.0, q[h,1]), raw_upper=max(0.0, q[h,2]),
                         lower_bound=max(0.0, q[h,0] - q_hat), upper_bound=q[h,2] + q_hat))
P = pd.DataFrame(rows)
P["interval_width"] = P.upper_bound - P.lower_bound
P["inside_interval"] = (P.actual_demand >= P.lower_bound) & (P.actual_demand <= P.upper_bound)
P["raw_inside_interval"] = (P.actual_demand >= P.raw_lower) & (P.actual_demand <= P.raw_upper)
peak_thr = float(P.actual_demand.quantile(0.90))
P["is_peak"] = P.actual_demand >= peak_thr
P.to_csv(os.path.join(OUT, "conformal_predictions.csv"), index=False)

err = P.actual_demand - P.median_prediction
mae, rmse = float(err.abs().mean()), float(np.sqrt((err**2).mean()))
cov = float(P.inside_interval.mean()); width = float(P.interval_width.mean())
S = pd.DataFrame([dict(xgboost_version=xgboost.__version__, nominal_coverage=NOMINAL, empirical_coverage=cov,
    coverage_minus_nominal=cov-NOMINAL, mean_interval_width=width, median_interval_width=float(P.interval_width.median()),
    median_pred_MAE=mae, median_pred_RMSE=rmse, n_observations=len(P), n_windows=len(test_windows),
    below_lower_pct=float((P.actual_demand < P.lower_bound).mean()), above_upper_pct=float((P.actual_demand > P.upper_bound).mean()),
    conformal_q_hat_kWh=q_hat, n_calibration_scores=n_cal, calibration_windows=len(val_windows),
    validation_coverage_before=val_cov_before, validation_coverage_after=val_cov_after,
    uncalibrated_test_coverage_same_model=float(P.raw_inside_interval.mean()),
    uncalibrated_test_width_same_model=float((P.raw_upper - P.raw_lower).mean()),
    peak_threshold_P90_kWh=peak_thr, train_rows=len(train))])
S.to_csv(os.path.join(OUT, "conformal_summary.csv"), index=False)

H = P.groupby("horizon").agg(coverage=("inside_interval","mean"), uncalibrated_coverage=("raw_inside_interval","mean"),
                             mean_interval_width=("interval_width","mean"), n=("inside_interval","size")).reset_index()
H["nominal_coverage"] = NOMINAL
H.to_csv(os.path.join(OUT, "conformal_horizon_coverage.csv"), index=False)

rows_pk = []
for flag, label in [(False, "Non-peak"), (True, "Peak (actual >= test-period P90)")]:
    d = P[P.is_peak == flag]
    rows_pk.append(dict(period=label, coverage=float(d.inside_interval.mean()), mean_interval_width=float(d.interval_width.mean()),
        median_pred_MAE=float((d.actual_demand-d.median_prediction).abs().mean()), n=len(d),
        below_lower=float((d.actual_demand < d.lower_bound).mean()), above_upper=float((d.actual_demand > d.upper_bound).mean()),
        nominal_coverage=NOMINAL, peak_threshold_kWh=peak_thr))
PK = pd.DataFrame(rows_pk); PK.to_csv(os.path.join(OUT, "conformal_peak_coverage.csv"), index=False)

# ---- comparison table (previous results are READ, not recomputed) ----
base = pd.read_csv("results/prediction_intervals/prediction_interval_summary.csv").iloc[0]
assert abs(base.peak_threshold_P90_kWh - peak_thr) < 1e-9, "peak threshold differs from baseline experiment"
sq = pd.read_csv("results/metrics/test_metrics_corrected.csv").set_index("Model").loc["XGBoost"]
CMP = pd.DataFrame([
    dict(Method="Original squared-error XGBoost", Nominal_Coverage="n/a (point forecast)", Actual_Coverage="n/a", Average_Width="n/a", MAE=sq.MAE, RMSE=sq.RMSE),
    dict(Method="Quantile XGBoost (5/50/95, uncalibrated)", Nominal_Coverage=NOMINAL, Actual_Coverage=base.empirical_coverage, Average_Width=base.mean_interval_width, MAE=base.median_pred_MAE, RMSE=base.median_pred_RMSE),
    dict(Method="Conformalized Quantile XGBoost", Nominal_Coverage=NOMINAL, Actual_Coverage=cov, Average_Width=width, MAE=mae, RMSE=rmse)])
CMP.to_csv(os.path.join(OUT, "method_comparison.csv"), index=False)

# ---- figures ----
for cols, yl, fn, ref in [(["coverage","uncalibrated_coverage"],"Empirical coverage","conformal_coverage_by_horizon.png",NOMINAL),
                          (["mean_interval_width"],"Mean interval width (kWh)","conformal_interval_width.png",None)]:
    fig, ax = plt.subplots(figsize=(9,4.5))
    ax.plot(H.horizon, H[cols[0]], marker="o", label="Conformalized" if len(cols)>1 else "Conformalized")
    if len(cols) > 1: ax.plot(H.horizon, H[cols[1]], marker="s", ls="--", label="Uncalibrated (same train-only model)")
    if ref: ax.axhline(ref, color="tab:red", ls=":", label=f"Nominal {ref:.0%}"); ax.set_ylim(0,1.02)
    else:
        raw_w = (P.raw_upper-P.raw_lower).groupby(P.horizon).mean(); ax.plot(H.horizon, raw_w.values, marker="s", ls="--", label="Uncalibrated (same train-only model)")
    ax.legend(); ax.set_xlabel("Forecast horizon (hours ahead)"); ax.set_ylabel(yl); ax.set_title(yl + " by horizon")
    ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(FIG, fn), dpi=150); plt.close(fig)

sub = P[P.forecast_window > len(test_windows)-7]
t = sub.timestamp.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
fig, ax = plt.subplots(figsize=(12,4.8))
ax.fill_between(t, sub.lower_bound, sub.upper_bound, alpha=.25, label="Conformalized 90% interval")
ax.plot(t, sub.median_prediction, label="Median prediction", lw=1.4); ax.plot(t, sub.actual_demand, color="k", lw=1, label="Actual")
out = sub[~sub.inside_interval]; ax.scatter(t[out.index], out.actual_demand, color="tab:red", s=18, zorder=3, label="Outside interval")
ax.set_ylabel("Demand (kWh)"); ax.set_title(f"Conformalized quantile XGBoost, last 7 test days (overall test coverage {cov:.1%})")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(FIG, "conformal_prediction_intervals.png"), dpi=150); plt.close(fig)

pd.set_option("display.width", 220)
print(); print(S.T.to_string()); print(); print(H.round(3).to_string(index=False)); print(); print(PK.round(3).to_string(index=False))
print(); print(CMP.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
