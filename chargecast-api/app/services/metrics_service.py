"""Model metrics, horizon curves and Diebold-Mariano results."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.services import stats
from app.utils import columns as cols


def _combined(keys: list[str]) -> tuple[pd.DataFrame | None, list[dict], list[str]]:
    frames, missing, sources = [], [], []
    for key in keys:
        art = al.load(key)
        if art:
            frames.append(art.frame)
            sources.append(art.spec.relative)
        else:
            missing.append(art.unavailable_payload())
    if not frames:
        return None, missing, sources
    return pd.concat(frames, ignore_index=True), missing, sources


def _metric_rows(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    model_col = cols.model_column(df)
    resolved = cols.resolve_metrics(df, config.METRIC_ALIASES)
    rows = []
    for _, row in df.iterrows():
        entry = {"model": str(row[model_col]) if model_col else ""}
        for canon, column in resolved.items():
            value = row.get(column)
            entry[canon] = None if pd.isna(value) else float(value)
        rows.append(entry)
    # Alphabetical by model name. Never ordered by metric value by default.
    rows.sort(key=lambda r: r["model"].lower())
    return rows, list(resolved.keys())


def metrics(metric: str | None = None) -> dict:
    df, missing, sources = _combined(["test_metrics", "sarimax_test_metrics"])
    if df is None:
        return {"available": False, "reason": "Artifact not found",
                "path": al.SPECS["test_metrics"].relative,
                "missing": missing}

    rows, present = _metric_rows(df)
    payload = {
        "available": True,
        "models": rows,
        "metrics": [
            {"key": k, "label": config.METRIC_LABELS[k],
             "unit": config.METRIC_UNITS[k],
             "lowerIsBetter": config.METRIC_LOWER_IS_BETTER[k]}
            for k in config.METRIC_ORDER if k in present
        ],
        "defaultOrder": "model-name",
        "orderingNote": ("Models are listed alphabetically. Sorting by a "
                         "metric is a display convenience and is not a "
                         "scientific ranking."),
        "sources": sources,
        "missing": missing,
    }
    if metric:
        key = metric.strip().lower()
        if key not in present:
            payload["selectedMetric"] = None
            payload["selectionError"] = (
                f"Metric '{metric}' is not present in the stored artefacts.")
        else:
            payload["selectedMetric"] = key
    return payload


def validation() -> dict:
    df, missing, sources = _combined(
        ["validation_metrics", "sarimax_validation_metrics"])
    if df is None:
        return {"available": False, "reason": "Artifact not found",
                "path": al.SPECS["validation_metrics"].relative,
                "missing": missing}
    return {"available": True, "columns": [str(c) for c in df.columns],
            "rows": al.frame_records(df), "sources": sources,
            "missing": missing}


def horizon(metric: str = "mae") -> dict:
    df, missing, sources = _combined(
        ["horizon_metrics", "sarimax_horizon_metrics"])
    if df is None:
        return {"available": False, "reason": "Artifact not found",
                "path": al.SPECS["horizon_metrics"].relative,
                "missing": missing}

    model_col = cols.model_column(df)
    resolved = cols.resolve_metrics(df, config.METRIC_ALIASES)
    key = metric.strip().lower()
    if key not in resolved:
        return {"available": False,
                "reason": f"Metric '{metric}' not present by horizon",
                "path": al.SPECS["horizon_metrics"].relative,
                "availableMetrics": list(resolved.keys())}

    horizon_col = cols.find(df, ("Horizon", "horizon", "h"))
    series = []
    for model in sorted(df[model_col].astype(str).unique()):
        sub = df[df[model_col].astype(str) == model].sort_values(horizon_col)
        series.append({
            "model": model,
            "points": [{"horizon": int(h), "value": float(v)}
                       for h, v in zip(sub[horizon_col], sub[resolved[key]])
                       if pd.notna(v)],
        })
    return {
        "available": True, "metric": key,
        "label": config.METRIC_LABELS[key], "unit": config.METRIC_UNITS[key],
        "availableMetrics": [k for k in config.METRIC_ORDER if k in resolved],
        "series": series, "sources": sources, "missing": missing,
        "note": ("Error at longer horizons is not evidence that a model is "
                 "deficient: horizons differ in how much observed history is "
                 "available at the forecast origin."),
    }


# --------------------------------------------------------------------------
# Diebold-Mariano
# --------------------------------------------------------------------------
def dm_audited() -> dict:
    """The verified artefact, rendered as stored plus resolved fields."""
    art = al.load("dm_tests")
    if not art:
        return art.unavailable_payload()

    df = art.frame
    res = cols.resolve(df, cols.DM_FIELDS, numeric=cols.DM_NUMERIC)

    comparisons = []
    for _, row in df.iterrows():
        entry = {"raw": {str(k): (None if pd.isna(v) else
                                  (float(v) if isinstance(v, (int, float))
                                   else str(v)))
                         for k, v in row.items()}}
        for field in ("model_a", "model_b", "loss", "significant"):
            col = res.get(field)
            entry[_camel(field)] = (None if col is None or pd.isna(row[col])
                                    else str(row[col]))
        for field in ("statistic", "p_value", "observations", "hac_lag"):
            col = res.get(field)
            value = None if col is None or pd.isna(row[col]) else float(row[col])
            entry[_camel(field)] = value
        if entry.get("pValue") is not None:
            entry["significantAt5Pct"] = entry["pValue"] < 0.05
        comparisons.append(entry)

    return {
        "available": True,
        "source": art.spec.relative,
        "columns": [str(c) for c in df.columns],
        "resolvedFields": {_camel(k): v for k, v in res.columns.items()},
        "absentFields": [_camel(f) for f in res.absent],
        "comparisons": comparisons,
        "rows": al.frame_records(df),
        "note": config.AUDITED_NOTE,
        "provenance": "VERIFIED RESEARCH ARTIFACT",
    }


def dm_interactive(model_a: str, model_b: str, hac_lag: int) -> dict:
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
        return {"available": False, "reason": "No model column in predictions",
                "path": al.SPECS["test_predictions"].relative}

    known = sorted(frame[model_col].astype(str).unique())
    for name, value in (("model_a", model_a), ("model_b", model_b)):
        if value not in known:
            return {"available": False,
                    "reason": f"Unknown model for {name}: {value}",
                    "availableModels": known}
    if model_a == model_b:
        return {"available": False,
                "reason": "Model A and Model B must differ",
                "availableModels": known}

    result = stats.dm_from_predictions(frame, model_col, model_a, model_b,
                                       int(hac_lag))
    if result is None:
        return {"available": False,
                "reason": "Not enough aligned observations for a paired test",
                "availableModels": known}

    return {
        "available": True,
        "modelA": result.model_a, "modelB": result.model_b,
        "statistic": result.statistic, "pValue": result.p_value,
        "observations": result.observations, "hacLag": result.hac_lag,
        "loss": result.loss,
        "significantAt5Pct": result.significant_at_5pct,
        "availableModels": known,
        "sources": sources,
        "note": config.EXPLORATORY_NOTE,
        "provenance": "EXPLORATORY \u2014 NOT THE AUDITED RESULT",
    }


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(p.title() for p in rest)
