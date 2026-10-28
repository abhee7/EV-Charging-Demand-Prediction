"""ChargeCast API configuration.

The repository root is taken from CHARGECAST_ROOT, falling back to the parent
of chargecast-api/, which is correct for the standard layout. No absolute
path is baked into application logic.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

APP_NAME = "ChargeCast API"
APP_VERSION = "3.0.0"
DATASET_NAME = "Caltech ACN"
UNIT = "kWh/h"  # reconstructed hourly energy, not instantaneous power

PACKAGE_DIR = Path(__file__).resolve().parent
API_DIR = PACKAGE_DIR.parent


def repo_root() -> Path:
    env = os.environ.get("CHARGECAST_ROOT", "").strip()
    return Path(env).expanduser().resolve() if env else API_DIR.parent


@lru_cache(maxsize=1)
def cors_origins() -> list[str]:
    raw = os.environ.get(
        "CHARGECAST_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


# --------------------------------------------------------------------------
# Analysis defaults, mirroring the research pipeline
# --------------------------------------------------------------------------
DM_HAC_LAG = 23
PEAK_PERCENTILE = 90
PEAK_PERCENTILE_OPTIONS = [75, 90, 95, 99]
CAPACITY_OPTIONS = [60, 120, 180, 240, 360]
FORECAST_HORIZON_HOURS = 24
TZ_LOCAL = "America/Los_Angeles"

METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "mae": ("MAE", "mae"),
    "rmse": ("RMSE", "rmse"),
    "r2": ("R2", "r2", "R\u00b2", "R_squared"),
    "smape": ("sMAPE_percent", "sMAPE", "SMAPE", "smape_percent", "smape"),
    "mase": ("MASE", "mase"),
}
METRIC_ORDER = ["mae", "rmse", "r2", "smape", "mase"]
METRIC_LABELS = {"mae": "MAE", "rmse": "RMSE", "r2": "R\u00b2",
                 "smape": "sMAPE", "mase": "MASE"}
METRIC_UNITS = {"mae": UNIT, "rmse": UNIT, "r2": "", "smape": "%", "mase": ""}
METRIC_LOWER_IS_BETTER = {"mae": True, "rmse": True, "r2": False,
                          "smape": True, "mase": True}

# --------------------------------------------------------------------------
# Research statements, served to the frontend so wording stays in one place
# --------------------------------------------------------------------------
TARGET_LIMITATION = (
    "The primary hourly target is a retrospective reconstruction: each "
    "session's energy is allocated uniformly from connectionTime to "
    "doneChargingTime, and doneChargingTime is only known after the session "
    "completes. It is therefore not a directly observed real-time power "
    "signal, and it contains information that would not be available at the "
    "actual forecast origin."
)
CROSS_TARGET_WARNING = (
    "The two targets represent different definitions of hourly demand. Their "
    "absolute error values should not be interpreted as a direct accuracy "
    "comparison between target definitions."
)
NOT_CAUSAL = (
    "SHAP describes model contribution, not causality. A large contribution "
    "does not establish that the feature causes demand."
)
PEAK_CAVEAT = (
    "A peak hour is reconstructed demand at or above the stated percentile "
    "threshold. Peak classification is a property of the forecast series and "
    "does not indicate electrical overload."
)
CAPACITY_CAVEAT = (
    "The target is reconstructed hourly energy expressed as kWh/h "
    "equivalent, not instantaneous power. Comparison against a nominal "
    "charger rating indicates sizing pressure only and does not establish an "
    "electrical overload."
)
SCENARIO_CAVEAT = (
    "Scenario simulation \u2014 not a new forecast. The historical series is "
    "scaled arithmetically. No model is run and no stored data is modified."
)
AUDITED_NOTE = (
    "Values are read directly from the verified research pipeline output."
)
EXPLORATORY_NOTE = (
    "Recomputed from stored predictions using the selected parameters. "
    "Exploratory: it does not overwrite or replace the audited result."
)
