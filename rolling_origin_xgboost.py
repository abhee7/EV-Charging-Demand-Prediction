"""Rolling-origin (expanding window) evaluation of the existing XGBoost config.
Standalone: reuses the logic of train_models.py (copied, since that file runs on import).
Writes ONLY to results/rolling_origin/."""
import os, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
warnings.filterwarnings("ignore")

INPUT_FILE = "data/processed/model_data.csv"
OUT = "results/rolling_origin"; FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)
LOCAL_TZ = "America/Los_Angeles"; TARGET = "demand_kWh"
FEATURES = ["lag_1","lag_2","lag_24","lag_48","lag_168","lag_336","rolling_mean_24",
            "rolling_std_24","rolling_mean_168","rolling_std_168","hour","day_of_week",
            "day_of_month","month","week_of_year","is_weekend","is_business_hour"]
XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8,
                  colsample_bytree=0.8, objective="reg:squarederror", random_state=42, n_jobs=-1)

df = pd.read_csv(INPUT_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
df = df.sort_values("timestamp").reset_index(drop=True)
n = len(df)
FIRST_TEST_START = int(n * 0.70)   # first fold begins where the existing validation period begins
ORIG_TEST_START = int(n * 0.85)    # start of the existing single test period

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

def recursive_forecast(model, history_values, start_timestamp):   # identical to train_models.py
    history = list(np.asarray(history_values, dtype=float)); preds = []
    ts = pd.Timestamp(start_timestamp)
    for _ in range(24):
        p = max(0.0, float(model.predict(make_features(history, ts))[0]))
        preds.append(p); history.append(p); ts += pd.Timedelta(hours=1)
    return np.array(preds)

def mae(y,p): return float(np.mean(np.abs(y-p)))
def rmse(y,p): return float(np.sqrt(np.mean((y-p)**2)))
def r2(y,p):
    t = np.sum((y-np.mean(y))**2)
    return float("nan") if t == 0 else float(1-np.sum((y-p)**2)/t)

# ---------------- leakage verification ----------------
print("LEAKAGE CHECKS")
chk = {}
rng = np.random.RandomState(0)
idx = rng.choice(np.arange(336, n), 300, replace=False)
maxdiff = 0.0
for i in idx:
    fr = make_features(df[TARGET].values[:i], df.timestamp[i]).iloc[0]
    maxdiff = max(maxdiff, float(np.nanmax(np.abs(fr.values.astype(float) - df.loc[i, FEATURES].values.astype(float)))))
chk["features rebuilt from history[:i] only match stored features, 300 random rows (max abs diff)"] = maxdiff
i = 6000; y2 = df[TARGET].values.copy(); y2[i:] += 1000
a_ = make_features(df[TARGET].values[:i], df.timestamp[i]); b_ = make_features(y2[:i], df.timestamp[i])
chk["features of row t unchanged when target at t and later is altered by +1000"] = bool(a_.equals(b_))
chk["stored rolling_mean_24 at t equals mean of targets t-24..t-1 (excludes t)"] = bool(np.isclose(df.rolling_mean_24[i], df[TARGET][i-24:i].mean()))
chk["stored rolling_mean_168 at t equals mean of targets t-168..t-1 (excludes t)"] = bool(np.isclose(df.rolling_mean_168[i], df[TARGET][i-168:i].mean()))
chk["stored lag_1 at t equals target at t-1"] = bool(np.isclose(df.lag_1[i], df[TARGET][i-1]))
for k_, v_ in chk.items(): print(" ", k_, "->", v_)

# ---------------- rolling-origin folds ----------------
starts = list(range(FIRST_TEST_START, n - 24 + 1, 24))
rows, preds_all = [], {}
for k, s in enumerate(starts, 1):
    e = s + 24
    train = df.iloc[:s].dropna(subset=FEATURES)      # rows strictly before the test window
    assert train.index.max() < s and (train.timestamp < df.timestamp[s]).all()
    model = XGBRegressor(**XGB_PARAMS).fit(train[FEATURES], train[TARGET])
    hist = df[TARGET].values[:s]
    fc = recursive_forecast(model, hist, df.timestamp[s])
    y = df[TARGET].values[s:e]
    preds_all[k] = (df.timestamp[s:e].values, y, fc)
    rows.append(dict(fold=k, train_start=df.timestamp[0], train_end=df.timestamp[s-1],
        test_start=df.timestamp[s], test_end=df.timestamp[e-1], n_train_rows=len(train),
        in_original_test_period=s >= ORIG_TEST_START, MAE=mae(y,fc), RMSE=rmse(y,fc), R2=r2(y,fc),
        actual_mean_kWh=float(y.mean())))
    print(f"fold {k}/{len(starts)} {df.timestamp[s]} MAE={rows[-1]['MAE']:.3f} RMSE={rows[-1]['RMSE']:.3f} R2={rows[-1]['R2']:.3f}")
chk["every fold: all training rows strictly earlier than test_start (asserted)"] = True
m = pd.DataFrame(rows); m.to_csv(os.path.join(OUT, "rolling_origin_metrics.csv"), index=False)

# ---------------- summary ----------------
def stats(col, d):
    v = d[col].dropna(); return dict(mean=v.mean(), std=v.std(ddof=1), min=v.min(), max=v.max(), median=v.median(), n_valid=len(v))
srows = []
for label, d in [("all_folds", m), ("folds_in_original_test_period", m[m.in_original_test_period])]:
    for c in ["MAE","RMSE","R2"]:
        srows.append(dict(subset=label, metric=c, **stats(c, d)))
S = pd.DataFrame(srows); S.to_csv(os.path.join(OUT, "rolling_origin_summary.csv"), index=False)
tbl = pd.DataFrame({"Metric":["MAE","RMSE","R2"],
    "Mean":[m[c].mean() for c in ["MAE","RMSE","R2"]], "Std":[m[c].std(ddof=1) for c in ["MAE","RMSE","R2"]],
    "Min":[m[c].min() for c in ["MAE","RMSE","R2"]], "Max":[m[c].max() for c in ["MAE","RMSE","R2"]],
    "Single_45day_test":[6.49,9.06,0.68]}).round(4)
tbl.to_csv(os.path.join(OUT, "rolling_origin_summary_table.csv"), index=False)

# ---------------- figures ----------------
x = m.test_start.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
orig_x = df.timestamp[ORIG_TEST_START].tz_convert(LOCAL_TZ).tz_localize(None)
for col, ref in [("MAE",6.49),("RMSE",9.06),("R2",0.68)]:
    fig, ax = plt.subplots(figsize=(10,4.5))
    ax.plot(x, m[col], marker="o", ms=4, lw=1.2, label=f"Per-window {col}")
    ax.axhline(m[col].mean(), color="gray", ls="--", label=f"Mean = {m[col].mean():.2f}")
    ax.axhline(ref, color="tab:red", ls=":", label=f"Single 45-day test = {ref}")
    ax.axvline(orig_x, color="k", alpha=.3, lw=1)
    ax.set_xlabel("Test window start (local time; vertical line = start of original test period)")
    ax.set_ylabel(col + (" (kWh)" if col != "R2" else "")); ax.set_title(f"Rolling-origin XGBoost: 24-hour window {col}")
    ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(FIG, f"rolling_origin_{col.lower()}.png"), dpi=150); plt.close(fig)
sel = sorted(set([m.RMSE.idxmin(), m.RMSE.idxmax(), (m.RMSE-m.RMSE.median()).abs().idxmin(), 0, len(m)//2, len(m)-1]))
for j in sel:
    k = int(m.fold[j]); ts, y, p = preds_all[k]
    t = pd.DatetimeIndex(ts).tz_localize("UTC").tz_convert(LOCAL_TZ).tz_localize(None) if pd.DatetimeIndex(ts).tz is None else pd.DatetimeIndex(ts).tz_convert(LOCAL_TZ).tz_localize(None)
    fig, ax = plt.subplots(figsize=(9,4)); ax.plot(t,y,label="Actual",marker="o",ms=3); ax.plot(t,p,label="XGBoost (recursive 24h)",marker="s",ms=3)
    ax.set_title(f"Window {k}: {t[0]:%Y-%m-%d} | MAE={m.MAE[j]:.2f} RMSE={m.RMSE[j]:.2f} R2={m.R2[j]:.2f}")
    ax.set_ylabel("kWh"); ax.legend(); ax.grid(alpha=.3); fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(os.path.join(FIG, f"actual_vs_predicted_window_{k:02d}.png"), dpi=150); plt.close(fig)

# ---------------- interpretation ----------------
o = m[m.in_original_test_period]
def line(c, d): return f"mean {d[c].mean():.2f}, std {d[c].std(ddof=1):.2f}, min {d[c].min():.2f}, max {d[c].max():.2f}"
nan_r2 = int(m.R2.isna().sum())
fa = float((m.MAE > 6.49).mean()); fr_ = float((m.RMSE > 9.06).mean())
cv = m.RMSE.std(ddof=1)/m.RMSE.mean()
nval = int((~m.in_original_test_period).sum())
md = f"""# Rolling-origin evaluation of the existing XGBoost model

Setup: expanding window, {len(m)} folds, each forecasting the next 24 hours recursively (existing `recursive_forecast` logic).
The model is refit each fold on all rows before the test window only. First test window starts {m.test_start.iloc[0]} (UTC);
last ends {m.test_end.iloc[-1]}. Configuration unchanged: {XGB_PARAMS}. Real data, existing features, no tuning.
Folds 1-{nval} fall in the existing validation period; folds {nval+1}-{len(m)} ({len(o)} folds) fall in the existing 45-day test period.

## Distribution across 24-hour windows
| Metric | all {len(m)} folds | original-test-period folds | Single 45-day test |
|---|---|---|---|
| MAE | {line('MAE',m)} | {line('MAE',o)} | 6.49 |
| RMSE | {line('RMSE',m)} | {line('RMSE',o)} | 9.06 |
| R2 | {line('R2',m)} | {line('R2',o)} | 0.68 |

R2 is undefined (zero-variance actuals) in {nan_r2} fold(s); those are excluded from R2 statistics.

## Comparison
- {fa:.0%} of windows have MAE above 6.49 and {fr_:.0%} have RMSE above 9.06; median window MAE is {m.MAE.median():.2f}, median RMSE {m.RMSE.median():.2f}.
- RMSE coefficient of variation across windows is {cv:.2f}; RMSE ranges from {m.RMSE.min():.2f} to {m.RMSE.max():.2f}.
- Per-window R2 ranges from {m.R2.min():.2f} to {m.R2.max():.2f}. A single day has 24 points and its own variance, so per-window R2 is not on the same scale as the pooled 0.68.
- The single-test figures pool 1,080 hours before computing RMSE/R2, while each fold uses 24 hours. The mean of per-window RMSE and a pooled RMSE are different quantities.

## Leakage checks (performed in `rolling_origin_xgboost.py`)
""" + "\n".join(f"- {k}: {v}" for k, v in chk.items()) + """
- Recursive forecast: within a window only the model's own previous predictions are appended to history (as in the existing logic); no actual test-window values enter features.

## Caveats
Consecutive folds share most training data and test days are adjacent, so folds are not independent. The data covers one site over about 10 months.
"""
open(os.path.join(OUT, "rolling_origin_interpretation.md"), "w", encoding="utf-8").write(md)
print(); print(tbl.to_string(index=False)); print(); print(S.to_string(index=False))
