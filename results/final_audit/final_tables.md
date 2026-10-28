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
