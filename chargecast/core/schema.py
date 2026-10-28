"""Declared artefacts.

Every path here is one of the verified filenames from the research repository.
Loaders validate against this registry so a mismatch surfaces as a readable
panel rather than a KeyError during a demonstration.

Column requirements are kept deliberately minimal. Metric column spellings are
resolved at load time (see config.METRIC_ALIASES) and explainability files
carry no confirmed headers, so those are detected rather than asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import config


@dataclass(frozen=True)
class FileSpec:
    key: str
    path: Path
    label: str
    produced_by: str
    required: tuple[str, ...] = ()
    time_cols: tuple[str, ...] = ()
    utc: bool = True
    group: str = "other"


HOURLY_COLS = ("timestamp", "demand_kWh", "hour", "day_of_week",
               "day_of_month", "month", "week_of_year", "is_weekend",
               "is_business_hour")

PRED_COLS = ("model", "forecast_window", "origin", "timestamp", "horizon",
             "actual", "prediction")

SPECS: dict[str, FileSpec] = {
    # ---------------- Primary metrics ----------------
    "test_metrics": FileSpec(
        "test_metrics", config.METRICS / "test_metrics_corrected.csv",
        "Primary test metrics", "train_models.py",
        required=("Model",), group="primary",
    ),
    "validation_metrics": FileSpec(
        "validation_metrics", config.METRICS / "validation_metrics_corrected.csv",
        "Primary validation metrics", "train_models.py",
        required=("Model",), group="primary",
    ),
    "horizon_metrics": FileSpec(
        "horizon_metrics", config.METRICS / "horizon_metrics.csv",
        "Primary metrics by horizon", "train_models.py",
        required=("Model", "Horizon"), group="primary",
    ),
    "test_predictions": FileSpec(
        "test_predictions", config.PREDICTIONS / "test_predictions_corrected.csv",
        "Primary test predictions", "train_models.py",
        required=("model", "origin", "timestamp", "horizon", "actual",
                  "prediction"),
        time_cols=("origin", "timestamp"), utc=True, group="primary",
    ),

    # ---------------- SARIMAX + Fourier ----------------
    "sarimax_test_metrics": FileSpec(
        "sarimax_test_metrics",
        config.METRICS / "sarimax_fourier_test_metrics.csv",
        "SARIMAX + Fourier test metrics", "train_sarima.py",
        required=("Model",), group="sarimax",
    ),
    "sarimax_validation_metrics": FileSpec(
        "sarimax_validation_metrics",
        config.METRICS / "sarimax_fourier_validation_metrics.csv",
        "SARIMAX + Fourier validation metrics", "train_sarima.py",
        required=("Model",), group="sarimax",
    ),
    "sarimax_horizon_metrics": FileSpec(
        "sarimax_horizon_metrics",
        config.METRICS / "sarimax_fourier_horizon_metrics.csv",
        "SARIMAX + Fourier metrics by horizon", "train_sarima.py",
        required=("Model", "Horizon"), group="sarimax",
    ),
    "sarimax_test_predictions": FileSpec(
        "sarimax_test_predictions",
        config.PREDICTIONS / "sarimax_fourier_test_predictions.csv",
        "SARIMAX + Fourier test predictions", "train_sarima.py",
        time_cols=("origin", "timestamp"), utc=True, group="sarimax",
    ),
    "sarimax_validation_predictions": FileSpec(
        "sarimax_validation_predictions",
        config.PREDICTIONS / "sarimax_fourier_validation_predictions.csv",
        "SARIMAX + Fourier validation predictions", "train_sarima.py",
        time_cols=("origin", "timestamp"), utc=True, group="sarimax",
    ),

    # ---------------- Explainability ----------------
    "shap_combined": FileSpec(
        "shap_combined", config.EXPLAINABILITY / "combined_shap_importance.csv",
        "Combined SHAP importance", "the explainability step", group="explain",
    ),
    "rf_importance": FileSpec(
        "rf_importance",
        config.EXPLAINABILITY / "random_forest_feature_importance.csv",
        "Random Forest feature importance", "the explainability step",
        group="explain",
    ),
    "xgb_importance": FileSpec(
        "xgb_importance",
        config.EXPLAINABILITY / "xgboost_feature_importance.csv",
        "XGBoost feature importance", "the explainability step",
        group="explain",
    ),
    "rf_shap_importance": FileSpec(
        "rf_shap_importance",
        config.EXPLAINABILITY / "random_forest_shap_importance.csv",
        "Random Forest SHAP importance", "the explainability step",
        group="explain",
    ),
    "xgb_shap_importance": FileSpec(
        "xgb_shap_importance",
        config.EXPLAINABILITY / "xgboost_shap_importance.csv",
        "XGBoost SHAP importance", "the explainability step", group="explain",
    ),
    "rf_shap_values": FileSpec(
        "rf_shap_values",
        config.EXPLAINABILITY / "random_forest_shap_values.csv",
        "Random Forest SHAP values", "the explainability step", group="explain",
    ),
    "xgb_shap_values": FileSpec(
        "xgb_shap_values",
        config.EXPLAINABILITY / "xgboost_shap_values.csv",
        "XGBoost SHAP values", "the explainability step", group="explain",
    ),

    # ---------------- Data ----------------
    "hourly_demand": FileSpec(
        "hourly_demand", config.DATA_PROCESSED / "hourly_demand.csv",
        "Hourly demand (interval allocation)", "prepare_hourly_demand.py",
        required=("timestamp", "demand_kWh"),
        time_cols=("timestamp",), utc=False, group="data",
    ),
    "model_data": FileSpec(
        "model_data", config.DATA_PROCESSED / "model_data.csv",
        "Model feature table", "prepare_model_data.py",
        required=("timestamp", "demand_kWh"),
        time_cols=("timestamp",), utc=False, group="data",
    ),

    # ---------------- Robustness ----------------
    "hourly_demand_arrival": FileSpec(
        "hourly_demand_arrival",
        config.DATA_PROCESSED / "hourly_demand_arrival_hour.csv",
        "Hourly demand (arrival-hour allocation)",
        "prepare_arrival_hour_demand.py",
        required=("timestamp", "demand_kWh"),
        time_cols=("timestamp",), utc=False, group="robustness",
    ),
    "model_data_arrival": FileSpec(
        "model_data_arrival",
        config.DATA_PROCESSED / "model_data_arrival_hour.csv",
        "Model feature table (arrival-hour)", "prepare_arrival_model_data.py",
        required=("timestamp", "demand_kWh"),
        time_cols=("timestamp",), utc=False, group="robustness",
    ),
    "arrival_test_metrics": FileSpec(
        "arrival_test_metrics",
        config.ARRIVAL_METRICS / "test_metrics_arrival_hour.csv",
        "Arrival-hour test metrics", "train_models_arrival_hour.py",
        required=("Model",), group="robustness",
    ),
    "arrival_validation_metrics": FileSpec(
        "arrival_validation_metrics",
        config.ARRIVAL_METRICS / "validation_metrics_arrival_hour.csv",
        "Arrival-hour validation metrics", "train_models_arrival_hour.py",
        required=("Model",), group="robustness",
    ),
    "arrival_horizon_metrics": FileSpec(
        "arrival_horizon_metrics",
        config.ARRIVAL_METRICS / "horizon_metrics_arrival_hour.csv",
        "Arrival-hour metrics by horizon", "train_models_arrival_hour.py",
        required=("Model", "Horizon"), group="robustness",
    ),
    "arrival_test_predictions": FileSpec(
        "arrival_test_predictions",
        config.ARRIVAL_PREDICTIONS / "test_predictions_arrival_hour.csv",
        "Arrival-hour test predictions", "train_models_arrival_hour.py",
        required=("model", "timestamp"),
        time_cols=("origin", "timestamp"), utc=True, group="robustness",
    ),

    # ---------------- Legacy, quarantined ----------------
    "legacy_sarima": FileSpec(
        "legacy_sarima", config.METRICS / "sarima_validation_metrics.csv",
        "Legacy SARIMA validation metrics (superseded)",
        "an abandoned SARIMA implementation", group="legacy",
    ),
}

# Directories rather than single files.
DIRECTORIES = {
    "peak_analysis": (config.PEAK_ANALYSIS, "Peak analysis outputs"),
    "figures": (config.FIGURES, "Generated figures"),
}


def spec(key: str) -> FileSpec:
    return SPECS[key]


def missing_columns(columns, required) -> list[str]:
    have = set(columns)
    return [c for c in required if c not in have]
