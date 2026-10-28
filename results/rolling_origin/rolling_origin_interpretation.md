# Rolling-origin evaluation of the existing XGBoost model

Setup: expanding window, 91 folds, each forecasting the next 24 hours recursively (existing `recursive_forecast` logic).
The model is refit each fold on all rows before the test window only. First test window starts 2018-11-24 00:00:00+00:00 (UTC);
last ends 2019-02-22 23:00:00+00:00. Configuration unchanged: {'n_estimators': 200, 'max_depth': 4, 'learning_rate': 0.05, 'subsample': 0.8, 'colsample_bytree': 0.8, 'objective': 'reg:squarederror', 'random_state': 42, 'n_jobs': -1}. Real data, existing features, no tuning.
Folds 1-46 fall in the existing validation period; folds 47-91 (45 folds) fall in the existing 45-day test period.

## Distribution across 24-hour windows
| Metric | all 91 folds | original-test-period folds | Single 45-day test |
|---|---|---|---|
| MAE | mean 6.22, std 2.54, min 2.66, max 18.48 | mean 6.01, std 2.02, min 2.66, max 13.95 | 6.49 |
| RMSE | mean 8.30, std 3.96, min 3.52, max 28.87 | mean 7.91, std 3.00, min 3.52, max 19.53 | 9.06 |
| R2 | mean -1.87, std 14.43, min -134.34, max 0.95 | mean 0.29, std 1.32, min -7.09, max 0.95 | 0.68 |

R2 is undefined (zero-variance actuals) in 0 fold(s); those are excluded from R2 statistics.

## Comparison
- 38% of windows have MAE above 6.49 and 30% have RMSE above 9.06; median window MAE is 5.70, median RMSE 7.42.
- RMSE coefficient of variation across windows is 0.48; RMSE ranges from 3.52 to 28.87.
- Per-window R2 ranges from -134.34 to 0.95. A single day has 24 points and its own variance, so per-window R2 is not on the same scale as the pooled 0.68.
- The single-test figures pool 1,080 hours before computing RMSE/R2, while each fold uses 24 hours. The mean of per-window RMSE and a pooled RMSE are different quantities.

## Leakage checks (performed in `rolling_origin_xgboost.py`)
- features rebuilt from history[:i] only match stored features, 300 random rows (max abs diff): 3.115285807098189e-13
- features of row t unchanged when target at t and later is altered by +1000: True
- stored rolling_mean_24 at t equals mean of targets t-24..t-1 (excludes t): True
- stored rolling_mean_168 at t equals mean of targets t-168..t-1 (excludes t): True
- stored lag_1 at t equals target at t-1: True
- every fold: all training rows strictly earlier than test_start (asserted): True
- Recursive forecast: within a window only the model's own previous predictions are appended to history (as in the existing logic); no actual test-window values enter features.

## Caveats
Consecutive folds share most training data and test days are adjacent, so folds are not independent. The data covers one site over about 10 months.
