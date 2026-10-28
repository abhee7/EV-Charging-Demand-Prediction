"""Centralised artefact loading.

Every CSV read in this service passes through here. Route modules never call
pd.read_csv directly, so path resolution, caching and read-only guarantees
live in one place.

Caching is keyed on path + mtime + size, so rerunning a research script is
picked up without restarting the API, and repeated requests do not reparse.

This module opens files for reading only. Nothing in the API writes to data/
or results/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app import config


@dataclass(frozen=True)
class ArtifactSpec:
    key: str
    relative: str
    label: str
    group: str
    produced_by: str
    # Required columns are declared only where this service has verified the
    # schema. Audited artefacts declare none and resolve columns at runtime.
    required: tuple[str, ...] = ()
    time_cols: tuple[str, ...] = ()
    utc: bool = True
    optional: bool = False

    @property
    def path(self) -> Path:
        return config.repo_root() / self.relative


HOURLY_REQUIRED = ("timestamp", "demand_kWh")
PRED_REQUIRED = ("model", "timestamp", "actual", "prediction")

SPECS: dict[str, ArtifactSpec] = {
    # ---------------- Data ----------------
    "hourly_demand": ArtifactSpec(
        "hourly_demand", "data/processed/hourly_demand.csv",
        "Hourly demand (interval allocation)", "data",
        "prepare_hourly_demand.py", HOURLY_REQUIRED, ("timestamp",), False),
    "model_data": ArtifactSpec(
        "model_data", "data/processed/model_data.csv",
        "Model feature table", "data", "prepare_model_data.py",
        HOURLY_REQUIRED, ("timestamp",), False, optional=True),
    "hourly_demand_arrival": ArtifactSpec(
        "hourly_demand_arrival",
        "data/processed/hourly_demand_arrival_hour.csv",
        "Hourly demand (arrival-hour allocation)", "robustness",
        "prepare_arrival_hour_demand.py", HOURLY_REQUIRED, ("timestamp",),
        False),
    "model_data_arrival": ArtifactSpec(
        "model_data_arrival", "data/processed/model_data_arrival_hour.csv",
        "Model feature table (arrival-hour)", "robustness",
        "prepare_arrival_model_data.py", HOURLY_REQUIRED, ("timestamp",),
        False, optional=True),

    # ---------------- Primary metrics ----------------
    "test_metrics": ArtifactSpec(
        "test_metrics", "results/metrics/test_metrics_corrected.csv",
        "Primary test metrics", "primary", "train_models.py", ("Model",)),
    "validation_metrics": ArtifactSpec(
        "validation_metrics",
        "results/metrics/validation_metrics_corrected.csv",
        "Primary validation metrics", "primary", "train_models.py",
        ("Model",), optional=True),
    "horizon_metrics": ArtifactSpec(
        "horizon_metrics", "results/metrics/horizon_metrics.csv",
        "Primary metrics by horizon", "primary", "train_models.py",
        ("Model", "Horizon")),
    "test_predictions": ArtifactSpec(
        "test_predictions",
        "results/predictions/test_predictions_corrected.csv",
        "Primary test predictions", "primary", "train_models.py",
        PRED_REQUIRED, ("origin", "timestamp"), True),

    # ---------------- SARIMAX + Fourier ----------------
    "sarimax_test_metrics": ArtifactSpec(
        "sarimax_test_metrics",
        "results/metrics/sarimax_fourier_test_metrics.csv",
        "SARIMAX + Fourier test metrics", "sarimax", "train_sarima.py",
        ("Model",)),
    "sarimax_validation_metrics": ArtifactSpec(
        "sarimax_validation_metrics",
        "results/metrics/sarimax_fourier_validation_metrics.csv",
        "SARIMAX + Fourier validation metrics", "sarimax", "train_sarima.py",
        ("Model",), optional=True),
    "sarimax_horizon_metrics": ArtifactSpec(
        "sarimax_horizon_metrics",
        "results/metrics/sarimax_fourier_horizon_metrics.csv",
        "SARIMAX + Fourier metrics by horizon", "sarimax", "train_sarima.py",
        ("Model", "Horizon"), optional=True),
    "sarimax_test_predictions": ArtifactSpec(
        "sarimax_test_predictions",
        "results/predictions/sarimax_fourier_test_predictions.csv",
        "SARIMAX + Fourier test predictions", "sarimax", "train_sarima.py",
        (), ("origin", "timestamp"), True, optional=True),
    "sarimax_validation_predictions": ArtifactSpec(
        "sarimax_validation_predictions",
        "results/predictions/sarimax_fourier_validation_predictions.csv",
        "SARIMAX + Fourier validation predictions", "sarimax",
        "train_sarima.py", (), ("origin", "timestamp"), True, optional=True),

    # ---------------- Audited statistical testing ----------------
    "dm_tests": ArtifactSpec(
        "dm_tests", "results/metrics/diebold_mariano_tests.csv",
        "Audited Diebold-Mariano tests", "audited",
        "the statistical testing step"),

    # ---------------- Audited peak analysis ----------------
    "peak_model_detection": ArtifactSpec(
        "peak_model_detection",
        "results/peak_analysis/model_peak_detection.csv",
        "Audited peak detection by model", "audited",
        "the peak analysis step"),
    "peak_thresholds": ArtifactSpec(
        "peak_thresholds",
        "results/peak_analysis/high_demand_thresholds.csv",
        "Audited high-demand thresholds", "audited",
        "the peak analysis step"),
    "peak_model_values": ArtifactSpec(
        "peak_model_values", "results/peak_analysis/model_peak_values.csv",
        "Audited peak values by model", "audited", "the peak analysis step",
        optional=True),
    "peak_error_split": ArtifactSpec(
        "peak_error_split",
        "results/peak_analysis/model_peak_vs_nonpeak_error.csv",
        "Audited peak vs non-peak error", "audited",
        "the peak analysis step", optional=True),
    "peak_top_hours": ArtifactSpec(
        "peak_top_hours", "results/peak_analysis/top_10_peak_hours.csv",
        "Audited highest-demand hours", "audited", "the peak analysis step",
        optional=True),
    "peak_overall_summary": ArtifactSpec(
        "peak_overall_summary",
        "results/peak_analysis/overall_demand_summary.csv",
        "Audited overall demand summary", "audited",
        "the peak analysis step", optional=True),
    "peak_hourly_profile": ArtifactSpec(
        "peak_hourly_profile",
        "results/peak_analysis/hourly_demand_profile.csv",
        "Audited hourly demand profile", "audited",
        "the peak analysis step", optional=True),
    "peak_dow_profile": ArtifactSpec(
        "peak_dow_profile", "results/peak_analysis/day_of_week_profile.csv",
        "Audited day-of-week profile", "audited", "the peak analysis step",
        optional=True),
    "peak_weekday_weekend": ArtifactSpec(
        "peak_weekday_weekend",
        "results/peak_analysis/weekday_weekend_profile.csv",
        "Audited weekday and weekend profile", "audited",
        "the peak analysis step", optional=True),
    "peak_monthly_profile": ArtifactSpec(
        "peak_monthly_profile",
        "results/peak_analysis/monthly_demand_profile.csv",
        "Audited monthly demand profile", "audited",
        "the peak analysis step", optional=True),
    "peak_all_predictions": ArtifactSpec(
        "peak_all_predictions",
        "results/peak_analysis/all_test_predictions_for_analysis.csv",
        "Audited prediction set used for peak analysis", "audited",
        "the peak analysis step", (), ("origin", "timestamp"), True,
        optional=True),

    # ---------------- Explainability ----------------
    "shap_combined": ArtifactSpec(
        "shap_combined",
        "results/explainability/combined_shap_importance.csv",
        "Combined SHAP importance", "explain", "the explainability step",
        optional=True),
    "rf_importance": ArtifactSpec(
        "rf_importance",
        "results/explainability/random_forest_feature_importance.csv",
        "Random Forest feature importance", "explain",
        "the explainability step", optional=True),
    "xgb_importance": ArtifactSpec(
        "xgb_importance",
        "results/explainability/xgboost_feature_importance.csv",
        "XGBoost feature importance", "explain", "the explainability step",
        optional=True),
    "rf_shap_importance": ArtifactSpec(
        "rf_shap_importance",
        "results/explainability/random_forest_shap_importance.csv",
        "Random Forest SHAP importance", "explain",
        "the explainability step", optional=True),
    "xgb_shap_importance": ArtifactSpec(
        "xgb_shap_importance",
        "results/explainability/xgboost_shap_importance.csv",
        "XGBoost SHAP importance", "explain", "the explainability step",
        optional=True),
    "rf_shap_values": ArtifactSpec(
        "rf_shap_values",
        "results/explainability/random_forest_shap_values.csv",
        "Random Forest SHAP values", "explain", "the explainability step",
        optional=True),
    "xgb_shap_values": ArtifactSpec(
        "xgb_shap_values",
        "results/explainability/xgboost_shap_values.csv",
        "XGBoost SHAP values", "explain", "the explainability step",
        optional=True),

    # ---------------- Robustness ----------------
    "arrival_test_metrics": ArtifactSpec(
        "arrival_test_metrics",
        "results/arrival_hour/metrics/test_metrics_arrival_hour.csv",
        "Arrival-hour test metrics", "robustness",
        "train_models_arrival_hour.py", ("Model",)),
    "arrival_validation_metrics": ArtifactSpec(
        "arrival_validation_metrics",
        "results/arrival_hour/metrics/validation_metrics_arrival_hour.csv",
        "Arrival-hour validation metrics", "robustness",
        "train_models_arrival_hour.py", ("Model",), optional=True),
    "arrival_horizon_metrics": ArtifactSpec(
        "arrival_horizon_metrics",
        "results/arrival_hour/metrics/horizon_metrics_arrival_hour.csv",
        "Arrival-hour metrics by horizon", "robustness",
        "train_models_arrival_hour.py", ("Model", "Horizon"), optional=True),
    "arrival_test_predictions": ArtifactSpec(
        "arrival_test_predictions",
        "results/arrival_hour/predictions/test_predictions_arrival_hour.csv",
        "Arrival-hour test predictions", "robustness",
        "train_models_arrival_hour.py", (), ("origin", "timestamp"), True,
        optional=True),

    # ---------------- Legacy, quarantined ----------------
    "legacy_sarima": ArtifactSpec(
        "legacy_sarima", "results/metrics/sarima_validation_metrics.csv",
        "Legacy SARIMA validation metrics", "legacy",
        "an abandoned SARIMA implementation", optional=True),
}

DIRECTORIES = {
    "figures": ("results/figures", "Generated figures", "*.png"),
    "peak_analysis": ("results/peak_analysis", "Peak analysis outputs",
                      "*.csv"),
}


@dataclass
class Artifact:
    """The result of a load. Never raises; always describes what happened."""
    available: bool
    spec: ArtifactSpec
    frame: pd.DataFrame | None = None
    reason: str = ""
    detail: str = ""
    detected_columns: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.available

    def unavailable_payload(self) -> dict:
        return {
            "available": False,
            "reason": self.reason or "Artifact not found",
            "path": self.spec.relative,
            "label": self.spec.label,
            "producedBy": self.spec.produced_by,
            "detail": self.detail,
            "expectedColumns": list(self.spec.required),
            "detectedColumns": self.detected_columns,
            "missingColumns": self.missing_columns,
        }


def _stamp(path: Path) -> tuple[float, int]:
    try:
        s = path.stat()
        return (s.st_mtime, s.st_size)
    except OSError:
        return (0.0, -1)


@lru_cache(maxsize=128)
def _read(path_str: str, stamp: tuple[float, int]) -> pd.DataFrame:
    # `stamp` is unused in the body by design: it invalidates the cache when
    # the file changes on disk.
    return pd.read_csv(path_str)


def _parse_times(df: pd.DataFrame, spec: ArtifactSpec) -> pd.DataFrame:
    """Parse UTC-first.

    Local files carry offsets that shift across DST. Parsing them directly
    makes pandas fall back to an object dtype, which breaks every downstream
    .dt accessor, so they are parsed as UTC and converted afterwards.
    """
    for col in spec.time_cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], utc=True, errors="coerce")
        if not spec.utc:
            parsed = parsed.dt.tz_convert(config.TZ_LOCAL)
        df[col] = parsed
    return df


def load(key: str) -> Artifact:
    spec = SPECS[key]
    path = spec.path

    if not path.exists():
        return Artifact(False, spec, reason="Artifact not found",
                        detail=f"Expected at {spec.relative}")

    try:
        df = _read(str(path), _stamp(path)).copy()
    except Exception as exc:  # noqa: BLE001
        return Artifact(False, spec, reason="Artifact could not be read",
                        detail=str(exc))

    detected = [str(c) for c in df.columns]
    missing = [c for c in spec.required if c not in df.columns]
    if missing:
        return Artifact(False, spec, reason="Artifact schema mismatch",
                        detail=f"Missing: {', '.join(missing)}",
                        detected_columns=detected, missing_columns=missing)
    if df.empty:
        return Artifact(False, spec, reason="Artifact is empty",
                        detail="The file has headers but no rows.",
                        detected_columns=detected)

    return Artifact(True, spec, frame=_parse_times(df, spec),
                    detected_columns=detected)


def list_directory(key: str) -> list[Path]:
    relative, _, pattern = DIRECTORIES[key]
    base = config.repo_root() / relative
    if not base.exists():
        return []
    return sorted(base.glob(pattern))


def frame_records(df: pd.DataFrame, limit: int | None = None) -> list[dict]:
    """JSON-safe records. NaN becomes null; timestamps become ISO strings."""
    out = df.head(limit) if limit else df
    out = out.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].apply(
                lambda v: None if pd.isna(v) else v.isoformat())
    return out.replace({float("nan"): None}).where(pd.notna(out), None) \
        .to_dict(orient="records")


def clear_cache() -> None:
    _read.cache_clear()
