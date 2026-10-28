"""Display formatting. Presentation only; stored values are never altered."""

from __future__ import annotations

import math

import pandas as pd

import config


def energy(value: float | None, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "\u2014"
    if abs(value) >= 10_000:
        return f"{value / 1000:,.1f} MWh"
    return f"{value:,.{decimals}f} kWh"


def metric(value, name: str) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "\u2014"
    if math.isnan(value):
        return "\u2014"
    unit = config.METRIC_META.get(name, {}).get("unit", "")
    if unit == "%":
        return f"{value:.2f}%"
    return f"{value:.4f}" if name in ("R2", "MASE") else f"{value:.4f}"


def number(value, decimals: int = 0) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "\u2014"
    if math.isnan(value):
        return "\u2014"
    return f"{value:,.{decimals}f}"


def day_range(series: pd.Series) -> str:
    if series is None or len(series) == 0:
        return "\u2014"
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi):
        return "\u2014"
    return f"{lo:%d %b %Y} \u2013 {hi:%d %b %Y}"


DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
