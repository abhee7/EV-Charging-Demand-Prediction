# Final Audit — EV Charging Demand Prediction Using Machine Learning and Time-Series Analysis

All numbers below were read from, or recomputed from, the generated CSV files in `results/`. Nothing in `results/` (other than the new `results/final_audit/` folder) was modified. Scripts added for this audit: `final_audit_tables.py` (builds the tables from the CSVs). Verification scratch scripts live outside the project.

---

## 1. Audit summary

### 1.1 Verified facts (source: `data/processed/model_data.csv` and result CSVs)

| Item | Verified value |
|---|---|
| Hourly observations | 7,288 (2018-04-25 → 2019-02-22), sorted, 0 time gaps, 0 missing targets, 486 zero-demand hours |
| Train / validation / test rows | 5,101 / 1,093 / 1,094 (chronological 70/15/15 by row index) |
| Train period (UTC) | 2018-04-25 11:00 → 2018-11-23 23:00 |
| Validation period (UTC) | 2018-11-24 00:00 → 2019-01-08 12:00 |
| Test period (UTC) | 2019-01-08 13:00 → 2019-02-23 02:00 |
| Forecast windows | 45 validation + 45 test, each 24 h non-overlapping. 1,080 hours evaluated in each; 14 test hours (and 13 validation hours) are left out because they do not fill a whole window |
| Rows with incomplete features | first 336 rows (lag_336 needs 14 days) — all inside the training set |
| Point-metric files | Re-computing MAE/RMSE/R² from the raw prediction CSVs reproduces `test_metrics_corrected.csv` and `sarimax_fourier_test_metrics.csv` to machine precision for all 5 models (max diff 0.0); horizon metrics also match |
| Rolling-origin | 91 folds, expanding window, 24 h each, train rows 4,765 → 6,925 (+24 per fold), first test 2018-11-24 00:00 UTC, last test ends 2019-02-22 23:00 UTC; 46 folds fall in the old validation period, 45 in the old test period |
| Quantile intervals | 1,080 rows; coverage, width, MAE/RMSE, horizon and peak files all recompute exactly from `prediction_intervals.csv` |
| Conformal intervals | 1,080 rows; calibration offset q̂ = 2.634 kWh from 1,080 validation scores (45 windows); upper = raw upper + q̂ and lower = max(0, raw lower − q̂) verified row by row (max error 7e-15); coverage, width, MAE/RMSE recompute exactly |

### 1.2 Discrepancies and issues found (reported, not silently fixed)

| # | Finding | Severity | Detail / recommendation |
|---|---|---|---|
| D1 | **Stale legacy result files contradict the corrected results** | High (if cited by mistake) | `results/metrics/model_metrics.csv` and `results/predictions/test_predictions.csv` hold an earlier pipeline's output: XGBoost MAE 15.04 / RMSE 18.53 / R² −0.33, Random Forest 9.85 / 13.30 / 0.32, Linear Regression 8.12 / 10.27 / 0.59 (Seasonal Naive is identical in both versions). The dashboard API, `generate_figures.py` and `final_results_audit.py` read only the `*_corrected` files, so no figure or dashboard page uses the stale values. Recommend renaming the two stale files with a `legacy_` prefix so they cannot be quoted by accident. Not done, because you asked me not to touch existing outputs. |
| D2 | **Baseline cannot be reproduced bit-for-bit on this machine** | Medium (numeric only) | An independent re-run (same config, train+validation fit, same recursive logic) gave MAE 6.459 / RMSE 9.028 / R² 0.684 versus stored 6.493 / 9.055 / 0.682 (differences of 0.5% / 0.3% / 0.002). The re-run is deterministic here (two identical runs). The difference appears already at horizon 1 (mean 0.11 kWh), so it is a model-fit difference, not a logic difference. The most likely cause is a different XGBoost/pandas/numpy version from the one that produced the stored files: no Python on this machine had xgboost installed, so I used a scratch venv (xgboost 3.4.1, pandas 3.0.6, numpy 2.5.3). I could not confirm the original versions. Consequence: the rolling-origin, quantile and conformal experiments were run with xgboost 3.4.1, so they are not bit-identical to the stored baseline. Conclusions are unaffected, but record your versions with `pip freeze` and cite the stored baseline (6.49 / 9.06 / 0.68). |
| D3 | **Calibration windows and test windows start at different times of day** | Medium (methodological caveat, not leakage) | Validation windows start at 00:00 UTC (16:00 local) but test windows start at 13:00 UTC (05:00 local), because 1,093 is not a multiple of 24. So horizon h means a different clock hour in calibration and in test. The conformal offset is a single pooled number (all 24 hours of the day appear in both sets), so it still works on average, but per-horizon calibration is not like-for-like. This helps explain the uneven conformal horizon coverage (see 6.4). Likewise, per-horizon curves from the test set and from the rolling-origin windows (which start at 16:00 local) are not comparable horizon-by-horizon. |
| D4 | **Two different "P90" peak thresholds exist** | Low | `high_demand_thresholds.csv` uses the whole dataset: P90 = 51.29 kWh. The peak detection and both interval experiments use the 1,080 test hours: P90 = 37.46 kWh. Both are valid; always state which one is used. |
| D5 | **Peak coverage is conditional on the outcome** | Low (interpretation) | "Peak" is defined by the actual demand being high, so peak coverage measures how often the interval contains an unusually large actual value. It is expected to be lower than overall coverage for any method. It is not the same as coverage when the model predicts a peak. |
| D6 | **SHAP uses one-step features built from actual lags** | Low (interpretation) | `run_shap_analysis.py` refits XGBoost (same 200/4/0.05/0.8/0.8 setup) on train+validation and explains it on the 1,094 test rows of `model_data.csv`, whose lag features are real past demand. The forecasts themselves use recursive predicted lags. SHAP therefore describes how the model uses features in the one-step setting, not the exact 24-hour recursive pipeline. |
| D7 | **Hyper-parameter choice used validation windows that rolling-origin also covers** | Low | XGBoost candidate 1 was selected on the 45 validation windows. Rolling-origin folds 1–46 lie in that period, so they are slightly optimistic. Folds 47–91 (the old test period) are unaffected. |
| D8 | **Small number of independent evaluation days** | Interpretation | 45 test days, one site, ~10 months. Per-horizon coverage rests on 45 observations each (about ±9 percentage points of sampling noise at 90%). |
| D9 | **Not audited** | Scope | The arrival-hour variant (`results/arrival_hour/`, `train_models_arrival_hour.py`), the Streamlit/React dashboards, and the older `final_results_audit.py` were not re-run or re-validated. README/architecture documents contain no result numbers to contradict, and the README states that no model is called best. |
| D10 | **SARIMAX configuration is modest** | Interpretation | The "SARIMAX + Fourier" model is ARMA(1,0,1) errors with a constant, daily and weekly Fourier terms (K=3 each) and no seasonal differencing, refit for every window. Its poor result applies to this configuration only. |

No discrepancy was found between the scripts, the CSV files and the earlier experiment summaries for rolling-origin, quantile and conformal results.

---

## 2. Data-leakage audit

| Check | Result | Evidence |
|---|---|---|
| 1. Chronological split | Pass | Timestamps strictly increasing, no gaps; split by row index (70%/85%); periods do not overlap (table in 1.1) |
| 2. No future target in features | Pass | Features rebuilt from only `history[:i]` equal the stored feature columns for 300 random rows (max abs diff 3e-13). Adding +1000 to the target at time t and later leaves the features of row t unchanged |
| 3. Lags use only the past | Pass | `lag_k = target.shift(k)`; stored `lag_1` at t equals the target at t−1 |
| 4. Rolling statistics exclude the current target | Pass | Built from `target.shift(1).rolling(...)`; stored rolling mean at t equals the mean of targets t−24…t−1 (and t−168…t−1) |
| 5. Rolling-origin folds only use past data | Pass | In all 91 folds the training rows are strictly earlier than the test window (asserted in code; `train_end < test_start` in every CSV row); training size grows by exactly 24 rows per fold |
| 6. Interval calibration uses validation only | Pass | Conformal model fit on rows before the 70% split; scores computed from the 45 validation windows; q̂ computed before any test window is forecast |
| 7. Test targets never used for fitting or calibration | Pass | Baseline, SHAP and quantile models are fit on rows before the 85% split; SARIMAX is fit per window on history only; the test P90 peak threshold is used only for reporting, not for fitting or calibration |
| 8. Recursive forecasting | Pass | Within a 24-hour window only the model's own predictions are appended to the history; real actuals enter only as history before the window start |
| 9. Preprocessing | Pass | No scaling/normalisation (tree models); no missing hours needed filling (0 gaps); the whole-dataset P90 in `high_demand_thresholds.csv` is descriptive only and feeds no model |

**Leakage audit passed.**

Caveats that are *not* leakage but should be stated: D3 (window phase mismatch between calibration and test), D5, D7. In addition, hourly demand is a reconstructed quantity (session energy spread evenly between connection and "done charging" time, sessions without a done-charging time or with non-positive energy removed), not a metered one.

---

## 3. Baseline verification (Part 3)

The stored test metrics were re-derived from the raw predictions (see 1.1) and agree exactly. XGBoost reproduces the 6.49 / 9.06 / 0.68 reference. An independent re-run on this machine gives 6.46 / 9.03 / 0.68 (D2).

Facts to report without ranking claims: Random Forest has the lowest MAE (6.38) while XGBoost has the lowest RMSE (9.06) and highest R² (0.682); their RMSE differs by 0.04 kWh. The Diebold–Mariano test (squared-error loss, HAC lag 23, 1,080 hours) finds **no significant difference between XGBoost and Random Forest** (p = 0.81). XGBoost differs significantly from Linear Regression (p = 3.4e-5), Seasonal Naive (p = 0.0018) and SARIMAX + Fourier (p ≈ 0). Linear Regression vs Seasonal Naive is not significant (p = 0.27). So the data support "XGBoost and Random Forest perform similarly and are more accurate than the other three configurations on this test period", not "XGBoost is best".

---

## 4. Rolling-origin verification (Part 4)

Per-window statistics (91 windows): MAE mean 6.22, std 2.54, median 5.70, min 2.66, max 18.48. RMSE mean 8.30, std 3.96, median 7.42, min 3.52, max 28.87. R² median 0.65, range −134.34 to 0.95; 20 of 91 windows have R² < 0 and 51 have R² ≥ 0.5.

**Do not read the mean per-window R² (−1.87) as comparable to the pooled test R² (0.68).** R² compares the squared error to the variance of the actuals *within that one window*. When a day has very low or very flat demand (holidays, weekends), the window variance is tiny, so a modest absolute error produces a huge negative R². Example: fold 33 (2018-12-26) has mean demand 1.62 kWh and MAE 9.2 kWh, giving R² = −134. Pooled R² divides the total error by the total variance across many days, which is much larger. The exact pooled values from the fold errors are: all 91 folds MAE 6.22, RMSE 9.19, R² 0.672; the 45 folds in the old test period MAE 6.01, RMSE 8.45, R² 0.728. These use models refit every day on expanding data, so they are not the same experiment as the single 45-day test; they indicate the pooled level is similar, not identical.

Hardest windows (RMSE): fold 45 (28.87; window starting 2019-01-06 16:00 local, mean demand 24.3 kWh), fold 59 (19.53; 2019-01-20 16:00 local; coincides with the Martin Luther King Jr. Day holiday, mean demand 5.97), fold 40 (19.26; 2019-01-01 16:00 local), fold 31 (18.11; 2018-12-23 16:00 local) and fold 33 (15.55). Several coincide with the Christmas/New Year period. Easiest: fold 72 (RMSE 3.52), 88 (3.94), 37 (4.01), 84 (4.25), 16 (4.44). Absolute errors are moderately variable: the interquartile range of MAE is 4.43–7.03 kWh, but a few days are several times worse (max 18.48), and window mean demand is almost uncorrelated with MAE (r = 0.09), so difficulty is not simply "busy days".

---

## 5. Prediction-interval audit (Part 5)

Quantiles 0.05 / 0.50 / 0.95 (`reg:quantileerror`, one model, XGBoost 3.4.1), nominal coverage 90%, trained on train+validation. Result: **empirical coverage 71.2% (769 of 1,080 hours), average width 29.46 kWh**. This is **under-coverage of 18.8 percentage points**, not a successful 90% interval. 23.4% of actuals fell below the lower bound and 5.4% above the upper bound. Peak hours: 49.1% coverage (108 hours, all misses above the upper bound); non-peak: 73.7%. Horizon coverage ranges from 24.4% (h=24) to 97.8% (h=1).

Plain-language explanation: the model predicted a range that should contain 90% of outcomes but contained only 71%. Much of the failure occurs at night hours where actual demand is exactly 0 kWh (201 of 1,080 hours, only 21% of them inside the interval), because the 5th-percentile bound sat slightly above zero (average 1.24 kWh on those hours). The intervals are also too narrow in peaks and are built around one recursive path, so they do not reflect error accumulating over 24 steps. The second reason is a plausible reading, not something that was separately tested.

---

## 6. Conformal calibration audit (Part 6)

### 6.1 Verified protocol
1. Quantile model fit on **train rows only** (4,765 rows).
2. Recursive 24-hour forecasts over the 45 **validation** windows give 1,080 conformity scores `s = max(lower − y, y − upper)`.
3. q̂ = the ⌈(n+1)(1−0.10)⌉/n empirical quantile of the scores = **2.634 kWh**.
4. The same train-only model is applied to the test period; bounds are lower − q̂ (floored at 0) and upper + q̂. Test targets are used only to score the result.

Validation coverage rose from 68.8% to 90.2% (this is expected by construction, since the offset was fitted on those scores).

### 6.2 Verified results (test, 1,080 hours)
**Empirical coverage 90.9%** (nominal 90%), **average width 34.45 kWh**. For the same train-only model without calibration: coverage 66.9%, width 29.63 kWh. So calibration raised coverage by 24.0 points (from 66.9%) at a cost of 4.82 kWh of width (+16.3%); against the baseline quantile run (71.2%, 29.46 kWh) the change is +19.7 points and +4.98 kWh (+16.9%).
Peak hours 72.2% (width 41.67), non-peak 93.0% (width 33.65). A bootstrap over the 45 test days (resampling whole days) gives an approximate 95% interval of 88.5%–93.1% for the overall coverage; for the baseline (uncalibrated) quantile run it is 66.9%–75.6%. These are rough, because neighbouring days are not independent.

### 6.3 Wording rules
Report this as **empirical coverage on this test period**. Do not call it guaranteed coverage: conformal guarantees assume exchangeable data, which hourly time series with trend, daily patterns and holidays do not strictly satisfy, and D3 shows that calibration and test windows are not phase-aligned.

### 6.4 Where it still falls short
Horizon coverage: 100% at h=1–3 and h=22–24 (wider than needed), but only 71.1% and 73.3% at h=5 and h=6 and 82–84% around h=17–19. By local clock hour, conformal coverage is 100% between 02:00 and 07:00 (no-demand hours) and 71–73% at 09:00–10:00 (the morning ramp-up). A single global offset cannot fix horizon- or time-of-day-specific error.

---

## 7. Fair-comparison warning (Part 7)

The three XGBoost experiments are **not three competing point-forecast models**:

| Experiment | Objective | Fitted on | Calibrated on | Median MAE / RMSE |
|---|---|---|---|---|
| Baseline | squared error | train+validation (5,858 rows) | – | 6.49 / 9.06 |
| Quantile | quantile (median head) | train+validation (5,858 rows) | – | 7.20 / 10.33 |
| Conformal | quantile (median head) | **train only (4,765 rows)** | validation scores | 7.05 / 9.61 |

They differ in the loss function (mean vs. median), the training rows (conformal had to stay train-only so the calibration is valid), and whether intervals exist. The conformal median is not "an improved model"; it simply comes from a different fit. Use the **baseline XGBoost for point-forecast performance** and the quantile/conformal experiments **only for uncertainty, coverage, calibration and width**. The like-for-like comparison for the effect of calibration is the *same train-only model with and without the offset* (66.9% → 90.9%, 29.63 → 34.45 kWh). Table 6 below lists each setup.

---

## 8. Final tables (Part 8)

Generated by `final_audit_tables.py` from the CSV files; CSV copies are in `results/final_audit/`.

## Table 1. Point-forecast comparison (45 test windows, 1,080 hours)

| Model | MAE | RMSE | R² | MASE |
|---|---|---|---|---|
| XGBoost | 6.493 | 9.055 | 0.682 | 0.731 |
| Random Forest | 6.383 | 9.098 | 0.679 | 0.718 |
| Linear Regression | 7.521 | 9.942 | 0.617 | 0.847 |
| Seasonal Naive | 7.141 | 10.517 | 0.572 | 0.804 |
| SARIMAX + Fourier | 11.057 | 13.726 | 0.270 | 1.258 |

## Table 2. Rolling-origin robustness (91 daily 24-hour windows; per-window statistics)

| Metric | Mean | Std | Median | Min | Max |
|---|---|---|---|---|---|
| MAE (kWh) | 6.22 | 2.54 | 5.70 | 2.66 | 18.48 |
| RMSE (kWh) | 8.30 | 3.96 | 7.42 | 3.52 | 28.87 |
| R2 (per 24-h window) | -1.87 | 14.43 | 0.65 | -134.34 | 0.95 |

Pooled over all hours in the folds (each window has 24 equally weighted hours, so these are exact):

| Subset | MAE | RMSE | Pooled R² | hours |
|---|---|---|---|---|
| All 91 folds | 6.22 | 9.19 | 0.672 | 2184 |
| 45 folds in original test period | 6.01 | 8.45 | 0.728 | 1080 |

## Table 3. Prediction-interval comparison (1,080 test hours)

| Method | Nominal | Empirical coverage | Avg width (kWh) | Rows used to fit |
|---|---|---|---|---|
| Quantile XGBoost, uncalibrated (fit on train+validation) | 90% | 71.2% | 29.46 | 5858 |
| Quantile XGBoost, uncalibrated (fit on train only) | 90% | 66.9% | 29.63 | 4765 |
| Conformalized quantile XGBoost (fit on train only; offset from validation) | 90% | 90.9% | 34.45 | 4765 |

## Table 4. Peak vs non-peak (peak = actual >= test-period P90 = 37.46 kWh)

| Method | Period | Hours | Coverage | Avg_Width_kWh | Below_lower | Above_upper |
|---|---|---|---|---|---|---|
| Quantile (uncalibrated) | Non-peak | 972 | 73.7% | 28.81 | 26.0% | 0.3% |
| Quantile (uncalibrated) | Peak (actual >= test-period P90) | 108 | 49.1% | 35.35 | 0.0% | 50.9% |
| Conformalized | Non-peak | 972 | 93.0% | 33.65 | 6.9% | 0.1% |
| Conformalized | Peak (actual >= test-period P90) | 108 | 72.2% | 41.67 | 0.0% | 27.8% |

## Table 5. Coverage by forecast horizon (45 observations per horizon)

| Horizon | Quantile_coverage | Conformal_coverage | Quantile_width | Conformal_width |
|---|---|---|---|---|
| 1 | 97.8% | 100.0% | 25.44 | 29.09 |
| 2 | 95.6% | 100.0% | 25.52 | 29.32 |
| 3 | 91.1% | 100.0% | 26.55 | 31.63 |
| 4 | 93.3% | 97.8% | 30.35 | 35.53 |
| 5 | 46.7% | 71.1% | 33.53 | 40.23 |
| 6 | 62.2% | 73.3% | 35.37 | 42.59 |
| 7 | 77.8% | 88.9% | 34.67 | 38.92 |
| 8 | 73.3% | 86.7% | 31.74 | 36.64 |
| 9 | 86.7% | 95.6% | 31.58 | 36.92 |
| 10 | 86.7% | 88.9% | 31.64 | 37.74 |
| 11 | 91.1% | 93.3% | 31.42 | 37.24 |
| 12 | 82.2% | 88.9% | 30.56 | 36.24 |
| 13 | 82.2% | 86.7% | 29.86 | 35.30 |
| 14 | 91.1% | 95.6% | 29.25 | 34.93 |
| 15 | 86.7% | 91.1% | 29.10 | 34.72 |
| 16 | 86.7% | 93.3% | 29.01 | 34.68 |
| 17 | 84.4% | 84.4% | 28.61 | 34.22 |
| 18 | 73.3% | 84.4% | 28.41 | 33.83 |
| 19 | 57.8% | 82.2% | 28.16 | 33.78 |
| 20 | 44.4% | 86.7% | 27.25 | 31.86 |
| 21 | 33.3% | 93.3% | 27.27 | 31.21 |
| 22 | 33.3% | 100.0% | 27.26 | 30.54 |
| 23 | 26.7% | 100.0% | 27.29 | 30.05 |
| 24 | 24.4% | 100.0% | 27.28 | 29.52 |

## Table 6. How each experiment was trained / calibrated

| Experiment | Objective | Fit_data | Fit_rows | Calibration | Test |
|---|---|---|---|---|---|
| Baseline XGBoost (squared error) | reg:squarederror | train+validation | 5858 | none | 45 windows / 1,080 h |
| Quantile XGBoost | reg:quantileerror [0.05,0.5,0.95] | train+validation | 5858 | none | same 45 windows / 1,080 h |
| Conformalized quantile XGBoost | reg:quantileerror [0.05,0.5,0.95] | train only | 4765 | validation 45 windows / 1,080 scores | same 45 windows / 1,080 h |
| Rolling-origin XGBoost | reg:squarederror | all rows before each window (expanding, refit per day) | 4,765 to 6,925 | none | 91 daily windows (Nov 24 - Feb 22) |

---

## 9. Recommended figures for the report (Part 9)

Use these existing files; no new figures are needed.

| # | File | Use / caption note |
|---|---|---|
| 1 | `results/figures/05_actual_vs_predicted_24h.png` | Illustrates a 24-hour forecast. It shows **only test window 1**, so caption it as "one illustrative window", not as typical performance. It also shows the models under-predicting the morning peak |
| 2 | `results/figures/12_test_period_actual_vs_predicted.png` | Whole test period. Six lines make it crowded; if space is tight, redraw with Actual + XGBoost only (optional) |
| 3 | `results/figures/06_model_metric_comparison.png` | MAE/RMSE bars for the five models (reads the corrected CSVs, verified) |
| 4 | `results/figures/08_shap_feature_importance.png` | Feature importance (mention D6 in the caption: one-step features) |
| 5 | `results/rolling_origin/figures/rolling_origin_mae.png` | Stability across 91 daily windows |
| 6 | `results/rolling_origin/figures/rolling_origin_rmse.png` | Same for RMSE. Skip `rolling_origin_r2.png`, or caption it carefully because of the extreme negative values |
| 7 | `results/conformal_prediction_intervals/figures/conformal_prediction_intervals.png` | Interval plot for the last 7 test days (the baseline version is `results/prediction_intervals/figures/prediction_intervals.png`) |
| 8 | `results/conformal_prediction_intervals/figures/conformal_coverage_by_horizon.png` | Coverage by horizon, conformalized vs uncalibrated, with the 90% line |

Peak vs non-peak uncertainty has no dedicated figure; present it as **Table 4**. Optional extras: `results/figures/07_horizon_rmse.png` and `results/conformal_prediction_intervals/figures/conformal_interval_width.png`.

---

## 10. Report-ready text (Part 10)

### 10.1 Methodology

**Dataset.** The study uses the Caltech ACN-Data charging-session records (`data/raw/acndata_caltech.csv`). Sessions without a "done charging" time or with non-positive delivered energy were removed. Each session's energy was spread evenly over the time between connection and the end of charging, and summed per clock hour (America/Los_Angeles time) to give hourly charging demand in kWh. The result is 7,288 consecutive hourly observations from 25 April 2018 to 22 February 2019 (486 hours with zero demand). Because the demand is reconstructed from session records, it approximates metered load.

**Preprocessing and features.** The hourly series was placed on a regular UTC timeline (no gaps were found). Seventeen features were used: lagged demand (1, 2, 24, 48, 168 and 336 hours); the mean and standard deviation of the previous 24 and 168 hours (shifted by one hour so the current value is never included); and calendar variables from local time (hour, day of week, day of month, month, week of year, weekend flag, business-hour flag 08:00–18:00). The first 336 rows, which lack a full lag history, are not used for training.

**Train / validation / test split.** The data were split chronologically by time: 70% training (5,101 h), 15% validation (1,093 h) and 15% test (1,094 h). Random shuffling was not used because it would let the model see the future. Candidate hyper-parameters were compared on the validation period. The selected models were then refit on training plus validation data and evaluated once on the test period.

**XGBoost.** Gradient-boosted regression trees with 200 trees, depth 4, learning rate 0.05, row and column sampling of 0.8, squared-error loss and seed 42. Linear Regression, Random Forest and a Seasonal Naive forecast (repeat the same 24 hours one week earlier) are used as reference methods.

**SARIMAX.** A time-series regression with ARMA(1,0,1) errors, a constant, and daily (24 h) and weekly (168 h) Fourier seasonal terms with three harmonics each, refit on all earlier history for every forecast window.

**24-hour forecasting.** For each forecast origin, the model predicts the next hour, adds that prediction to the history, and repeats 24 times (recursive multi-step forecasting). Negative predictions are set to 0. The test period contains 45 non-overlapping 24-hour windows (1,080 hours). Accuracy is measured with MAE, RMSE and R² (also sMAPE and MASE in the CSV files), overall and by horizon. The Diebold–Mariano test with a Newey–West (HAC) variance compares models.

**Rolling-origin evaluation.** To check stability over time, XGBoost was refit for each of 91 consecutive days (24-hour test windows from 24 November 2018 to 22 February 2019), always training on all data before the window (expanding window), using the same features and recursive forecast.

**Quantile prediction intervals.** XGBoost was trained with the quantile objective for the 5th, 50th and 95th percentiles; the 5th–95th range is a nominal 90% prediction interval, and the median is the point forecast. The median is fed back in the recursive loop.

**Conformal calibration.** To correct the interval width, conformalized quantile regression was used. The quantile model was fitted on the training data only. On the validation windows, each hour's score is how far the actual value fell outside the predicted interval (zero or negative if inside). The 90% (finite-sample adjusted) quantile of these 1,080 scores, 2.63 kWh, was added to the upper bound and subtracted from the lower bound. Test data were used only to measure the final coverage. Peak hours are defined as test hours whose actual demand is at or above the test-period 90th percentile (37.46 kWh).

### 10.2 Results

**Point forecasts (45 test windows, 1,080 hours).**

| Model | MAE | RMSE | R² |
|---|--:|--:|--:|
| XGBoost | 6.49 | 9.06 | 0.682 |
| Random Forest | 6.38 | 9.10 | 0.679 |
| Linear Regression | 7.52 | 9.94 | 0.617 |
| Seasonal Naive | 7.14 | 10.52 | 0.572 |
| SARIMAX + Fourier | 11.06 | 13.73 | 0.270 |

XGBoost and Random Forest have very similar errors, and the Diebold–Mariano test finds no significant difference between them (p = 0.81). Both are significantly different from Seasonal Naive and SARIMAX + Fourier.

**Rolling-origin (91 daily windows).** Mean MAE 6.22 (std 2.54, median 5.70, range 2.66–18.48); mean RMSE 8.30 (std 3.96, median 7.42, range 3.52–28.87). Pooled over all 2,184 forecast hours the RMSE is 9.19 and R² is 0.672; for the 45 windows inside the original test period the pooled RMSE is 8.45 and R² 0.728. Individual one-day R² values range from −134 to 0.95 (median 0.65), with 20 of 91 days below zero; these negative values occur on low-demand days, where the denominator of R² is very small (for example 26 December 2018, mean demand 1.6 kWh).

**Prediction intervals (nominal 90%).**

| Method | Empirical coverage | Avg width (kWh) |
|---|--:|--:|
| Quantile XGBoost, uncalibrated | 71.2% | 29.46 |
| Same model family fit on train only, uncalibrated | 66.9% | 29.63 |
| Conformalized quantile XGBoost | 90.9% | 34.45 |

Coverage of the conformalized intervals was 93.0% for non-peak hours and 72.2% for peak hours (uncalibrated: 73.7% and 49.1%). By forecast horizon the conformalized coverage ranged from 71% (h=5) to 100%.

### 10.3 Discussion

*Why XGBoost captures demand patterns.* Charging demand at this site follows strong daily and weekly cycles and depends heavily on the immediately preceding hours. SHAP analysis shows `lag_1` carries about 59% of the mean absolute SHAP value, followed by the hour of day, the same hour one and two weeks earlier (`lag_168`, `lag_336`) and `lag_2`. Tree ensembles can combine these lag and calendar effects non-linearly, which a linear model or a seasonal-only model cannot. The measured results are consistent with this: XGBoost and Random Forest, which both use such features, had lower errors than Linear Regression, Seasonal Naive and the SARIMAX configuration used here, but XGBoost and Random Forest cannot be separated statistically.

*Variation across rolling windows.* The median daily error (MAE 5.7, RMSE 7.4) is close to the single-test figures, and the pooled error over the folds is similar, so average performance is consistent. Individual days vary a lot: the worst day had MAE 18.5 kWh, about 3 times the median. The hardest days include windows around Christmas, New Year and a public holiday, when demand patterns differ from normal weeks. Single-day R² is unstable (see above).

*Why uncalibrated quantile intervals under-covered.* A nominal 90% interval should contain 90% of actual values; here it contained 71.2%. The intervals are produced from one recursive forecast path, so they do not include the extra error that builds up as predictions are fed back over 24 steps, and the lower bound sat slightly above zero on many no-demand night hours (201 hours with exactly zero demand, only 21% of which were inside the interval).

*How conformal calibration helped.* Calibration measured how often the intervals missed on the validation period (68.8% coverage) and widened them by the amount (2.63 kWh each side) needed to reach 90% there. On the unseen test period the empirical coverage was then 90.9%, at the price of intervals about 16–17% wider (29.5 → 34.4 kWh). This is an empirical result for this test period, not a guarantee.

*Why peak coverage remains lower.* Peak hours are rare (10% of the test hours) and unusually large, and the model's peak predictions are generally lower than the actual values (all peak misses were above the upper bound). A single global widening cannot fix errors that are specific to peaks. In addition, peak is defined by the actual value being high, which makes it harder for any interval to contain it.

*Practical meaning.* A point forecast alone hides risk. The calibrated interval gives an operator a plausible range, for example planning capacity on the upper bound for a given hour. But the intervals are wide (about 34 kWh) compared with the mean hourly demand (21 kWh), and they under-cover peak hours, so peak-capacity decisions should include a safety margin and should not rely on the interval alone.

### 10.4 Limitations
- A single charging site (Caltech) and about 10 months of data, with only 45 test days and 91 rolling days. Neighbouring days are not independent, so confidence statements are approximate.
- Time-series dependence and possible distribution shifts (term time, holidays, seasons); the test period is winter only.
- Hourly demand is reconstructed from session records, not metered.
- The ML hyper-parameters were chosen from three candidates per model; no extensive tuning was done. The SARIMAX configuration is simple, so its results apply to that configuration only.
- Peak-demand uncertainty is still poorly captured (72.2% coverage after calibration).
- Conformal methods assume exchangeable data, which is not strictly true for time series; also the calibration and test windows start at different hours of the day (D3), and one global offset was used for all horizons.
- Numerical results depend on the library version (D2): re-running in a different environment gave MAE/RMSE differing by about 0.03 kWh.
- SHAP was computed with one-step features built from real lags.

### 10.5 Future work
- Add weather variables and traffic or event/calendar information (academic term, holidays).
- Use data from multiple charging stations or sites and a longer history (more than one winter/season).
- Horizon-specific (and time-of-day-specific) conformal calibration, once more calibration data are available.
- Evaluate more advanced probabilistic forecasting methods only after the data coverage above has improved.
- Document library versions and fix the evaluation windows so results are fully reproducible.

---

## 11. Executive conclusion (Part 11)

This project showed that hourly EV charging demand at one campus charging site can be forecast 24 hours ahead from its own recent history and calendar information with a typical error of about 6–7 kWh per hour (test MAE 6.49, RMSE 9.06, R² 0.68 for XGBoost, against a mean demand of about 21 kWh). Tree-based models (XGBoost and Random Forest, which are statistically indistinguishable here) outperformed the Linear Regression, Seasonal Naive and SARIMAX + Fourier configurations tested, and SHAP shows that the most recent hour dominates the prediction, with the time of day and the same hour in previous weeks next in importance.

The rolling-origin experiment shows that the average level of accuracy is repeatable across 91 different days (median MAE 5.7 kWh, pooled R² 0.67), but that single-day performance is variable and is worst on holiday-like or unusual days; a single 45-day test, and especially any single-day R², should be interpreted with that in mind. The uncertainty experiments showed that raw quantile intervals were over-confident (71.2% empirical coverage for a nominal 90%), that calibration on validation data raised empirical coverage on the test period to 90.9% at the cost of roughly 17% wider intervals, and that peak hours remained under-covered (72.2%). These intervals are empirical results from one site and one winter period, not guarantees.

Overall, the work demonstrates a leakage-controlled forecasting workflow, a measurement of how stable the model is over time, and an honest check of how reliable its uncertainty estimates are. It does not show that any one algorithm is universally best, and its conclusions are limited by the single site, the short history and the modest number of independent test days.

---

## 12. Viva preparation (Part 12)

1. **Why did you choose XGBoost?** Demand depends non-linearly on recent hours, time of day and day of week. Gradient-boosted trees handle such tabular lag features well, need no scaling and train quickly. I compared it with simpler baselines; on the test set it was similar to Random Forest and better than the other three.
2. **Why did you use SARIMAX?** It is the classical time-series benchmark. I used ARMA errors plus daily and weekly Fourier seasonality to see how a statistical model compares with ML. In my configuration it was less accurate (RMSE 13.7), but that applies to this simple setup only.
3. **What is rolling-origin evaluation?** Instead of one train/test split, I move the forecast origin forward day by day, train on everything before it, forecast the next 24 hours and score it. This tests whether performance is stable across many periods (91 days here).
4. **Why can't we randomly split time-series data?** Random splits mix future and past, so the model could learn from data that comes after the point it is predicting. The test would then look better than reality. I split chronologically.
5. **What is data leakage?** Any information from the future or the test set that the model would not have at prediction time. I checked that lags use only earlier values, rolling averages are shifted by one hour, and test data never enter training or calibration.
6. **What is recursive forecasting?** To forecast 24 hours, the model predicts hour 1, treats that prediction as if it were known data, predicts hour 2, and so on. Errors can accumulate over the 24 steps.
7. **What is a prediction interval?** A range that is supposed to contain the true future value with a stated probability, for example 90%. It shows uncertainty, unlike a single-number forecast.
8. **Why did the 90% quantile interval only achieve 71.2% coverage?** The intervals were too narrow: they come from one recursive forecast path (so accumulated error is ignored), the 5th-percentile bound sat just above zero on no-demand night hours where the actual value was exactly 0, and peaks were under-predicted. I report this as under-coverage, not a success.
9. **What is conformal prediction?** A method that uses past forecast errors on held-out data (here the validation period) to adjust an interval so that it reaches the desired coverage. I added the 90th-percentile "miss distance" of 2.63 kWh to each side.
10. **Why did coverage improve to about 90.9%?** The validation data showed the intervals missed too often, so the correction widened them by just enough to reach 90% there; on the test set the empirical coverage came out at 90.9%.
11. **What is empirical coverage?** The measured fraction of real observations that fall inside the interval (here 982 of 1,080 hours). It is measured, not guaranteed.
12. **Why is peak coverage lower?** Peaks are rare and large, the model tends to under-predict them, and a single global adjustment cannot fix a peak-specific error. Also, peak is defined by the real value being high, which makes it harder to contain.
13. **Why can R² become negative for individual daily windows?** R² compares the error with the variance of that day's demand. On a quiet day (for example 1.6 kWh mean) the variance is tiny, so even a moderate error gives a hugely negative R². The pooled R² over many days is more meaningful.
14. **What does `lag_1` represent?** The demand in the previous hour. It is the strongest feature (about 59% of the SHAP importance) because demand changes smoothly from one hour to the next.
15. **Why are lag features useful?** They give the model the recent state of the system and repeating patterns: lag_24 is the same hour yesterday, lag_168 is the same hour last week, lag_336 two weeks ago.
16. **What does SHAP tell us?** How much each feature moved the model's predictions on average. For XGBoost, `lag_1` dominates, then hour of day, `lag_336`, `lag_168` and `lag_2`. It shows what the model relies on, not cause and effect.
17. **What are the limitations of your dataset?** One site, about 10 months, a single winter test period, only 45 test days, reconstructed rather than metered hourly demand, and no weather or event data.
18. **Why did you not use LSTM?** The dataset is small (about 7,300 hourly points), and a deep network would need more data and tuning, would be harder to explain and could overfit. The tree models with lag features already capture the main patterns, and the project's focus was on honest evaluation and uncertainty rather than adding algorithms.
19. **How can this system help an EV charging station?** It gives next-day hourly demand forecasts and a range, so operators can plan capacity, schedule charging and avoid peak-power charges. Because peak coverage is only about 72%, peak decisions should include an extra safety margin.
20. **What would you improve in future work?** Add weather and event/academic-calendar data, use several sites and more than one season of data, calibrate the intervals separately for each forecast horizon, and keep the evaluation setup and software versions fixed for reproducibility.
