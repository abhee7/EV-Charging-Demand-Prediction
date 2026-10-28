# ChargeCast

**EV charging demand intelligence** — a read-only dashboard over the research
outputs of *A Comparative Study of Machine Learning and Time-Series Approaches
for EV Charging Demand Prediction*.

This package loads no models, fits nothing, retrains nothing, and never writes
to `data/` or `results/`. Every figure on screen comes from a stored result
file.

## Install and run

Extract `chargecast/` into the repository root, then:

```
cd C:\Users\admin\EV-Charging-Demand-Prediction
pip install -r chargecast\requirements.txt
streamlit run chargecast\app.py
```

Paths resolve against the repository root (the parent of `chargecast/`), not
the current working directory. Override with `CHARGECAST_ROOT` if needed.

## Verify

```
python chargecast\tests\smoke_test.py
```

Checks that every module imports, every page renders without raising, and no
ranking language appears in rendered copy. Run it after producing new results.

## Pages

| Page | Reads |
|---|---|
| Overview | hourly demand, test metrics, SARIMAX metrics, test predictions |
| Forecast | test predictions, SARIMAX predictions, arrival-hour predictions |
| Model comparison | test / validation / horizon metrics, both model families |
| Demand analytics | hourly demand, peak analysis, figures |
| Explainability | the seven explainability exports |
| Robustness | both demand series, both metric sets, both horizon sets |
| About the project | methodology, leakage controls, live artefact status |

## Files read

Primary
```
results/metrics/test_metrics_corrected.csv
results/metrics/validation_metrics_corrected.csv
results/metrics/horizon_metrics.csv
results/predictions/test_predictions_corrected.csv
```

SARIMAX + Fourier (the active time-series comparator)
```
results/metrics/sarimax_fourier_test_metrics.csv
results/metrics/sarimax_fourier_validation_metrics.csv
results/metrics/sarimax_fourier_horizon_metrics.csv
results/predictions/sarimax_fourier_test_predictions.csv
results/predictions/sarimax_fourier_validation_predictions.csv
```

Explainability
```
results/explainability/combined_shap_importance.csv
results/explainability/random_forest_feature_importance.csv
results/explainability/xgboost_feature_importance.csv
results/explainability/random_forest_shap_importance.csv
results/explainability/xgboost_shap_importance.csv
results/explainability/random_forest_shap_values.csv
results/explainability/xgboost_shap_values.csv
```

Data and robustness
```
data/processed/hourly_demand.csv
data/processed/model_data.csv
data/processed/hourly_demand_arrival_hour.csv
data/processed/model_data_arrival_hour.csv
results/arrival_hour/metrics/test_metrics_arrival_hour.csv
results/arrival_hour/metrics/validation_metrics_arrival_hour.csv
results/arrival_hour/metrics/horizon_metrics_arrival_hour.csv
results/arrival_hour/predictions/test_predictions_arrival_hour.csv
```

Directories scanned
```
results/peak_analysis/     (*.csv)
results/figures/           (*.png)
```

Quarantined — read but never used in any table or chart, shown only in a
collapsed "Superseded / legacy" section:
```
results/metrics/sarima_validation_metrics.csv
```

Any file that is absent renders a labelled empty state naming its path. All
paths live in `core/schema.py`; change them there and no page needs editing.

## Implementation notes

**Model / model capitalisation.** Metric files use `Model`, prediction files
use `model`. `loaders.model_column()` resolves either, so both are handled
without per-page branching.

**Metric column spellings.** `sMAPE_percent`, `sMAPE`, `SMAPE` and similar are
resolved to a canonical key at load time via `config.METRIC_ALIASES`. The
dashboard does not depend on one exact header spelling.

**Explainability headers.** These exports have no fixed schema, so the feature
and value columns are detected: the first non-numeric column is treated as the
feature name, the first numeric column as the value.

**Timestamps.** Prediction files are parsed as UTC. The hourly demand files
carry local timestamps whose offsets change across DST; parsing those directly
makes pandas fall back to an object dtype and break every `.dt` accessor, so
they are parsed as UTC first and then converted to `America/Los_Angeles`.

**Streamlit compatibility.** `use_container_width` is deprecated in favour of
`width="stretch"`. `core/ui.py` detects which the installed version accepts, so
the app runs clean on both.

**No `pages/` directory.** Streamlit auto-discovers a `pages/` folder next to
the entry script and would build a second navigation competing with the custom
sidebar. Views live in `views/`.

## Neutrality

The dashboard presents factual metric comparisons and identifies no overall
winner. This is enforced structurally rather than editorially:

* `components/metric_table.py` sorts alphabetically by model name by default
* sorting by a metric requires an explicit argument and renders a label saying
  it is a display sort, not a scientific ranking
* no badge, trophy, medal, highlight row or superlative exists in the codebase
* `assert_neutral()` scans rendered copy for ranking language, and the smoke
  test runs it against every page

The checker is negation-aware: "not a scientific ranking" passes, "the best
model is X" fails.

Stated wherever the two closest models appear: Random Forest has lower test MAE
than XGBoost, while XGBoost has lower RMSE and slightly higher R². The
Diebold–Mariano comparison between them is not statistically significant
(p = 0.810), so their squared-error performance is not statistically
distinguishable at the 5% level.

## Target reconstruction

Stated on the Overview, Robustness and About pages: the primary hourly target
is reconstructed by spreading each session's energy uniformly from
`connectionTime` to `doneChargingTime`. `doneChargingTime` is only known once a
session has ended, so the target uses information that would not be available
at the forecast origin. It is not a directly observed real-time meter series.
The arrival-hour allocation is the robustness experiment against that choice.

Metrics computed on the two target series are not directly comparable as
accuracy scores, because the series differ in scale and variance. The
Robustness page states this and presents both constructions symmetrically —
same layout, same chart types, same wording — without calling either correct.
