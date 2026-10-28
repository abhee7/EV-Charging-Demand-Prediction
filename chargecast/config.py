"""ChargeCast configuration.

Paths resolve against the repository root (the parent of chargecast/), so the
app behaves the same whichever directory it is launched from.

Read-only: nothing in this package writes to data/ or results/.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "ChargeCast"
APP_SUBTITLE = "EV charging demand intelligence"

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("CHARGECAST_ROOT", PACKAGE_DIR.parent))

DATA_PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
METRICS = RESULTS / "metrics"
PREDICTIONS = RESULTS / "predictions"
EXPLAINABILITY = RESULTS / "explainability"
PEAK_ANALYSIS = RESULTS / "peak_analysis"
FIGURES = RESULTS / "figures"
ARRIVAL_METRICS = RESULTS / "arrival_hour" / "metrics"
ARRIVAL_PREDICTIONS = RESULTS / "arrival_hour" / "predictions"

TZ_LOCAL = "America/Los_Angeles"

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
BASE = "#070C0F"
SURFACE = "#0F1619"
GLASS = "rgba(255,255,255,.03)"
HAIRLINE = "rgba(0,224,198,.12)"
GRID = "#162025"
TEXT = "#E6EDF0"
TEXT_MUTED = "#7C8F96"

CYAN = "#00E0C6"     # observed / actual
AMBER = "#FFB347"    # prediction
VIOLET = "#9B8CFF"
ROSE = "#FF7A9C"
LIME = "#8CE99A"

MODEL_COLORS = {
    "seasonal_naive": TEXT_MUTED,
    "linear_regression": VIOLET,
    "random_forest": AMBER,
    "xgboost": CYAN,
    "sarimax_fourier": ROSE,
    "sarimax": ROSE,
    "sarimax_+_fourier": ROSE,
}
FALLBACK_CYCLE = [CYAN, AMBER, VIOLET, ROSE, LIME, TEXT_MUTED]

# --------------------------------------------------------------------------
# Metric handling
# --------------------------------------------------------------------------
# Canonical key -> accepted column spellings, most likely first. Resolved at
# load time so the dashboard does not depend on one exact header spelling.
METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "MAE": ("MAE", "mae", "Mae"),
    "RMSE": ("RMSE", "rmse", "Rmse"),
    "R2": ("R2", "r2", "R\u00b2", "R_squared", "r_squared"),
    "sMAPE": ("sMAPE_percent", "sMAPE", "SMAPE", "smape_percent", "smape",
              "sMAPE_pct"),
    "MASE": ("MASE", "mase", "Mase"),
}

METRIC_META = {
    "MAE": {"label": "MAE", "unit": "kWh", "lower_is_better": True,
            "help": "Mean absolute error. Average size of the forecast error, in kWh."},
    "RMSE": {"label": "RMSE", "unit": "kWh", "lower_is_better": True,
             "help": "Root mean squared error. Penalises large misses more heavily than MAE."},
    "R2": {"label": "R\u00b2", "unit": "", "lower_is_better": False,
           "help": "Share of variance explained. Inflated on strongly seasonal series."},
    "sMAPE": {"label": "sMAPE", "unit": "%", "lower_is_better": True,
              "help": "Symmetric mean absolute percentage error. Stays defined when demand is zero."},
    "MASE": {"label": "MASE", "unit": "", "lower_is_better": True,
             "help": "Error relative to a seasonal naive benchmark. Below 1 means smaller error than that benchmark."},
}
METRIC_ORDER = ["MAE", "RMSE", "R2", "sMAPE", "MASE"]

FORECAST_HORIZON_HOURS = 24

NAV = [
    ("overview", "Overview"),
    ("forecast", "Forecast"),
    ("comparison", "Model comparison"),
    ("analytics", "Demand analytics"),
    ("explainability", "Explainability"),
    ("robustness", "Robustness"),
    ("about", "About the project"),
]

# --------------------------------------------------------------------------
# Shared research statements, written once so every page states them alike
# --------------------------------------------------------------------------
TARGET_LIMITATION = (
    "The primary hourly target is reconstructed by spreading each session's "
    "energy uniformly from connectionTime to doneChargingTime. doneChargingTime "
    "is only known once a session has ended, so the target uses information "
    "that would not be available at the forecast origin. It is not a directly "
    "observed real-time meter series. The arrival-hour allocation on the "
    "Robustness page tests how sensitive the findings are to this choice."
)

DM_STATEMENT = (
    "Random Forest has lower test MAE than XGBoost, while XGBoost has lower "
    "RMSE and slightly higher R\u00b2. The Diebold\u2013Mariano comparison "
    "between Random Forest and XGBoost is not statistically significant "
    "(p = 0.810), so their squared-error performance is not statistically "
    "distinguishable at the 5% level."
)

NOT_CAUSAL = (
    "Feature importance and SHAP values describe what a model's predictions "
    "are associated with. They are not causal inference: a high contribution "
    "does not show that the feature causes demand."
)

CROSS_TARGET_WARNING = (
    "Metrics computed on different target series are not directly comparable "
    "as accuracy scores, because the two series differ in scale and variance. "
    "What this experiment examines is whether the relative behaviour of the "
    "models is stable across both constructions."
)
