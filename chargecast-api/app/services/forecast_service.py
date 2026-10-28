"""Forecast replay from stored predictions. No inference is performed."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.services import stats
from app.utils import columns as cols

SETS = {
    "primary": "test_predictions",
    "sarimax": "sarimax_test_predictions",
    "arrival": "arrival_test_predictions",
}
SET_LABELS = {"primary": "Primary target",
              "sarimax": "SARIMAX + Fourier",
              "arrival": "Arrival-hour target"}


def _frame(prediction_set: str):
    key = SETS.get(prediction_set, SETS["primary"])
    art = al.load(key)
    if not art:
        return None, art
    return art.frame, art


def available_sets() -> list[dict]:
    return [{"key": k, "label": SET_LABELS[k],
             "available": bool(al.load(v)), "path": al.SPECS[v].relative}
            for k, v in SETS.items()]


def models(prediction_set: str = "primary") -> dict:
    df, art = _frame(prediction_set)
    if df is None:
        return art.unavailable_payload()
    model_col = cols.model_column(df)
    if model_col is None:
        return {"available": False, "reason": "No model column",
                "path": art.spec.relative}
    return {"available": True, "predictionSet": prediction_set,
            "models": sorted(df[model_col].astype(str).unique()),
            "sets": available_sets(), "source": art.spec.relative}


def _window_column(df: pd.DataFrame) -> str | None:
    for candidate in ("forecast_window", "window"):
        if candidate in df.columns:
            return candidate
    return None


def windows(prediction_set: str = "primary",
            model: str | None = None) -> dict:
    df, art = _frame(prediction_set)
    if df is None:
        return art.unavailable_payload()

    model_col = cols.model_column(df)
    if model and model_col is not None:
        known = set(df[model_col].astype(str).unique())
        if model not in known:
            return {"available": False, "reason": f"Unknown model: {model}",
                    "availableModels": sorted(known)}
        df = df[df[model_col].astype(str) == model]

    win_col = _window_column(df)
    has_origin = "origin" in df.columns
    out = []

    if win_col is not None:
        for value in sorted(df[win_col].dropna().unique()):
            sub = df[df[win_col] == value]
            origin = (sub["origin"].iloc[0] if has_origin and len(sub)
                      else None)
            out.append({
                "id": int(value),
                "origin": (origin.isoformat()
                           if origin is not None and pd.notna(origin)
                           else None),
                "label": f"Window {int(value)}",
                "horizons": int(sub["horizon"].nunique())
                if "horizon" in sub.columns else None,
            })
    elif has_origin:
        for i, value in enumerate(sorted(df["origin"].dropna().unique()), 1):
            out.append({"id": i, "origin": pd.Timestamp(value).isoformat(),
                        "label": pd.Timestamp(value).strftime("%d %b %Y %H:%M"),
                        "horizons": None})

    return {"available": True, "predictionSet": prediction_set,
            "model": model, "windows": out, "count": len(out),
            "source": art.spec.relative}


def window(window_id: int, model: str, prediction_set: str = "primary",
           horizon: int | None = None) -> dict:
    df, art = _frame(prediction_set)
    if df is None:
        return art.unavailable_payload()

    model_col = cols.model_column(df)
    if model_col is None:
        return {"available": False, "reason": "No model column",
                "path": art.spec.relative}
    known = sorted(df[model_col].astype(str).unique())
    if model not in known:
        return {"available": False, "reason": f"Unknown model: {model}",
                "availableModels": known}

    win_col = _window_column(df)
    if win_col is not None:
        sub = df[(df[win_col] == window_id)
                 & (df[model_col].astype(str) == model)]
    elif "origin" in df.columns:
        origins = sorted(df["origin"].dropna().unique())
        if not 1 <= window_id <= len(origins):
            return {"available": False,
                    "reason": f"Window {window_id} is out of range",
                    "windowCount": len(origins)}
        sub = df[(df["origin"] == origins[window_id - 1])
                 & (df[model_col].astype(str) == model)]
    else:
        return {"available": False, "reason": "No window or origin column",
                "path": art.spec.relative}

    if sub.empty:
        return {"available": False,
                "reason": f"No stored forecast for {model} in window "
                          f"{window_id}"}

    sub = (sub.sort_values("horizon") if "horizon" in sub.columns
           else sub.sort_values("timestamp"))
    if horizon:
        sub = sub[sub["horizon"] <= int(horizon)]

    local_hours = []
    if "timestamp" in sub.columns:
        try:
            local_hours = (sub["timestamp"].dt.tz_convert(config.TZ_LOCAL)
                           .dt.hour.tolist())
        except (TypeError, AttributeError):
            local_hours = []

    points = []
    for i, (_, row) in enumerate(sub.iterrows()):
        actual = row.get("actual")
        pred = row.get("prediction")
        points.append({
            "horizon": int(row["horizon"]) if "horizon" in sub.columns
            else i + 1,
            "timestamp": (row["timestamp"].isoformat()
                          if "timestamp" in sub.columns
                          and pd.notna(row["timestamp"]) else None),
            "localHour": local_hours[i] if i < len(local_hours) else None,
            "actual": None if pd.isna(actual) else float(actual),
            "prediction": None if pd.isna(pred) else float(pred),
            "absoluteError": (None if pd.isna(actual) or pd.isna(pred)
                              else abs(float(pred) - float(actual))),
        })

    origin = sub["origin"].iloc[0] if "origin" in sub.columns else None
    return {
        "available": True,
        "predictionSet": prediction_set,
        "windowId": int(window_id),
        "model": model,
        "origin": (origin.isoformat() if origin is not None
                   and pd.notna(origin) else None),
        "unit": config.UNIT,
        "points": points,
        "stats": stats.window_stats(sub["actual"], sub["prediction"]),
        "note": ("Historical test-period forecast replay. These are stored "
                 "predictions read back from the research outputs, not a "
                 "live prediction."),
        "source": art.spec.relative,
    }
