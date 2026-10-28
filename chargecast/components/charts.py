"""Themed chart builders.

Every figure returned here has the ChargeCast template applied. Charts read
stored values only; nothing is smoothed, interpolated or extrapolated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import config
from core import loaders
from theme import plotly_theme as theme


def demand_ribbon(ts: pd.Series, values: pd.Series,
                  title: str = "", height: int = 300) -> go.Figure:
    """The signature chart: observed demand as a filled cyan ribbon."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts, y=values,
        mode="lines", name="Observed demand",
        line=dict(color=config.CYAN, width=1.4),
        fill="tozeroy",
        fillcolor="rgba(0,224,198,0.13)",
        hovertemplate="%{x|%d %b %Y %H:%M}<br>%{y:.2f} kWh<extra></extra>",
    ))
    fig.update_layout(title=title, showlegend=False)
    fig.update_yaxes(title_text="kWh per hour")
    return theme.apply(fig, height=height)


def actual_vs_predicted(df: pd.DataFrame, time_col: str = "timestamp",
                        actual_col: str = "actual",
                        pred_col: str = "prediction",
                        title: str = "", height: int = 340) -> go.Figure:
    """Observed vs forecast over time for a single model."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[time_col], y=df[actual_col],
        mode="lines", name="Observed",
        line=dict(color=config.CYAN, width=1.6),
        hovertemplate="%{y:.2f} kWh<extra>Observed</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df[time_col], y=df[pred_col],
        mode="lines", name="Forecast",
        line=dict(color=config.AMBER, width=1.6, dash="dot"),
        hovertemplate="%{y:.2f} kWh<extra>Forecast</extra>",
    ))
    fig.update_layout(title=title)
    fig.update_yaxes(title_text="kWh per hour")
    return theme.apply(fig, height=height)


def forecast_window(df: pd.DataFrame, title: str = "",
                    height: int = 380) -> go.Figure:
    """A single 24-hour window: bars for observed, line for forecast."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["horizon"], y=df["actual"],
        name="Observed",
        marker=dict(color="rgba(0,224,198,0.28)",
                    line=dict(color=config.CYAN, width=1)),
        hovertemplate="h+%{x}<br>%{y:.2f} kWh<extra>Observed</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["horizon"], y=df["prediction"],
        mode="lines+markers", name="Forecast",
        line=dict(color=config.AMBER, width=2),
        marker=dict(size=6, color=config.AMBER),
        hovertemplate="h+%{x}<br>%{y:.2f} kWh<extra>Forecast</extra>",
    ))
    fig.update_layout(title=title, bargap=0.45)
    fig.update_xaxes(title_text="Hours ahead of forecast origin",
                     dtick=2, tickmode="linear")
    fig.update_yaxes(title_text="kWh per hour")
    return theme.apply(fig, height=height)


def error_over_horizon(df: pd.DataFrame, metric: str = "MAE",
                       title: str = "", height: int = 340) -> go.Figure:
    """Metric by forecast horizon, one line per model."""
    fig = go.Figure()
    model_col = loaders.model_column(df) or "Model"
    for i, name in enumerate(sorted(df[model_col].astype(str).unique())):
        sub = df[df[model_col].astype(str) == name].sort_values("Horizon")
        fig.add_trace(go.Scatter(
            x=sub["Horizon"], y=sub[metric],
            mode="lines+markers", name=name,
            line=dict(color=loaders.model_color(name, i), width=2),
            marker=dict(size=5),
            hovertemplate=f"h+%{{x}}<br>{metric} %{{y:.3f}}<extra>{name}</extra>",
        ))
    fig.update_layout(title=title)
    fig.update_xaxes(title_text="Forecast horizon (hours ahead)",
                     dtick=2, tickmode="linear")
    fig.update_yaxes(title_text=f"{metric} (kWh)")
    return theme.apply(fig, height=height)


def metric_bars(df: pd.DataFrame, metric: str, title: str = "",
                height: int = 300) -> go.Figure:
    """Horizontal bars for one metric. Alphabetical order, no ranking."""
    model_col = loaders.model_column(df) or "Model"
    sub = df[[model_col, metric]].dropna().copy()
    sub = sub.sort_values(model_col, key=lambda s: s.astype(str).str.lower(),
                          ascending=False)
    colors = [loaders.model_color(m, i)
              for i, m in enumerate(sub[model_col].astype(str))]
    fig = go.Figure(go.Bar(
        x=sub[metric], y=sub[model_col].astype(str),
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="%{y}<br>%{x:.3f}<extra></extra>",
    ))
    meta = config.METRIC_META.get(metric, {})
    unit = meta.get("unit", "")
    fig.update_layout(title=title or meta.get("label", metric),
                      showlegend=False)
    fig.update_xaxes(title_text=f"{meta.get('label', metric)}"
                                + (f" ({unit})" if unit else ""))
    return theme.apply(fig, height=height)


def hourly_profile(df: pd.DataFrame, value_col: str = "demand_kWh",
                   hour_col: str = "hour", title: str = "",
                   height: int = 300) -> go.Figure:
    """Mean demand by hour of day with an interquartile band."""
    grouped = df.groupby(hour_col)[value_col]
    mean = grouped.mean()
    q1, q3 = grouped.quantile(0.25), grouped.quantile(0.75)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(q3.index) + list(q3.index[::-1]),
        y=list(q3.values) + list(q1.values[::-1]),
        fill="toself", fillcolor="rgba(0,224,198,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Interquartile range", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=mean.index, y=mean.values,
        mode="lines+markers", name="Mean",
        line=dict(color=config.CYAN, width=2),
        marker=dict(size=5),
        hovertemplate="%{x}:00<br>%{y:.2f} kWh<extra>Mean</extra>",
    ))
    fig.update_layout(title=title)
    fig.update_xaxes(title_text="Hour of day (America/Los_Angeles)",
                     dtick=2, tickmode="linear")
    fig.update_yaxes(title_text="kWh per hour")
    return theme.apply(fig, height=height)


def weekly_heatmap(df: pd.DataFrame, value_col: str = "demand_kWh",
                   title: str = "", height: int = 340) -> go.Figure:
    """Mean demand by weekday x hour."""
    from core.formatting import DAY_SHORT

    pivot = (df.pivot_table(index="day_of_week", columns="hour",
                            values=value_col, aggfunc="mean")
             .reindex(range(7)))
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=[DAY_SHORT[i] for i in pivot.index],
        colorscale=theme.HEATMAP_SCALE,
        colorbar=dict(title=dict(text="kWh", side="right"),
                      tickfont=dict(color=config.TEXT_MUTED, size=10),
                      outlinewidth=0, thickness=10),
        hovertemplate="%{y} %{x}:00<br>%{z:.2f} kWh<extra></extra>",
    ))
    fig.update_layout(title=title)
    fig.update_xaxes(title_text="Hour of day", dtick=2, tickmode="linear")
    return theme.apply(fig, height=height)


def distribution(values: pd.Series, title: str = "",
                 height: int = 300) -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=values, nbinsx=48,
        marker=dict(color="rgba(0,224,198,0.42)",
                    line=dict(color=config.CYAN, width=0.6)),
        hovertemplate="%{x:.1f} kWh<br>%{y} hours<extra></extra>",
    ))
    fig.update_layout(title=title, showlegend=False, bargap=0.04)
    fig.update_xaxes(title_text="kWh per hour")
    fig.update_yaxes(title_text="Number of hours")
    return theme.apply(fig, height=height)


def grouped_bars(labels, series: dict, title: str = "",
                 y_title: str = "", height: int = 320) -> go.Figure:
    """Generic grouped bar chart; `series` maps name -> values."""
    fig = go.Figure()
    for i, (name, values) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            x=labels, y=values, name=name,
            marker=dict(color=loaders.model_color(name, i)),
            hovertemplate="%{x}<br>%{y:.2f}<extra>" + str(name) + "</extra>",
        ))
    fig.update_layout(title=title, barmode="group", bargap=0.3)
    fig.update_yaxes(title_text=y_title)
    return theme.apply(fig, height=height)


def acf_plot(values: pd.Series, max_lag: int = 180, title: str = "",
             height: int = 320) -> go.Figure:
    """Autocorrelation computed from the stored demand series.

    Uses the standard biased estimator (denominator n), matching statsmodels'
    default. This is a statistic of the real series, not a model output.
    """
    x = pd.Series(values).astype(float).dropna().to_numpy()
    n = x.size
    max_lag = int(min(max_lag, max(1, n - 1)))
    x = x - x.mean()
    denom = float(np.dot(x, x))

    lags = np.arange(1, max_lag + 1)
    if denom == 0:
        acf = np.zeros(max_lag)
    else:
        acf = np.array([float(np.dot(x[: n - k], x[k:])) / denom for k in lags])

    ci = 1.96 / np.sqrt(n)
    colors = [config.CYAN if k in (1, 24, 168) else "rgba(230,237,240,0.30)"
              for k in lags]

    fig = go.Figure(go.Bar(
        x=lags, y=acf, marker=dict(color=colors),
        hovertemplate="lag %{x}<br>ACF %{y:.4f}<extra></extra>",
    ))
    for sign in (1, -1):
        fig.add_hline(y=sign * ci, line=dict(color=config.AMBER, width=1,
                                             dash="dot"))
    fig.update_layout(title=title, showlegend=False, bargap=0.1)
    fig.update_xaxes(title_text="Lag (hours)")
    fig.update_yaxes(title_text="Autocorrelation")
    return theme.apply(fig, height=height)


def scatter_actual_pred(df: pd.DataFrame, title: str = "",
                        height: int = 340) -> go.Figure:
    """Calibration scatter with a 45-degree reference line."""
    hi = float(max(df["actual"].max(), df["prediction"].max()))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, hi], y=[0, hi], mode="lines",
        line=dict(color="rgba(230,237,240,0.25)", width=1, dash="dash"),
        name="Perfect agreement", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df["actual"], y=df["prediction"], mode="markers",
        marker=dict(size=5, color=config.CYAN, opacity=0.45,
                    line=dict(width=0)),
        name="Test hours",
        hovertemplate="Observed %{x:.2f}<br>Forecast %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(title=title, hovermode="closest")
    fig.update_xaxes(title_text="Observed kWh")
    fig.update_yaxes(title_text="Forecast kWh")
    return theme.apply(fig, height=height)


def importance_bars(df, feature_col: str, value_col: str, colour: str,
                    title: str = "", top_n: int = 20, height: int = 0):
    """Horizontal importance bars, largest at the top."""
    sub = df[[feature_col, value_col]].dropna().copy()
    sub = sub.sort_values(value_col, ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        x=sub[value_col], y=sub[feature_col].astype(str),
        orientation="h",
        marker=dict(color=colour),
        hovertemplate="%{y}<br>%{x:.5f}<extra></extra>",
    ))
    fig.update_layout(title=title, showlegend=False)
    fig.update_xaxes(title_text=str(value_col))
    return theme.apply(fig, height=height or max(300, 24 * len(sub)))


def importance_compare(frames: dict, feature_col_map: dict,
                       title: str = "", top_n: int = 15, height: int = 0):
    """Two models' importances side by side over their shared feature set."""
    ordered = None
    series = {}
    for i, (name, (df, fcol, vcol)) in enumerate(frames.items()):
        s = (df[[fcol, vcol]].dropna()
             .groupby(fcol)[vcol].mean())
        # Normalise within model: importances use different scales per model.
        total = float(s.sum())
        if total:
            s = s / total
        series[name] = s
        ordered = s if ordered is None else ordered.add(s, fill_value=0)

    if ordered is None or ordered.empty:
        return None
    features = list(ordered.sort_values(ascending=True).tail(top_n).index)

    fig = go.Figure()
    for i, (name, s) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            x=[float(s.get(f, 0.0)) for f in features],
            y=[str(f) for f in features],
            orientation="h", name=str(name),
            marker=dict(color=loaders.model_color(name, i)),
            hovertemplate="%{y}<br>%{x:.4f}<extra>" + str(name) + "</extra>",
        ))
    fig.update_layout(title=title, barmode="group", bargap=0.25)
    fig.update_xaxes(title_text="Share of that model's total importance")
    return theme.apply(fig, height=height or max(340, 30 * len(features)))
