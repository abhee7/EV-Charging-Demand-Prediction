"""Builds the final report tables from the generated CSV files (source of truth).
Read-only on all existing outputs; writes ONLY to results/final_audit/."""
import os
import numpy as np, pandas as pd

OUT = "results/final_audit"; os.makedirs(OUT, exist_ok=True)
rd = pd.read_csv
f3 = lambda x: f"{x:.3f}"; f2 = lambda x: f"{x:.2f}"; pct = lambda x: f"{100*x:.1f}%"

def md(df):
    cols = list(df.columns); out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"]*len(cols)) + "|"]
    for _, r in df.iterrows(): out.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(out)

# ---- Table 1: point forecasting (stored, recomputation verified in audit) ----
t = rd("results/metrics/test_metrics_corrected.csv"); s = rd("results/metrics/sarimax_fourier_test_metrics.csv")
s["Model"] = "SARIMAX + Fourier"
T1 = pd.concat([t, s])[["Model","MAE","RMSE","R2","MASE"]].sort_values("RMSE").reset_index(drop=True)
T1.round(4).to_csv(f"{OUT}/table1_point_forecasting.csv", index=False)

# ---- Table 2: rolling-origin ----
ro = rd("results/rolling_origin/rolling_origin_metrics.csv")
rows = []
for c, lab in [("MAE","MAE (kWh)"),("RMSE","RMSE (kWh)"),("R2","R2 (per 24-h window)")]:
    v = ro[c]; rows.append(dict(Metric=lab, Mean=v.mean(), Std=v.std(ddof=1), Median=v.median(), Min=v.min(), Max=v.max()))
T2 = pd.DataFrame(rows); T2.round(4).to_csv(f"{OUT}/table2_rolling_origin.csv", index=False)
# exact pooled metrics (each window has 24 equally weighted hours)
d = pd.read_csv("data/processed/model_data.csv"); d["timestamp"] = pd.to_datetime(d.timestamp, utc=True)
def pooled(sub):
    idx = np.concatenate([np.arange(d.index[d.timestamp == pd.Timestamp(ts)][0], d.index[d.timestamp == pd.Timestamp(ts)][0]+24) for ts in sub.test_start])
    y = d.demand_kWh.values[idx]; sse = (24*sub.RMSE**2).sum()
    return dict(MAE=sub.MAE.mean(), RMSE=np.sqrt((sub.RMSE**2).mean()), R2=1 - sse/np.sum((y-y.mean())**2), hours=len(idx))
PO = pd.DataFrame([dict(Subset="All 91 folds", **pooled(ro)), dict(Subset="45 folds in original test period", **pooled(ro[ro.in_original_test_period]))])
PO.round(4).to_csv(f"{OUT}/table2b_rolling_origin_pooled.csv", index=False)

# ---- Table 3: interval comparison ----
q = rd("results/prediction_intervals/prediction_interval_summary.csv").iloc[0]; c = rd("results/conformal_prediction_intervals/conformal_summary.csv").iloc[0]
T3 = pd.DataFrame([
    dict(Method="Quantile XGBoost, uncalibrated (fit on train+validation)", Nominal=0.90, Empirical=q.empirical_coverage, Avg_Width_kWh=q.mean_interval_width, Fit_rows=int(q.train_rows)),
    dict(Method="Quantile XGBoost, uncalibrated (fit on train only)", Nominal=0.90, Empirical=c.uncalibrated_test_coverage_same_model, Avg_Width_kWh=c.uncalibrated_test_width_same_model, Fit_rows=int(c.train_rows)),
    dict(Method="Conformalized quantile XGBoost (fit on train only; offset from validation)", Nominal=0.90, Empirical=c.empirical_coverage, Avg_Width_kWh=c.mean_interval_width, Fit_rows=int(c.train_rows))])
T3.round(4).to_csv(f"{OUT}/table3_interval_comparison.csv", index=False)

# ---- Table 4: peak vs non-peak ----
qp = rd("results/prediction_intervals/peak_coverage.csv"); cp = rd("results/conformal_prediction_intervals/conformal_peak_coverage.csv")
rows = []
for lab, df_ in [("Quantile (uncalibrated)", qp), ("Conformalized", cp)]:
    for _, r in df_.iterrows(): rows.append(dict(Method=lab, Period=r.period, Hours=int(r.n), Coverage=r.coverage, Avg_Width_kWh=r.mean_interval_width, Below_lower=r.below_lower, Above_upper=r.above_upper))
T4 = pd.DataFrame(rows); T4.round(4).to_csv(f"{OUT}/table4_peak_vs_nonpeak.csv", index=False)

# ---- Table 5: horizon coverage ----
qh = rd("results/prediction_intervals/horizon_coverage.csv"); ch = rd("results/conformal_prediction_intervals/conformal_horizon_coverage.csv")
T5 = pd.DataFrame(dict(Horizon=qh.horizon, Quantile_coverage=qh.coverage, Conformal_coverage=ch.coverage, Quantile_width=qh.mean_interval_width, Conformal_width=ch.mean_interval_width))
T5.round(4).to_csv(f"{OUT}/table5_horizon_coverage.csv", index=False)

# ---- Training-data comparison (Part 7) ----
d_rows = pd.DataFrame([
    dict(Experiment="Baseline XGBoost (squared error)", Objective="reg:squarederror", Fit_data="train+validation", Fit_rows=5858, Calibration="none", Test="45 windows / 1,080 h"),
    dict(Experiment="Quantile XGBoost", Objective="reg:quantileerror [0.05,0.5,0.95]", Fit_data="train+validation", Fit_rows=int(q.train_rows), Calibration="none", Test="same 45 windows / 1,080 h"),
    dict(Experiment="Conformalized quantile XGBoost", Objective="reg:quantileerror [0.05,0.5,0.95]", Fit_data="train only", Fit_rows=int(c.train_rows), Calibration="validation 45 windows / 1,080 scores", Test="same 45 windows / 1,080 h"),
    dict(Experiment="Rolling-origin XGBoost", Objective="reg:squarederror", Fit_data="all rows before each window (expanding, refit per day)", Fit_rows="4,765 to 6,925", Calibration="none", Test="91 daily windows (Nov 24 - Feb 22)")])
d_rows.to_csv(f"{OUT}/table6_training_setups.csv", index=False)

with open(f"{OUT}/final_tables.md", "w", encoding="utf-8") as fh:
    fh.write("## Table 1. Point-forecast comparison (45 test windows, 1,080 hours)\n\n" + md(T1.assign(MAE=T1.MAE.map(f3), RMSE=T1.RMSE.map(f3), R2=T1.R2.map(f3), MASE=T1.MASE.map(f3)).rename(columns={"R2":"R²"})) + "\n\n")
    fh.write("## Table 2. Rolling-origin robustness (91 daily 24-hour windows; per-window statistics)\n\n" + md(T2.assign(**{k: T2[k].map(f2) for k in ["Mean","Std","Median","Min","Max"]})) + "\n\n")
    fh.write("Pooled over all hours in the folds (each window has 24 equally weighted hours, so these are exact):\n\n" + md(PO.assign(MAE=PO.MAE.map(f2), RMSE=PO.RMSE.map(f2), R2=PO.R2.map(f3)).rename(columns={"R2":"Pooled R²"})) + "\n\n")
    fh.write("## Table 3. Prediction-interval comparison (1,080 test hours)\n\n" + md(T3.assign(Nominal="90%", Empirical=T3.Empirical.map(pct), Avg_Width_kWh=T3.Avg_Width_kWh.map(f2)).rename(columns={"Empirical":"Empirical coverage","Avg_Width_kWh":"Avg width (kWh)","Fit_rows":"Rows used to fit"})) + "\n\n")
    fh.write("## Table 4. Peak vs non-peak (peak = actual >= test-period P90 = 37.46 kWh)\n\n" + md(T4.assign(Coverage=T4.Coverage.map(pct), Avg_Width_kWh=T4.Avg_Width_kWh.map(f2), Below_lower=T4.Below_lower.map(pct), Above_upper=T4.Above_upper.map(pct))) + "\n\n")
    fh.write("## Table 5. Coverage by forecast horizon (45 observations per horizon)\n\n" + md(T5.assign(Quantile_coverage=T5.Quantile_coverage.map(pct), Conformal_coverage=T5.Conformal_coverage.map(pct), Quantile_width=T5.Quantile_width.map(f2), Conformal_width=T5.Conformal_width.map(f2))) + "\n\n")
    fh.write("## Table 6. How each experiment was trained / calibrated\n\n" + md(d_rows) + "\n")
print(open(f"{OUT}/final_tables.md", encoding="utf-8").read())
