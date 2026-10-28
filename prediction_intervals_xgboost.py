"""Quantile-regression prediction intervals for the existing XGBoost setup.
Same split (70/15/15), same features, same 45 recursive 24-hour test windows,
same hyperparameters as train_models.py candidate 1; only the objective changes to
reg:quantileerror with quantile_alpha = [0.05, 0.5, 0.95].
Writes ONLY to results/prediction_intervals/."""
import os, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import xgboost
from xgboost import XGBRegressor
warnings.filterwarnings("ignore")

INPUT_FILE = "data/processed/model_data.csv"
OUT = "results/prediction_intervals"; FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)
LOCAL_TZ = "America/Los_Angeles"; TARGET = "demand_kWh"
QUANTILES = [0.05, 0.5, 0.95]
NOMINAL = 0.90
FEATURES = ["lag_1","lag_2","lag_24","lag_48","lag_168","lag_336","rolling_mean_24",
            "rolling_std_24","rolling_mean_168","rolling_std_168","hour","day_of_week",
            "day_of_month","month","week_of_year","is_weekend","is_business_hour"]
# Existing hyperparameters (train_models.py XGBoost candidate 1); only the objective differs.
PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8,
              colsample_bytree=0.8, objective="reg:quantileerror",
              quantile_alpha=np.array(QUANTILES), random_state=42, n_jobs=-1)

print("XGBoost version:", xgboost.__version__)
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

def recursive_interval_forecast(model, history_values, start_timestamp):
    """Recursive 24h forecast. The MEDIAN is fed back into history (consistent with the
    existing point-forecast logic); lower/upper are not fed back."""
    history = list(np.asarray(history_values, dtype=float)); out = []; ts = pd.Timestamp(start_timestamp)
    crossings = 0
    for _ in range(24):
        q = model.predict(make_features(history, ts))[0].astype(float)
        if not (q[0] <= q[1] <= q[2]): crossings += 1
        q = np.sort(q)                              # remove quantile crossing
        q = np.maximum(q, 0.0)                      # demand cannot be negative
        out.append(q); history.append(q[1]); ts += pd.Timedelta(hours=1)
    return np.array(out), crossings

# ---- train on train+validation only (as the existing final test phase does) ----
tv = df.iloc[:validation_end].dropna(subset=FEATURES)
assert tv.index.max() < validation_end
model = XGBRegressor(**PARAMS).fit(tv[FEATURES], tv[TARGET])

windows = []; c = validation_end
while c + 24 <= n: windows.append((c, c+24)); c += 24
print(f"{len(windows)} test windows, {len(windows)*24} hours")

rows = []; total_crossings = 0
for w, (s, e) in enumerate(windows, 1):
    hist = df[TARGET].values[:s]
    q, cr = recursive_interval_forecast(model, hist, df.timestamp[s]); total_crossings += cr
    for h in range(24):
        rows.append(dict(forecast_window=w, horizon=h+1, timestamp=df.timestamp[s+h],
                         actual_demand=df[TARGET][s+h], lower_bound=q[h,0],
                         median_prediction=q[h,1], upper_bound=q[h,2]))
P = pd.DataFrame(rows)
P["interval_width"] = P.upper_bound - P.lower_bound
P["inside_interval"] = (P.actual_demand >= P.lower_bound) & (P.actual_demand <= P.upper_bound)
peak_thr = float(P.actual_demand.quantile(0.90))   # same definition as run_peak_analysis.py: test-period P90
P["is_peak"] = P.actual_demand >= peak_thr
P.to_csv(os.path.join(OUT, "prediction_intervals.csv"), index=False)

# ---- metrics ----
def cov(d): return float(d.inside_interval.mean())
err = P.actual_demand - P.median_prediction
S = pd.DataFrame([dict(
    xgboost_version=xgboost.__version__, nominal_coverage=NOMINAL, empirical_coverage=cov(P),
    coverage_minus_nominal=cov(P)-NOMINAL, mean_interval_width=P.interval_width.mean(),
    median_interval_width=P.interval_width.median(), median_pred_MAE=float(err.abs().mean()),
    median_pred_RMSE=float(np.sqrt((err**2).mean())), n_observations=len(P), n_windows=len(windows),
    below_lower_pct=float((P.actual_demand < P.lower_bound).mean()),
    above_upper_pct=float((P.actual_demand > P.upper_bound).mean()),
    quantile_crossings_before_sorting=total_crossings, peak_threshold_P90_kWh=peak_thr,
    train_rows=len(tv))])
S.to_csv(os.path.join(OUT, "prediction_interval_summary.csv"), index=False)

H = P.groupby("horizon").agg(coverage=("inside_interval","mean"), mean_interval_width=("interval_width","mean"),
                             n=("inside_interval","size")).reset_index()
H["nominal_coverage"] = NOMINAL
H.to_csv(os.path.join(OUT, "horizon_coverage.csv"), index=False)

PK = P.groupby("is_peak").agg(coverage=("inside_interval","mean"), mean_interval_width=("interval_width","mean"),
        median_pred_MAE=("actual_demand", lambda s: float((s - P.loc[s.index,"median_prediction"]).abs().mean())),
        n=("inside_interval","size"), below_lower=("actual_demand", lambda s: float((s < P.loc[s.index,"lower_bound"]).mean())),
        above_upper=("actual_demand", lambda s: float((s > P.loc[s.index,"upper_bound"]).mean()))).reset_index()
PK.insert(0, "period", PK.is_peak.map({True:"Peak (actual >= test-period P90)", False:"Non-peak"}))
PK["nominal_coverage"] = NOMINAL; PK["peak_threshold_kWh"] = peak_thr
PK.drop(columns="is_peak").to_csv(os.path.join(OUT, "peak_coverage.csv"), index=False)

# ---- figures ----
for col, yl, fn, ref in [("coverage","Empirical coverage","coverage_by_horizon.png",NOMINAL),
                         ("mean_interval_width","Mean interval width (kWh)","interval_width_by_horizon.png",None)]:
    fig, ax = plt.subplots(figsize=(9,4.5)); ax.plot(H.horizon, H[col], marker="o")
    if ref: ax.axhline(ref, color="tab:red", ls=":", label=f"Nominal {ref:.0%}"); ax.set_ylim(0,1.02); ax.legend()
    ax.set_xlabel("Forecast horizon (hours ahead)"); ax.set_ylabel(yl); ax.set_title(yl + " by horizon (XGBoost quantile 5-95%)")
    ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(FIG, fn), dpi=150); plt.close(fig)

# time-series figure: last 7 forecast days of the test period
sub = P[P.forecast_window > len(windows)-7]
t = sub.timestamp.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
fig, ax = plt.subplots(figsize=(12,4.8))
ax.fill_between(t, sub.lower_bound, sub.upper_bound, alpha=.25, label="90% interval (5th-95th pct)")
ax.plot(t, sub.median_prediction, label="Median prediction", lw=1.4)
ax.plot(t, sub.actual_demand, label="Actual", color="k", lw=1)
out = sub[~sub.inside_interval]; ax.scatter(t[out.index], out.actual_demand, color="tab:red", s=18, zorder=3, label="Outside interval")
ax.set_ylabel("Demand (kWh)"); ax.set_title(f"XGBoost prediction intervals, last 7 test days (overall coverage {cov(P):.1%})")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(FIG, "prediction_intervals.png"), dpi=150); plt.close(fig)

pd.set_option("display.width", 200)
print(); print(S.T.to_string()); print(); print(H.round(3).to_string(index=False)); print(); print(PK.round(3).to_string(index=False))
print(f"\nNominal coverage = {NOMINAL:.0%}\nActual coverage = {cov(P):.2%}\nAverage interval width = {P.interval_width.mean():.2f} kWh")
