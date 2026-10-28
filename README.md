# EV Charging Demand Prediction Using Machine Learning and Time-Series Analysis

Hourly EV charging demand forecasting for a Caltech charging site (ACN-Data), with
24-hour-ahead recursive forecasts, a rolling-origin robustness check, and prediction
intervals whose real coverage was measured and then calibrated with conformal
prediction. A read-only dashboard (**ChargeCast**) presents the verified results.

> B.Tech Data Science project, Vishwakarma Institute of Technology.
> Authors: Abhishek Dombale, Harshwardhan Gangarde. Guide: Prof. Gopal Deshmukh.

---

## Contents

1. [Key results](#key-results)
2. [What the project does](#what-the-project-does)
3. [Dataset](#dataset)
4. [Method in brief](#method-in-brief)
5. [Repository layout](#repository-layout)
6. [Setup](#setup)
7. [Reproducing the results](#reproducing-the-results)
8. [ChargeCast dashboard](#chargecast-dashboard)
9. [Research integrity and audit](#research-integrity-and-audit)
10. [Limitations](#limitations)
11. [Data attribution and citation](#data-attribution-and-citation)

---

## Key results

All numbers are from the audited result files in `results/` (see
`results/final_audit/FINAL_AUDIT_REPORT.md`). Test period: 45 non-overlapping
24-hour windows (1,080 hours), 8 Jan – 22 Feb 2019.

**Point forecasts**

| Model | MAE (kWh) | RMSE (kWh) | R² |
|---|--:|--:|--:|
| XGBoost | 6.49 | 9.06 | 0.682 |
| Random Forest | 6.38 | 9.10 | 0.679 |
| Linear Regression | 7.52 | 9.94 | 0.617 |
| Seasonal Naive | 7.14 | 10.52 | 0.572 |
| SARIMAX + Fourier | 11.06 | 13.73 | 0.270 |

XGBoost and Random Forest are **not** significantly different (Diebold–Mariano
p = 0.81), so this table is not a ranking claim. Both differ significantly from
Seasonal Naive and from the SARIMAX + Fourier configuration used here.

**Rolling-origin robustness (XGBoost, 91 daily windows)**

| | Mean | Std | Median | Min | Max |
|---|--:|--:|--:|--:|--:|
| MAE (kWh) | 6.22 | 2.54 | 5.70 | 2.66 | 18.48 |
| RMSE (kWh) | 8.30 | 3.96 | 7.42 | 3.52 | 28.87 |

Pooled over all forecast hours the R² is 0.672. Single-day R² is not comparable
to the pooled value: on low-variance days it can be very negative (down to −134).

**Prediction intervals (nominal 90%, same 1,080 test hours)**

| Method | Empirical coverage | Avg width (kWh) |
|---|--:|--:|
| Quantile XGBoost (uncalibrated) | 71.2% | 29.46 |
| Conformalized quantile XGBoost | 90.9% | 34.45 |

The calibration offset is 2.63 kWh, learned from validation data only. Peak
hours (actual ≥ 37.46 kWh) remain under-covered: 72.2% against 93.0% for
non-peak hours. These are *empirical* coverages on one test period, not
guarantees.

---

## What the project does

- Rebuilds an **hourly demand series** from ACN-Data charging sessions.
- Engineers 17 **lag, rolling-statistic and calendar features** that use only
  past information.
- Forecasts **24 hours ahead** with a recursive strategy and a strict
  chronological 70/15/15 train/validation/test split.
- Compares **XGBoost, Random Forest, Linear Regression, Seasonal Naive and
  SARIMAX + Fourier**, with a Diebold–Mariano test of the differences.
- Evaluates XGBoost on **91 rolling-origin daily windows**.
- Builds **quantile prediction intervals** and calibrates them with
  **conformalized quantile regression**.
- Analyses **peak vs non-peak hours**, **coverage by forecast horizon**, and
  **SHAP** feature importance.
- Serves the verified outputs through a **read-only dashboard**.

---

## Dataset

[ACN-Data](https://ev.caltech.edu/dataset), the open dataset of the Caltech
Adaptive Charging Network (session-level records: connection time, end of
charging, energy delivered, station).

| Item | Value |
|---|---|
| Sessions used | 16,972 (of 17,000 downloaded) |
| Period | 25 Apr 2018 – 22 Feb 2019 (about ten months) |
| Hourly observations | 7,288 (no gaps; 486 zero-demand hours) |
| Mean / max hourly demand | 21.35 / 136.36 kWh |

Hourly demand is **reconstructed**: each session's energy is spread evenly
between connection and the end of charging and summed per clock hour (local
time, America/Los_Angeles). It is not metered load.

**The raw session file is not included in this repository** (redistribution
terms are not clear and it contains user IDs). `data/processed/` is included, so
you can reproduce everything from the modelling step onwards without it. To
re-create the raw file, see [Re-downloading the raw data](#re-downloading-the-raw-data).

---

## Method in brief

| Step | Detail |
|---|---|
| Features (17) | `lag_1, lag_2, lag_24, lag_48, lag_168, lag_336`, rolling mean/std over 24 h and 168 h (shifted by one hour so the current value is excluded), `hour, day_of_week, day_of_month, month, week_of_year, is_weekend, is_business_hour` |
| Split | Chronological: 5,101 train / 1,093 validation / 1,094 test rows |
| Selection | Candidates compared on 45 validation windows; selected models refitted on train + validation, then evaluated once on the test windows |
| Forecasting | Recursive 24-hour forecasts; each prediction is appended to the history for the next hour; negatives clipped to 0 |
| XGBoost | `n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, objective=reg:squarederror, random_state=42` |
| SARIMAX | ARMA(1,0,1) errors + constant, daily and weekly Fourier terms (K=3 each), refitted for every window |
| Rolling-origin | Expanding training window, 91 consecutive daily 24-hour windows |
| Intervals | `reg:quantileerror` at 0.05 / 0.50 / 0.95; median fed back in the recursion |
| Conformal | Quantile model fitted on train only; conformity scores `max(lower − y, y − upper)` from validation windows; offset added to both bounds on the test windows |

---

## Repository layout

```
.
├── download_acndata.py            raw ACN-Data download (needs an API token)
├── prepare_hourly_demand.py       sessions -> hourly demand
├── prepare_model_data.py          hourly demand -> model features
├── train_models.py                Linear Regression / Random Forest / XGBoost / Seasonal Naive
├── train_sarima.py                SARIMAX + Fourier
├── run_dm_tests.py                Diebold-Mariano tests
├── run_shap_analysis.py           SHAP feature importance
├── run_peak_analysis.py           peak vs non-peak analysis
├── generate_figures.py            report figures
├── rolling_origin_xgboost.py      rolling-origin evaluation       -> results/rolling_origin/
├── prediction_intervals_xgboost.py quantile intervals             -> results/prediction_intervals/
├── conformal_intervals_xgboost.py  conformal calibration          -> results/conformal_prediction_intervals/
├── final_audit_tables.py          final report tables             -> results/final_audit/
├── train_models_arrival_hour.py   alternative demand definition (arrival-hour variant)
├── data/processed/                hourly series and model features
├── results/                       metrics, predictions, figures and experiment outputs
│   └── final_audit/               FINAL_AUDIT_REPORT.md, FINAL_PROJECT_REPORT.md, tables
├── chargecast/                    Streamlit dashboard (original)
├── chargecast-api/                FastAPI backend (read-only)
├── chargecast-web/                React dashboard
└── scripts/smoke_test.py          end-to-end smoke test
```

Each experiment script writes only to its own folder under `results/`.

---

## Setup

Tested with Python 3.13 and Node.js 24.

```bash
python -m venv .venv
# Windows PowerShell:  .\.venv\Scripts\Activate.ps1
# macOS / Linux:       source .venv/bin/activate

pip install pandas numpy scipy scikit-learn xgboost statsmodels shap matplotlib
```

The experiments in `results/rolling_origin/`, `results/prediction_intervals/`
and `results/conformal_prediction_intervals/` were run with XGBoost 3.4.1,
pandas 3.0.6 and numpy 2.5.3. Run `pip freeze` to record your own versions;
see [Reproducibility](#reproducibility).

---

## Reproducing the results

Run from the repository root. `data/processed/` is already present, so steps 1–2
are only needed if you re-create the raw data.

```bash
# 1-2. Rebuild hourly demand and features (needs data/raw/acndata_caltech.csv)
python prepare_hourly_demand.py
python prepare_model_data.py

# 3. Point-forecast models and SARIMAX
python train_models.py
python train_sarima.py          # slow: refits for every window

# 4. Post-hoc analyses and figures
python run_dm_tests.py
python run_shap_analysis.py
python run_peak_analysis.py
python generate_figures.py

# 5. Additional experiments (each writes to its own results/ subfolder)
python rolling_origin_xgboost.py
python prediction_intervals_xgboost.py
python conformal_intervals_xgboost.py     # reads the quantile experiment's outputs
python final_audit_tables.py
```

> Steps 3 and 4 **overwrite** the files in `results/metrics`, `results/predictions`,
> `results/explainability`, `results/peak_analysis` and `results/figures`.
> Copy `results/` first if you want to keep the originals.

### Re-downloading the raw data

1. Request an API token on the [ACN-Data site](https://ev.caltech.edu/dataset).
2. Set it as an environment variable (never commit it):

   ```bash
   # PowerShell
   $env:ACN_API_TOKEN="your_token"
   # bash
   export ACN_API_TOKEN="your_token"
   ```

3. **Edit `START_PAGES` in `download_acndata.py`** before a fresh download. It is
   set to resume the Caltech site from page 676 (earlier pages were downloaded in
   a previous run). For a complete download from scratch, set `"caltech": 1`.
   The script also fetches the JPL and Office 1 sites, which this project does
   not use; remove them from `SITES` to skip them.

   ```bash
   python download_acndata.py
   ```

### Reproducibility

An independent re-run of the baseline XGBoost in a different software
environment gave MAE 6.46 / RMSE 9.03 / R² 0.684 against the stored
6.49 / 9.06 / 0.682. The difference appears from the first forecast hour, so it
is a model-fit difference most likely caused by library versions, not a change
in method. The stored results are the ones cited throughout.

---

## ChargeCast dashboard

A read-only presentation layer over the verified results. The FastAPI backend
never writes to `data/` or `results/`, never retrains anything, and accepts no
filesystem path from the caller. The original Streamlit dashboard in
`chargecast/` still works alongside it.

```bash
# Backend  -> http://localhost:8000  (API docs at /docs)
cd chargecast-api
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend -> http://localhost:5173
cd chargecast-web
npm install
npm run dev

# Original Streamlit dashboard (from the repository root)
pip install -r chargecast/requirements.txt
streamlit run chargecast/app.py
```

Set `CHARGECAST_ROOT` if the repository root is not the parent of
`chargecast-api/`. Set `VITE_API_URL` in `chargecast-web/.env.local` if the API
is not on port 8000.

Verify:

```bash
cd chargecast-api && python -m pytest tests/ -q     # backend test suite
cd chargecast-web && npm run lint && npm run build  # lint + typecheck + build
python scripts/smoke_test.py --with-frontend        # both services respond
```

`CHARGECAST_REACT_ARCHITECTURE.md` documents the architecture, every endpoint,
the artefact mapping and deployment.

---

## Research integrity and audit

- A **leakage audit** passed: chronological split; features built only from
  earlier data (verified on 300 random rows); rolling statistics exclude the
  current hour; rolling-origin training data strictly earlier than each window;
  conformal calibration uses validation data only; test targets are never used
  for fitting or calibration.
- The dashboard serves audited artefacts as stored and labels in-dashboard
  recomputations as exploratory. Missing artefacts produce a structured empty
  state, never a fabricated chart.
- No model is described as best, winner or superior anywhere. The legacy
  SARIMA file stays quarantined.
- `results/final_audit/FINAL_AUDIT_REPORT.md` lists every discrepancy found
  during the audit, including two legacy files that hold superseded values:
  `results/metrics/model_metrics.csv` and `results/predictions/test_predictions.csv`.
  **Do not cite those two files**; use the `*_corrected` files instead.
- The three XGBoost variants (squared error, quantile, conformal) differ in
  loss function and training rows, so their MAE/RMSE are not directly
  comparable. Use the baseline for point-forecast performance and the quantile
  and conformal experiments only for uncertainty and calibration.

---

## Limitations

- One charging site and about ten months of data; the test period is winter only.
- Only 45 test days and 91 rolling days; neighbouring days are not independent.
- Peak-demand hours remain under-covered (72.2%) and under-predicted.
- Conformal exchangeability assumptions may not strictly hold for hourly time
  series, and calibration windows start at a different clock time (16:00 local)
  from test windows (05:00 local).
- Weather, traffic and event data are not used.
- Hourly demand is reconstructed from session energy, not metered.
- Results are specific to this dataset and should not be generalised to other
  sites without re-evaluation.

---

## Data attribution and citation

This project uses ACN-Data. If you use this work, please cite the dataset:

> Z. J. Lee, T. Li and S. H. Low, "ACN-Data: Analysis and Applications of an
> Open EV Charging Dataset," in *Proc. 10th ACM International Conference on
> Future Energy Systems (e-Energy '19)*, 2019, pp. 139–149.
> doi: [10.1145/3307772.3328313](https://doi.org/10.1145/3307772.3328313)

Please also consult the [ACN-Data site](https://ev.caltech.edu/dataset) for
its current terms of use before redistributing any data.
