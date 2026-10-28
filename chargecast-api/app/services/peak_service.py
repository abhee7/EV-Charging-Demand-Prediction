"""Peak analysis: audited artefacts and exploratory recomputation."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.services import stats
from app.utils import columns as cols

SUPPLEMENTARY = [
    ("peak_model_values", "Peak values by model"),
    ("peak_error_split", "Error on peak against non-peak hours"),
    ("peak_top_hours", "Highest-demand hours"),
    ("peak_overall_summary", "Overall demand summary"),
    ("peak_hourly_profile", "Hourly demand profile"),
    ("peak_dow_profile", "Day-of-week profile"),
    ("peak_weekday_weekend", "Weekday and weekend profile"),
    ("peak_monthly_profile", "Monthly demand profile"),
]


def audited() -> dict:
    """model_peak_detection.csv, rendered as stored plus resolved fields."""
    art = al.load("peak_model_detection")
    if not art:
        return art.unavailable_payload()

    df = art.frame
    res = cols.resolve(df, cols.PEAK_FIELDS, numeric=cols.PEAK_NUMERIC)
    model_col = res.get("model") or cols.model_column(df)

    rows = []
    for _, row in df.iterrows():
        entry = {"model": str(row[model_col]) if model_col else ""}
        for field in ("precision", "recall", "f1", "true_positive",
                      "false_positive", "false_negative", "true_negative",
                      "threshold", "percentile"):
            col = res.get(field)
            value = (None if col is None or pd.isna(row[col])
                     else float(row[col]))
            entry[_camel(field)] = value
        if entry.get("truePositive") is not None:
            tp = entry["truePositive"]
            fn = entry.get("falseNegative")
            fp = entry.get("falsePositive")
            entry["observedPeakHours"] = (tp + fn) if fn is not None else None
            entry["forecastPeakHours"] = (tp + fp) if fp is not None else None
        rows.append(entry)
    rows.sort(key=lambda r: r["model"].lower())

    return {
        "available": True,
        "source": art.spec.relative,
        "columns": [str(c) for c in df.columns],
        "resolvedFields": {_camel(k): v for k, v in res.columns.items()},
        "absentFields": [_camel(f) for f in res.absent],
        "hasConfusionMatrix": res.has("true_positive", "false_positive",
                                      "false_negative", "true_negative"),
        "models": rows,
        "rows": al.frame_records(df),
        "note": config.AUDITED_NOTE,
        "provenance": "VERIFIED RESEARCH ARTIFACT",
        "caveat": config.PEAK_CAVEAT,
    }


def thresholds() -> dict:
    art = al.load("peak_thresholds")
    if not art:
        return art.unavailable_payload()
    df = art.frame
    res = cols.resolve(df, cols.THRESHOLD_FIELDS,
                       numeric=cols.THRESHOLD_NUMERIC)

    entries = []
    pct_col, thr_col = res.get("percentile"), res.get("threshold")
    if pct_col and thr_col:
        for _, row in df.iterrows():
            entries.append({
                "percentile": (None if pd.isna(row[pct_col])
                               else float(row[pct_col])),
                "threshold": (None if pd.isna(row[thr_col])
                              else float(row[thr_col])),
            })

    return {
        "available": True, "source": art.spec.relative,
        "columns": [str(c) for c in df.columns],
        "resolvedFields": {_camel(k): v for k, v in res.columns.items()},
        "entries": entries, "rows": al.frame_records(df),
        "unit": config.UNIT, "note": config.AUDITED_NOTE,
    }


def supplementary() -> list[dict]:
    out = []
    for key, label in SUPPLEMENTARY:
        art = al.load(key)
        if not art:
            continue
        out.append({"key": key, "label": label, "path": art.spec.relative,
                    "columns": [str(c) for c in art.frame.columns],
                    "rows": al.frame_records(art.frame, limit=200)})
    return out


def interactive(percentile: int, model: str | None = None) -> dict:
    """Recomputation from stored predictions. Exploratory."""
    frames, sources = [], []
    for key in ("test_predictions", "sarimax_test_predictions"):
        art = al.load(key)
        if art:
            frames.append(art.frame)
            sources.append(art.spec.relative)
    if not frames:
        return al.load("test_predictions").unavailable_payload()

    frame = pd.concat(frames, ignore_index=True)
    model_col = cols.model_column(frame)
    if model_col is None:
        return {"available": False, "reason": "No model column in predictions"}

    scores, threshold = stats.peak_scores(frame, model_col, int(percentile))
    if not scores:
        return {"available": False,
                "reason": "Stored predictions lack paired observed and "
                          "forecast values"}

    known = [s.model for s in scores]
    if model and model not in known:
        return {"available": False, "reason": f"Unknown model: {model}",
                "availableModels": known}

    rows = [{
        "model": s.model, "precision": s.precision, "recall": s.recall,
        "f1": s.f1, "truePositive": s.true_positive,
        "falsePositive": s.false_positive, "falseNegative": s.false_negative,
        "trueNegative": s.true_negative,
        "observedPeakHours": s.true_positive + s.false_negative,
        "forecastPeakHours": s.true_positive + s.false_positive,
    } for s in sorted(scores, key=lambda s: s.model.lower())]

    audited_pct = config.PEAK_PERCENTILE
    differs = int(percentile) != audited_pct
    return {
        "available": True,
        "percentile": int(percentile),
        "auditedPercentile": audited_pct,
        "differsFromAudited": differs,
        "thresholdNotice": (
            "Interactive threshold differs from audited research threshold."
            if differs else
            "Interactive threshold matches the audited research threshold."),
        "threshold": threshold, "unit": config.UNIT,
        "models": rows,
        "selected": next((r for r in rows if r["model"] == model), None),
        "availableModels": known,
        "sources": sources,
        "note": config.EXPLORATORY_NOTE,
        "provenance": "EXPLORATORY \u2014 NOT THE AUDITED RESULT",
        "caveat": config.PEAK_CAVEAT,
    }


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(p.title() for p in rest)
