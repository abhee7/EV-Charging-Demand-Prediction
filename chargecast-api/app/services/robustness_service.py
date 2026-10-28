"""Robustness: the two target constructions, kept structurally symmetric."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.services import stats
from app.utils import columns as cols

TARGETS = {
    "primary": {
        "label": "Primary target",
        "construction": "Interval allocation",
        "series": "hourly_demand",
        "metrics": "test_metrics",
        "horizon": "horizon_metrics",
        "definition": (
            "Each session's energy is allocated uniformly across the hours "
            "from connectionTime to doneChargingTime. This approximates when "
            "energy was drawn and relies on doneChargingTime, which is only "
            "known once the session completes."),
    },
    "arrival": {
        "label": "Arrival-hour target",
        "construction": "Arrival-hour allocation",
        "series": "hourly_demand_arrival",
        "metrics": "arrival_test_metrics",
        "horizon": "arrival_horizon_metrics",
        "definition": (
            "Each session's entire delivered energy is assigned to the hour "
            "the vehicle connected. This is knowable at arrival time and "
            "attributes energy to arrival rather than to draw time."),
    },
}


def _summary_for(target: str) -> dict:
    spec = TARGETS[target]
    art = al.load(spec["series"])
    if not art:
        payload = art.unavailable_payload()
        payload.update({"target": target, "label": spec["label"]})
        return payload
    summ = stats.summarise(art.frame["demand_kWh"])
    summ.update({
        "available": True, "target": target, "label": spec["label"],
        "construction": spec["construction"], "definition": spec["definition"],
        "unit": config.UNIT, "source": art.spec.relative,
    })
    return summ


def summary() -> dict:
    return {
        "targets": [_summary_for(t) for t in TARGETS],
        "warning": config.CROSS_TARGET_WARNING,
        "question": ("Does the relative behaviour of the forecasting methods "
                     "change when the target construction changes?"),
        "limitation": config.TARGET_LIMITATION,
    }


def _metric_rows(df: pd.DataFrame) -> list[dict]:
    model_col = cols.model_column(df)
    resolved = cols.resolve_metrics(df, config.METRIC_ALIASES)
    rows = []
    for _, row in df.iterrows():
        entry = {"model": str(row[model_col]) if model_col else ""}
        for canon, column in resolved.items():
            value = row.get(column)
            entry[canon] = None if pd.isna(value) else float(value)
        rows.append(entry)
    rows.sort(key=lambda r: r["model"].lower())
    return rows


def metrics() -> dict:
    out = {"targets": [], "warning": config.CROSS_TARGET_WARNING}
    for target, spec in TARGETS.items():
        art = al.load(spec["metrics"])
        if not art:
            payload = art.unavailable_payload()
            payload.update({"target": target, "label": spec["label"]})
            out["targets"].append(payload)
            continue
        out["targets"].append({
            "available": True, "target": target, "label": spec["label"],
            "models": _metric_rows(art.frame),
            "source": art.spec.relative,
        })
    return out


def horizon(metric: str = "mae") -> dict:
    key = metric.strip().lower()
    out = {"metric": key, "targets": [],
           "warning": config.CROSS_TARGET_WARNING}
    for target, spec in TARGETS.items():
        art = al.load(spec["horizon"])
        if not art:
            payload = art.unavailable_payload()
            payload.update({"target": target, "label": spec["label"]})
            out["targets"].append(payload)
            continue
        df = art.frame
        resolved = cols.resolve_metrics(df, config.METRIC_ALIASES)
        if key not in resolved:
            out["targets"].append({
                "available": False, "target": target, "label": spec["label"],
                "reason": f"Metric '{metric}' not present by horizon",
                "availableMetrics": list(resolved.keys()),
                "path": art.spec.relative})
            continue
        model_col = cols.model_column(df)
        horizon_col = cols.find(df, ("Horizon", "horizon"))
        series = []
        for model in sorted(df[model_col].astype(str).unique()):
            sub = df[df[model_col].astype(str) == model].sort_values(
                horizon_col)
            series.append({"model": model, "points": [
                {"horizon": int(h), "value": float(v)}
                for h, v in zip(sub[horizon_col], sub[resolved[key]])
                if pd.notna(v)]})
        out["targets"].append({
            "available": True, "target": target, "label": spec["label"],
            "series": series, "source": art.spec.relative})
    return out
