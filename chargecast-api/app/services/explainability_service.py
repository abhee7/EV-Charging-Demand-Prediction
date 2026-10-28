"""Explainability artefacts. No SHAP is recomputed here."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.utils import columns as cols

FEATURE_GLOSSARY = {
    "lag_1": "Demand one hour before the forecast origin. Recent demand "
             "history is the dominant contribution in this dataset.",
    "lag_2": "Demand two hours before the origin. Captures the direction a "
             "short run is moving in.",
    "lag_24": "Same hour on the previous day, encoding the daily cycle.",
    "lag_48": "Same hour two days earlier, separating a persistent daily "
              "level from a one-day anomaly.",
    "lag_168": "Same hour on the previous week, encoding the weekly cycle.",
    "lag_336": "Same hour two weeks earlier, supporting the weekly pattern "
               "when the previous week was unusual.",
    "rolling_mean_24": "Average demand over the 24 hours ending at the "
                       "origin: a recent level estimate.",
    "rolling_std_24": "Variability over the same 24 hours.",
    "rolling_mean_168": "Average over the previous week.",
    "rolling_std_168": "Variability over the previous week.",
    "hour": "Hour of day in America/Los_Angeles, driving the daily shape.",
    "day_of_week": "Day of week, separating weekday from weekend use.",
    "day_of_month": "Day within the month.",
    "month": "Calendar month.",
    "week_of_year": "Week within the year.",
    "is_weekend": "Weekend indicator.",
    "is_business_hour": "Business-hours indicator.",
}

MODEL_KEYS = {
    "random-forest": {"shap": "rf_shap_importance",
                      "importance": "rf_importance",
                      "values": "rf_shap_values",
                      "label": "Random Forest"},
    "xgboost": {"shap": "xgb_shap_importance",
                "importance": "xgb_importance",
                "values": "xgb_shap_values",
                "label": "XGBoost"},
}


def _importance_payload(key: str) -> dict:
    art = al.load(key)
    if not art:
        return art.unavailable_payload()
    df = art.frame
    feature_col, value_col = cols.feature_value_columns(df)
    if feature_col is None or value_col is None:
        return {"available": False,
                "reason": "Could not identify feature and value columns",
                "path": art.spec.relative,
                "detectedColumns": [str(c) for c in df.columns]}

    frame = df[[feature_col, value_col]].dropna()
    frame = frame.sort_values(value_col, ascending=False)
    total = float(frame[value_col].sum()) or 1.0
    return {
        "available": True, "source": art.spec.relative,
        "featureColumn": str(feature_col), "valueColumn": str(value_col),
        "features": [{"feature": str(f), "value": float(v),
                      "share": float(v) / total,
                      "description": FEATURE_GLOSSARY.get(str(f))}
                     for f, v in zip(frame[feature_col], frame[value_col])],
        "note": config.NOT_CAUSAL,
    }


def model_view(model: str, source: str = "shap") -> dict:
    spec = MODEL_KEYS.get(model)
    if spec is None:
        return {"available": False, "reason": f"Unknown model: {model}",
                "availableModels": sorted(MODEL_KEYS.keys())}
    key = spec["shap"] if source == "shap" else spec["importance"]
    payload = _importance_payload(key)
    payload.setdefault("model", spec["label"])
    payload["source_kind"] = source
    return payload


def combined_shap() -> dict:
    art = al.load("shap_combined")
    if not art:
        return art.unavailable_payload()
    df = art.frame
    model_col = cols.model_column(df)
    feature_col, value_col = cols.feature_value_columns(df)
    if feature_col is None or value_col is None:
        return {"available": False,
                "reason": "Could not identify feature and value columns",
                "path": art.spec.relative,
                "detectedColumns": [str(c) for c in df.columns]}

    groups = []
    if model_col is not None:
        for name in sorted(df[model_col].astype(str).unique()):
            sub = df[df[model_col].astype(str) == name]
            sub = sub[[feature_col, value_col]].dropna().sort_values(
                value_col, ascending=False)
            groups.append({
                "model": name,
                "features": [{"feature": str(f), "value": float(v),
                              "description": FEATURE_GLOSSARY.get(str(f))}
                             for f, v in zip(sub[feature_col], sub[value_col])],
            })
    else:
        sub = df[[feature_col, value_col]].dropna().sort_values(
            value_col, ascending=False)
        groups.append({
            "model": "Combined",
            "features": [{"feature": str(f), "value": float(v),
                          "description": FEATURE_GLOSSARY.get(str(f))}
                         for f, v in zip(sub[feature_col], sub[value_col])],
        })

    return {"available": True, "source": art.spec.relative,
            "featureColumn": str(feature_col),
            "valueColumn": str(value_col),
            "groups": groups, "note": config.NOT_CAUSAL,
            "interpretation": (
                "Recent demand history dominates the attribution in this "
                "dataset, with hour-of-day and the weekly lags contributing "
                "further. This describes model behaviour.")}
