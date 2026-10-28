"""Demand analytics — descriptive structure of the demand series."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import charts, empty_state, kpi
from core import formatting as fmt
from core import loaders
from core import ui


def _acf_at(series: pd.Series, lag: int) -> float | None:
    x = series.astype(float).dropna().to_numpy()
    n = x.size
    if lag >= n:
        return None
    xc = x - x.mean()
    denom = float((xc ** 2).sum())
    if denom == 0:
        return None
    return float((xc[: n - lag] * xc[lag:]).sum()) / denom


def render() -> None:
    st.markdown("## Demand analytics")

    demand = loaders.load("hourly_demand")
    if not demand:
        empty_state.from_dataset(demand)
        return

    df = demand.df.sort_values("timestamp")
    kpi.caption(
        f"{len(df):,} hourly observations, {fmt.day_range(df['timestamp'])}. "
        "Calendar features are derived in America/Los_Angeles."
    )

    # ---------------- Hourly demand ----------------
    st.markdown("### Hourly demand")
    st.plotly_chart(
        charts.demand_ribbon(df["timestamp"], df["demand_kWh"],
                             title="Observed hourly demand", height=320),
        **ui.STRETCH,
    )

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        st.plotly_chart(
            charts.distribution(df["demand_kWh"],
                                title="Distribution of hourly demand"),
            **ui.STRETCH,
        )
    with c2:
        q = df["demand_kWh"].quantile([0.5, 0.95, 0.99])
        kpi.kpi_row([{"label": "Median hour",
                      "value": fmt.energy(float(q.loc[0.5]), 2)}])
        st.markdown("")
        kpi.kpi_row([{"label": "95th percentile",
                      "value": fmt.energy(float(q.loc[0.95]), 2),
                      "accent": "amber"}])
        st.markdown("")
        kpi.kpi_row([{"label": "Hours at zero demand",
                      "value": f"{int((df['demand_kWh'] <= 0).sum()):,}",
                      "sub": f"{(df['demand_kWh'] <= 0).mean() * 100:.1f}% of hours"}])

    # ---------------- Hour of day ----------------
    st.markdown("### Hour-of-day profile")
    if "hour" in df.columns:
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            st.plotly_chart(
                charts.hourly_profile(df, title="Demand by hour of day"),
                **ui.STRETCH)
        with d2:
            if "day_of_week" in df.columns:
                by_day = (df.groupby("day_of_week")["demand_kWh"].mean()
                          .reindex(range(7)))
                st.plotly_chart(
                    charts.grouped_bars(
                        [fmt.DAY_SHORT[i] for i in by_day.index],
                        {"Mean hourly demand": by_day.values},
                        title="Demand by day of week",
                        y_title="kWh per hour"),
                    **ui.STRETCH)
        if "day_of_week" in df.columns:
            st.plotly_chart(
                charts.weekly_heatmap(
                    df, title="Mean demand by weekday and hour"),
                **ui.STRETCH)

    # ---------------- Weekday vs weekend ----------------
    if "is_weekend" in df.columns and "hour" in df.columns:
        st.markdown("### Weekday against weekend")
        we = df.groupby(["is_weekend", "hour"])["demand_kWh"].mean().unstack(0)
        series = {("Weekend" if bool(c) else "Weekday"): we[c].values
                  for c in we.columns}
        st.plotly_chart(
            charts.grouped_bars(list(we.index), series,
                                title="Mean demand by hour",
                                y_title="kWh per hour"),
            **ui.STRETCH)

        split = df.groupby("is_weekend")["demand_kWh"].mean()
        kpi.kpi_row([
            {"label": "Mean demand, weekdays",
             "value": fmt.energy(float(split.get(0, float("nan"))), 2),
             "accent": "cyan"},
            {"label": "Mean demand, weekends",
             "value": fmt.energy(float(split.get(1, float("nan"))), 2)},
        ])

    # ---------------- Monthly ----------------
    if "month" in df.columns:
        st.markdown("### Monthly demand")
        monthly = df.groupby("month")["demand_kWh"].sum()
        st.plotly_chart(
            charts.grouped_bars(
                [fmt.MONTH_SHORT[int(m) - 1] for m in monthly.index],
                {"Total energy": monthly.values},
                title="Total demand by month", y_title="kWh"),
            **ui.STRETCH)
        kpi.caption(
            "Aggregated across the whole study period. With under a year of "
            "coverage, month totals reflect uneven coverage as much as "
            "seasonality, so they are not evidence of an annual cycle."
        )

    # ---------------- Peak statistics ----------------
    st.markdown("### Peak demand")
    p95 = float(df["demand_kWh"].quantile(0.95))
    peaks = df[df["demand_kWh"] >= p95]
    kpi.caption(
        f"A peak hour is defined here as demand at or above the 95th "
        f"percentile of the observed series ({p95:.2f} kWh). The threshold is "
        "a documented percentile rule rather than a chosen cut-off."
    )
    kpi.kpi_row([
        {"label": "Peak hours identified", "value": f"{len(peaks):,}"},
        {"label": "Highest observed hour",
         "value": fmt.energy(float(df['demand_kWh'].max()), 2),
         "accent": "amber"},
        {"label": "Share of energy in peak hours",
         "value": f"{peaks['demand_kWh'].sum() / df['demand_kWh'].sum() * 100:.1f}%"},
    ])
    if "hour" in peaks.columns and len(peaks):
        counts = peaks["hour"].value_counts().sort_index()
        st.plotly_chart(
            charts.grouped_bars(list(counts.index),
                                {"Peak hours": counts.values},
                                title="When peak hours occur",
                                y_title="Number of peak hours"),
            **ui.STRETCH)

    # --- peak analysis exports, if the research pipeline wrote any ---
    peak_files = loaders.list_files("peak_analysis", ("*.csv",))
    if peak_files:
        with st.expander("Peak analysis exports from the research pipeline"):
            for path in peak_files:
                st.markdown(f"**{path.name}**")
                try:
                    st.dataframe(pd.read_csv(path), **ui.TABLE,
                                 hide_index=True)
                except Exception as exc:  # noqa: BLE001
                    st.info(f"Could not read {path.name}: {exc}")

    # ---------------- Autocorrelation ----------------
    st.markdown("### Autocorrelation")
    kpi.caption(
        "Computed from the stored demand series. Lags 1, 24 and 168 hours are "
        "highlighted; dotted lines mark the 95% significance band."
    )
    max_lag = st.slider("Maximum lag (hours)", 24, 336, 180, step=12,
                        key="an_acf")
    st.plotly_chart(
        charts.acf_plot(df["demand_kWh"], max_lag=max_lag,
                        title="Autocorrelation of hourly demand"),
        **ui.STRETCH)

    cards = []
    for lag in (1, 24, 168):
        val = _acf_at(df["demand_kWh"], lag)
        if val is not None:
            cards.append({"label": f"ACF at lag {lag}", "value": f"{val:.4f}"})
    if cards:
        kpi.kpi_row(cards)

    # ---------------- Figures ----------------
    figures = loaders.list_files("figures", ("*.png",))
    if figures:
        st.markdown("### Generated figures")
        kpi.caption(
            f"{len(figures)} figures exported by the research pipeline, shown "
            "as produced.")
        cols = st.columns(2, gap="medium")
        for i, path in enumerate(figures):
            with cols[i % 2]:
                st.image(str(path), **ui.IMAGE)
                st.markdown(f'<div class="cc-fig-name">{path.name}</div>',
                            unsafe_allow_html=True)
