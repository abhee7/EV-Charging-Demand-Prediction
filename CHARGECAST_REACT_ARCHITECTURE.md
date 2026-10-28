# ChargeCast 3.0 — Architecture

React + TypeScript presentation layer and FastAPI read-only API over the
verified research outputs of *A Comparative Study of Machine Learning and
Time-Series Approaches for EV Charging Demand Prediction*.

The existing Streamlit application in `chargecast/` is untouched and continues
to work. The two presentation layers coexist over the same artefacts.

---

## 1. Architecture

```
EV-Charging-Demand-Prediction/
├── data/processed/              verified — read only
├── results/                     verified — read only
│   ├── metrics/  predictions/  explainability/
│   ├── peak_analysis/  figures/  arrival_hour/
├── chargecast/                  existing Streamlit app (unchanged)
├── chargecast-api/              FastAPI service  :8000
├── chargecast-web/              React + Vite app :5173
├── scripts/smoke_test.py        end-to-end check of both services
└── CHARGECAST_REACT_ARCHITECTURE.md
```

Request path:

```
Browser
  → React page (lazy-loaded)
    → useApi hook (session cache, AbortController)
      → api/client.ts  fetch VITE_API_URL + fixed path
        → FastAPI route (validates query parameters)
          → service module (business logic)
            → artifact_loader (the only place a CSV is opened)
              → pandas.read_csv, cached on path + mtime + size
```

Nothing flows back the other way. There is no write path.

---

## 2. API endpoints

All under `/api`. Every endpoint is GET. `/docs` serves interactive docs.

| Endpoint | Query parameters | Returns |
|---|---|---|
| `/health` | — | Service status, repository root, artefact counts |
| `/overview` | — | Demand summary, ACF highlights, forecast metadata |
| `/demand/summary` | — | Observations, total, mean, median, peak, percentiles |
| `/demand/hourly` | `downsample` 1–24, `limit` | Demand ribbon series |
| `/demand/profile` | — | Mean by hour of day with IQR band |
| `/demand/weekday` | — | Weekday against weekend by hour |
| `/demand/monthly` | — | Totals and means by calendar month |
| `/demand/heatmap` | — | Hour × day-of-week cells with min/max |
| `/demand/distribution` | `bins` 8–200 | Histogram with P75/P90/P95/P99 |
| `/demand/acf` | `max_lag` 1–1000, `lag` | ACF series, band, highlights |
| `/demand/scenario` | `change` −20…50 | Arithmetically scaled summary |
| `/demand/capacity` | `capacity_kw` ∈ {60,120,180,240,360} | Sizing pressure |
| `/forecast/models` | `prediction_set` | Models with stored predictions |
| `/forecast/windows` | `prediction_set`, `model` | Stored window list |
| `/forecast/{window_id}` | `model` (required), `prediction_set`, `horizon` | One 24-hour replay + window stats |
| `/models/metrics` | `metric` | Test metrics, alphabetical by model |
| `/models/validation` | — | Validation metrics as stored |
| `/models/horizon` | `metric` | Error by horizon, one series per model |
| `/models/dm/audited` | — | **Audited** DM artefact as stored |
| `/models/dm/interactive` | `model_a`, `model_b` (required), `hac_lag` 0–72 | **Exploratory** recomputation |
| `/peak/audited` | — | **Audited** peak detection artefact |
| `/peak/thresholds` | — | **Audited** high-demand thresholds |
| `/peak/supplementary` | — | The other eight peak-analysis exports |
| `/peak/interactive` | `percentile` ∈ {75,90,95,99}, `model` | **Exploratory** recomputation |
| `/explainability/shap` | — | Combined SHAP importance |
| `/explainability/random-forest` | `source` ∈ {shap, importance} | RF attribution |
| `/explainability/xgboost` | `source` ∈ {shap, importance} | XGBoost attribution |
| `/robustness/summary` | — | Series facts for both target constructions |
| `/robustness/metrics` | — | Model metrics under both constructions |
| `/robustness/horizon` | `metric` | Horizon curves under both constructions |
| `/research/artifacts` | — | Live status of every expected artefact |
| `/research/provenance` | — | Study description, limitations, provenance rows |

Validation returns HTTP 422 for out-of-range or malformed parameters.
Domain-level rejections (unknown model, unsupported percentile) return HTTP 200
with `available: false` and a reason, so the UI shows an empty state rather
than an error page.

---

## 3. Artifact mapping

| Artefact | Key | Consumed by |
|---|---|---|
| `data/processed/hourly_demand.csv` | `hourly_demand` | Overview, Analytics, Peak, Robustness |
| `data/processed/model_data.csv` | `model_data` | registered; reserved |
| `data/processed/hourly_demand_arrival_hour.csv` | `hourly_demand_arrival` | Robustness |
| `data/processed/model_data_arrival_hour.csv` | `model_data_arrival` | registered; reserved |
| `results/metrics/test_metrics_corrected.csv` | `test_metrics` | Model Lab, Overview, Robustness |
| `results/metrics/validation_metrics_corrected.csv` | `validation_metrics` | Model Lab |
| `results/metrics/horizon_metrics.csv` | `horizon_metrics` | Model Lab, Forecast |
| `results/predictions/test_predictions_corrected.csv` | `test_predictions` | Forecast, DM explorer, Peak explorer |
| `results/metrics/sarimax_fourier_test_metrics.csv` | `sarimax_test_metrics` | Model Lab, Overview |
| `results/metrics/sarimax_fourier_validation_metrics.csv` | `sarimax_validation_metrics` | Model Lab |
| `results/metrics/sarimax_fourier_horizon_metrics.csv` | `sarimax_horizon_metrics` | Model Lab |
| `results/predictions/sarimax_fourier_test_predictions.csv` | `sarimax_test_predictions` | Forecast, DM explorer |
| `results/predictions/sarimax_fourier_validation_predictions.csv` | `sarimax_validation_predictions` | registered |
| **`results/metrics/diebold_mariano_tests.csv`** | `dm_tests` | **Model Lab — audited section** |
| **`results/peak_analysis/model_peak_detection.csv`** | `peak_model_detection` | **Peak — audited section** |
| **`results/peak_analysis/high_demand_thresholds.csv`** | `peak_thresholds` | **Peak — audited section** |
| `results/peak_analysis/model_peak_values.csv` | `peak_model_values` | Peak supplementary |
| `results/peak_analysis/model_peak_vs_nonpeak_error.csv` | `peak_error_split` | Peak supplementary |
| `results/peak_analysis/top_10_peak_hours.csv` | `peak_top_hours` | Peak supplementary |
| `results/peak_analysis/overall_demand_summary.csv` | `peak_overall_summary` | Peak supplementary |
| `results/peak_analysis/hourly_demand_profile.csv` | `peak_hourly_profile` | Peak supplementary |
| `results/peak_analysis/day_of_week_profile.csv` | `peak_dow_profile` | Peak supplementary |
| `results/peak_analysis/weekday_weekend_profile.csv` | `peak_weekday_weekend` | Peak supplementary |
| `results/peak_analysis/monthly_demand_profile.csv` | `peak_monthly_profile` | Peak supplementary |
| `results/peak_analysis/all_test_predictions_for_analysis.csv` | `peak_all_predictions` | registered |
| `results/explainability/combined_shap_importance.csv` | `shap_combined` | Explainability |
| `results/explainability/random_forest_feature_importance.csv` | `rf_importance` | Explainability |
| `results/explainability/xgboost_feature_importance.csv` | `xgb_importance` | Explainability |
| `results/explainability/random_forest_shap_importance.csv` | `rf_shap_importance` | Explainability |
| `results/explainability/xgboost_shap_importance.csv` | `xgb_shap_importance` | Explainability |
| `results/explainability/random_forest_shap_values.csv` | `rf_shap_values` | registered |
| `results/explainability/xgboost_shap_values.csv` | `xgb_shap_values` | registered |
| `results/arrival_hour/metrics/test_metrics_arrival_hour.csv` | `arrival_test_metrics` | Robustness |
| `results/arrival_hour/metrics/validation_metrics_arrival_hour.csv` | `arrival_validation_metrics` | registered |
| `results/arrival_hour/metrics/horizon_metrics_arrival_hour.csv` | `arrival_horizon_metrics` | Robustness |
| `results/arrival_hour/predictions/test_predictions_arrival_hour.csv` | `arrival_test_predictions` | Forecast |
| `results/figures/*.png` | directory | Research status |
| `results/metrics/sarima_validation_metrics.csv` | `legacy_sarima` | **Quarantined** — never a current result |

Paths live only in `app/services/artifact_loader.py`. Change one there and no
route or page needs editing.

---

## 4. Research-integrity rules

**Read-only.** The API opens files for reading only. `test_no_write_operations_in_source`
greps the whole package for write calls; `test_repository_files_unchanged_by_requests`
hashes `data/` and `results/` before and after exercising the API.

**Audited versus exploratory.** Two results appear in both forms. They are
served by separate endpoints, carry distinct `provenance` strings, and are
rendered in separate cards with different accent colours.

| | Audited | Exploratory |
|---|---|---|
| Diebold-Mariano | `/models/dm/audited` reads `diebold_mariano_tests.csv` | `/models/dm/interactive` recomputes from stored predictions |
| Peak detection | `/peak/audited` reads `model_peak_detection.csv` | `/peak/interactive` recomputes at a chosen percentile |

`provenance` is `VERIFIED RESEARCH ARTIFACT` or
`EXPLORATORY — NOT THE AUDITED RESULT`. The interactive peak endpoint defaults
to the audited 90th percentile and sets `differsFromAudited` with a notice when
another percentile is chosen. An interactive request never mutates the audited
response — asserted by `test_interactive_does_not_mutate_the_audited_response`.

**No fabricated data.** No `np.random`, `Math.random()`, faker, mock, fixture or
placeholder data exists in either package; both test suites assert this. A
missing artefact yields a structured `available: false` payload and the UI
renders an empty state naming the path.

**No hard-coded research values.** `test_no_research_values_hard_coded_in_source`
fails the build if a published figure appears in backend source.

**Neutral presentation.** Models default to alphabetical order everywhere.
Sorting by a metric requires explicit selection and renders "Sorting is for
display only; it is not a scientific ranking." No badge, medal or superlative
exists. `test_no_ranking_language_in_api_source` scans backend source for
ranking language with word-boundary patterns.

**Legacy SARIMA.** `sarima_validation_metrics.csv` is registered in the `legacy`
group, excluded from every metric, chart and comparison, and appears only as a
`quarantined` row on the Research page.

**Target limitation.** The retrospective reconstruction caveat is defined once
in `app/config.py` and surfaced on Overview, Robustness and Research.

**Security.** Query parameters are validated by FastAPI. No endpoint accepts a
filesystem path — `test_no_arbitrary_path_parameter` scans the OpenAPI schema
for a parameter named `path`, `file`, `filename`, `filepath` or `csv`. CORS is
restricted to the configured local frontend origins, methods to GET.
Environment variables are never echoed; the global handler returns a clean
message rather than a traceback.

---

## 5. Data flow examples

**Overview demand ribbon.** `Overview.tsx` calls `useApi('/api/demand/hourly',
{downsample: 2})` → `demand_service.hourly` loads `hourly_demand`, downsamples,
attaches the P90 threshold → `DemandRibbon` renders an area chart with a brush.

**Audited DM.** `ModelLab.tsx` calls `/api/models/dm/audited` →
`metrics_service.dm_audited` loads `dm_tests`, resolves columns at runtime,
returns both the resolved comparison objects and the raw stored rows → the page
shows summary tiles plus the source table exactly as stored, under a
`VERIFIED RESEARCH ARTIFACT` badge.

**Interactive peak.** The percentile select calls `/api/peak/interactive?percentile=95`
→ `peak_service.interactive` concatenates the stored prediction sets, thresholds
at the chosen percentile and scores each model → the page renders the table, a
confusion matrix, and a notice that the threshold differs from the audited one.

---

## 6. Frontend structure

```
src/
├── main.tsx  App.tsx            router, lazy routes
├── layouts/AppShell.tsx         collapsible sidebar, top bar, footer, API status
├── pages/                       Overview Forecast ModelLab Analytics
│                                Peak Explainability Robustness Research
├── charts/                      theme.ts + 11 chart components
├── components/                  KpiCard EmptyState QueryBoundary DataTable
│                                ProvenanceNote ResearchNote SectionHeading
│                                StatTile PageHeader + ui/ primitives
├── hooks/                       useApi, useHealth
├── api/                         client.ts, endpoints.ts
├── lib/                         utils.ts (cn), format.ts
└── types/api.ts                 typed responses, no `any`
```

Design tokens live in `tailwind.config.ts` and `charts/theme.ts`:
base `#070C0F`, surface `#0F1619`, signal `#00E0C6` (observed), prediction
`#FFB347`, violet `#9B8CFF`, rose `#FF7A9C`, lime `#8CE99A`, text `#E6EDF0`,
muted `#7C8F96`, grid `#162025`. Space Grotesk for display, Inter for body,
tabular numerals on every metric.

---

## 7. Running and deployment

```bash
# Backend
cd chargecast-api
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd chargecast-web
npm install
npm run dev
```

Frontend <http://localhost:5173> · Backend <http://localhost:8000> ·
Docs <http://localhost:8000/docs>

End-to-end check:

```bash
python scripts/smoke_test.py --with-frontend
```

**Production.** `npm run build` emits static assets to `chargecast-web/dist/`;
serve them from any static host with `VITE_API_URL` set at build time. Run the
API behind a process manager:
`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`. Set
`CHARGECAST_CORS_ORIGINS` to the deployed frontend origin. Because the API is
read-only and unauthenticated, keep it on a trusted network or behind a
reverse proxy that handles authentication.
