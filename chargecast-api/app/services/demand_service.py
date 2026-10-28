"""Demand series analysis, derived from the stored hourly demand artefact."""

from __future__ import annotations

import pandas as pd

from app import config
from app.services import artifact_loader as al
from app.services import stats

DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _series(key: str = "hourly_demand"):
    art = al.load(key)
    if not art:
        return None, art
    return art.frame.sort_values("timestamp"), art


def summary(key: str = "hourly_demand") -> dict:
    df, art = _series(key)
    if df is None:
        return art.unavailable_payload()
    out = stats.summarise(df["demand_kWh"])
    out.update({
        "available": True,
        "unit": config.UNIT,
        "coverageStart": df["timestamp"].min().isoformat(),
        "coverageEnd": df["timestamp"].max().isoformat(),
        "source": art.spec.relative,
    })
    return out


def hourly(downsample: int = 1, limit: int | None = None) -> dict:
    """The demand ribbon series. Downsampling keeps payloads small."""
    df, art = _series()
    if df is None:
        return art.unavailable_payload()

    frame = df[["timestamp", "demand_kWh"]]
    step = max(1, int(downsample))
    if step > 1:
        frame = frame.iloc[::step]
    if limit:
        frame = frame.tail(int(limit))

    summ = stats.summarise(df["demand_kWh"])
    return {
        "available": True,
        "unit": config.UNIT,
        "downsample": step,
        "points": [
            {"t": ts.isoformat(), "v": None if pd.isna(v) else float(v)}
            for ts, v in zip(frame["timestamp"], frame["demand_kWh"])
        ],
        "peakThreshold": summ.get("p90"),
        "maximum": summ.get("maximum"),
        "totalPoints": int(len(df)),
        "source": art.spec.relative,
    }


def profile() -> dict:
    """Mean demand by hour of day, with an interquartile band."""
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    if "hour" not in df.columns:
        return {"available": False, "reason": "No hour column",
                "path": art.spec.relative}

    grouped = df.groupby("hour")["demand_kWh"]
    mean, q1, q3 = grouped.mean(), grouped.quantile(.25), grouped.quantile(.75)
    return {
        "available": True, "unit": config.UNIT,
        "points": [{"hour": int(h), "mean": float(mean.loc[h]),
                    "q1": float(q1.loc[h]), "q3": float(q3.loc[h])}
                   for h in mean.index],
        "source": art.spec.relative,
    }


def weekday() -> dict:
    """Weekday against weekend, by hour, plus segment means."""
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    if "hour" not in df.columns or "is_weekend" not in df.columns:
        return {"available": False, "reason": "No hour/is_weekend columns",
                "path": art.spec.relative}

    pivot = df.groupby(["is_weekend", "hour"])["demand_kWh"].mean().unstack(0)
    weekday_col = next((c for c in pivot.columns if not bool(c)), None)
    weekend_col = next((c for c in pivot.columns if bool(c)), None)
    segment = df.groupby("is_weekend")["demand_kWh"].mean()

    return {
        "available": True, "unit": config.UNIT,
        "points": [{
            "hour": int(h),
            "weekday": (float(pivot.loc[h, weekday_col])
                        if weekday_col is not None else None),
            "weekend": (float(pivot.loc[h, weekend_col])
                        if weekend_col is not None else None),
        } for h in pivot.index],
        "weekdayMean": float(segment.get(0)) if 0 in segment.index else None,
        "weekendMean": float(segment.get(1)) if 1 in segment.index else None,
        "source": art.spec.relative,
    }


def monthly() -> dict:
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    if "month" not in df.columns:
        return {"available": False, "reason": "No month column",
                "path": art.spec.relative}
    total = df.groupby("month")["demand_kWh"].sum()
    mean = df.groupby("month")["demand_kWh"].mean()
    return {
        "available": True,
        "points": [{"month": int(m), "label": MONTH_SHORT[int(m) - 1],
                    "total": float(total.loc[m]), "mean": float(mean.loc[m])}
                   for m in total.index],
        "note": ("Aggregated across the whole study period. With under a year "
                 "of coverage, month totals partly reflect uneven coverage "
                 "rather than an annual cycle."),
        "source": art.spec.relative,
    }


def heatmap() -> dict:
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    if "hour" not in df.columns or "day_of_week" not in df.columns:
        return {"available": False, "reason": "No hour/day_of_week columns",
                "path": art.spec.relative}

    pivot = (df.pivot_table(index="day_of_week", columns="hour",
                            values="demand_kWh", aggfunc="mean")
             .reindex(range(7)))
    cells = []
    for day in pivot.index:
        for hour in pivot.columns:
            value = pivot.loc[day, hour]
            cells.append({"day": int(day), "hour": int(hour),
                          "value": None if pd.isna(value) else float(value)})
    values = [c["value"] for c in cells if c["value"] is not None]
    return {
        "available": True, "unit": config.UNIT,
        "days": DAY_SHORT, "cells": cells,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "source": art.spec.relative,
    }


def distribution(bins: int = 48) -> dict:
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    import numpy as np

    values = df["demand_kWh"].astype(float).dropna()
    counts, edges = np.histogram(values, bins=int(bins))
    summ = stats.summarise(values)
    return {
        "available": True, "unit": config.UNIT,
        "bins": [{"start": float(edges[i]), "end": float(edges[i + 1]),
                  "mid": float((edges[i] + edges[i + 1]) / 2),
                  "count": int(counts[i])} for i in range(len(counts))],
        "percentiles": {"p75": summ["p75"], "p90": summ["p90"],
                        "p95": summ["p95"], "p99": summ["p99"]},
        "source": art.spec.relative,
    }


def autocorrelation(max_lag: int = 336, lag: int | None = None) -> dict:
    df, art = _series()
    if df is None:
        return art.unavailable_payload()

    series = df["demand_kWh"]
    values = stats.acf(series, int(max_lag))
    n = int(series.dropna().size)
    selected = None
    if lag:
        value = stats.acf_at(series, int(lag))
        if value is not None:
            selected = {"lag": int(lag), "value": value,
                        "meaning": _lag_meaning(int(lag))}

    highlights = []
    for key in (1, 24, 168):
        value = stats.acf_at(series, key)
        if value is not None:
            highlights.append({"lag": key, "value": value,
                               "meaning": _lag_meaning(key)})

    return {
        "available": True,
        "points": [{"lag": i + 1, "value": v} for i, v in enumerate(values)],
        "confidence": 1.96 / (n ** 0.5) if n else None,
        "observations": n,
        "highlights": highlights,
        "selected": selected,
        "source": art.spec.relative,
    }


def _lag_meaning(lag: int) -> str:
    if lag == 1:
        return "1 hour is the immediately preceding observation."
    if lag % 168 == 0:
        weeks = lag // 168
        return (f"{lag} hours corresponds approximately to {weeks} "
                f"week{'s' if weeks > 1 else ''}.")
    if lag % 24 == 0:
        days = lag // 24
        return f"{lag} hours corresponds to {days} day{'s' if days > 1 else ''}."
    return f"{lag} hours is {lag / 24:.1f} days."


def scenario(pct: float) -> dict:
    """Arithmetic scaling of the historical summary. Not a forecast."""
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    base = stats.summarise(df["demand_kWh"])
    factor = 1.0 + float(pct) / 100.0
    scaled = {k: (v * factor if isinstance(v, (int, float)) and k in
                  ("totalKwh", "mean", "median", "maximum", "p75", "p90",
                   "p95", "p99") else v)
              for k, v in base.items()}
    scaled["peakOverAverage"] = (scaled["maximum"] / scaled["mean"]
                                 if scaled.get("mean") else None)
    return {
        "available": True, "unit": config.UNIT, "changePercent": float(pct),
        "baseline": base, "scenario": scaled,
        "note": config.SCENARIO_CAVEAT, "source": art.spec.relative,
    }


def capacity(capacity_kw: float) -> dict:
    df, art = _series()
    if df is None:
        return art.unavailable_payload()
    s = df["demand_kWh"].astype(float).dropna()
    above = int((s > capacity_kw).sum())
    peak = float(s.max())
    return {
        "available": True, "unit": config.UNIT,
        "capacityKw": float(capacity_kw),
        "historicalPeak": peak,
        "peakOverCapacity": peak / capacity_kw if capacity_kw else None,
        "hoursAbove": above,
        "shareAbove": float(above / s.size * 100) if s.size else 0.0,
        "observations": int(s.size),
        "note": config.CAPACITY_CAVEAT,
        "source": art.spec.relative,
    }
