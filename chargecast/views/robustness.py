"""Robustness — two target constructions, presented symmetrically.

Both sides use the same layout, the same chart types and the same wording
templates, so the page cannot imply a preference through presentation.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from components import charts, empty_state, kpi, metric_table
from core import formatting as fmt
from core import loaders
from core import ui

TARGET_A = "Primary target \u2014 interval allocation"
TARGET_B = "Robustness target \u2014 arrival-hour allocation"

DESC_A = ("Each session's energy is spread uniformly across the hours from "
          "connectionTime to doneChargingTime. This approximates when energy "
          "was drawn, and relies on doneChargingTime, which is only known "
          "once the session has ended.")
DESC_B = ("Each session's entire kWhDelivered is assigned to the hour the "
          "vehicle connected. This is knowable at the moment of arrival, and "
          "attributes energy to arrival time rather than to draw time.")

SERIES = {TARGET_A: "hourly_demand", TARGET_B: "hourly_demand_arrival"}
METRICS = {TARGET_A: "test_metrics", TARGET_B: "arrival_test_metrics"}
HORIZONS = {TARGET_A: "horizon_metrics", TARGET_B: "arrival_horizon_metrics"}


def _series_panel(key: str, label: str) -> None:
    ds = loaders.load(key)
    if not ds:
        empty_state.from_dataset(ds)
        return
    df = ds.df
    st.plotly_chart(
        charts.demand_ribbon(df["timestamp"], df["demand_kWh"],
                             title="", height=230),
        **ui.STRETCH)
    st.markdown(
        f'<div class="cc-section-note">{len(df):,} hourly observations '
        f'\u00b7 {fmt.energy(float(df["demand_kWh"].sum()), 0)} total '
        f'\u00b7 peak {fmt.energy(float(df["demand_kWh"].max()), 1)} '
        f'\u00b7 std {df["demand_kWh"].std():.2f} '
        f'\u00b7 {(df["demand_kWh"] <= 0).mean() * 100:.1f}% zero hours</div>',
        unsafe_allow_html=True)


def _metric_panel(key: str) -> None:
    ds = loaders.load(key)
    if ds:
        metric_table.metric_table(ds.df)
    else:
        empty_state.from_dataset(ds)


def _horizon_panel(key: str) -> None:
    ds = loaders.load(key)
    if not ds:
        empty_state.from_dataset(ds)
        return
    metrics = loaders.resolve_metrics(ds.df)
    col = metrics.get("MAE")
    if col is None:
        st.dataframe(ds.df, **ui.TABLE, hide_index=True)
        return
    st.plotly_chart(
        charts.error_over_horizon(ds.df, metric=col, title="", height=300),
        **ui.STRETCH)


def render() -> None:
    st.markdown("## Robustness: target construction")
    kpi.caption(
        "Hourly demand can be reconstructed from session records in more than "
        "one defensible way. This experiment holds models, features and split "
        "fixed and varies only how session energy is mapped to hours. Neither "
        "construction is treated as correct."
    )

    # ---------------- Definitions ----------------
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        kpi.target_head(TARGET_A)
        kpi.caption(DESC_A)
    with c2:
        kpi.target_head(TARGET_B)
        kpi.caption(DESC_B)

    # ---------------- Series ----------------
    st.markdown("### Reconstructed demand series")
    s1, s2 = st.columns(2, gap="medium")
    with s1:
        kpi.target_head(TARGET_A)
        _series_panel(SERIES[TARGET_A], TARGET_A)
    with s2:
        kpi.target_head(TARGET_B)
        _series_panel(SERIES[TARGET_B], TARGET_B)
    kpi.caption(
        "Both series are built from the same cleaned sessions, so total "
        "energy is comparable. They differ in how that energy is spread "
        "across hours, which changes the smoothness of the series and "
        "therefore how predictable it is."
    )

    # ---------------- Metrics ----------------
    st.markdown("### Test metrics under each construction")
    m1, m2 = st.columns(2, gap="medium")
    with m1:
        kpi.target_head(TARGET_A)
        _metric_panel(METRICS[TARGET_A])
    with m2:
        kpi.target_head(TARGET_B)
        _metric_panel(METRICS[TARGET_B])

    kpi.note(config.CROSS_TARGET_WARNING, label="Reading this comparison.")

    # ---------------- Paired view ----------------
    ds_a, ds_b = loaders.load(METRICS[TARGET_A]), loaders.load(METRICS[TARGET_B])
    if ds_a and ds_b:
        st.markdown("### How model behaviour changes between constructions")
        col_a = loaders.model_column(ds_a.df)
        col_b = loaders.model_column(ds_b.df)
        met_a = loaders.resolve_metrics(ds_a.df)
        met_b = loaders.resolve_metrics(ds_b.df)

        a = ds_a.df.set_index(ds_a.df[col_a].astype(str))
        b = ds_b.df.set_index(ds_b.df[col_b].astype(str))
        shared = sorted(set(a.index) & set(b.index))
        common = [m for m in config.METRIC_ORDER if m in met_a and m in met_b]

        if not shared or not common:
            kpi.caption(
                "No models or metrics are common to both result sets, so a "
                "paired view cannot be shown.")
        else:
            rows = []
            for name in shared:
                row = {"Model": name}
                for canon in common:
                    label = config.METRIC_META[canon]["label"]
                    row[f"{label} \u2014 primary"] = a.loc[name, met_a[canon]]
                    row[f"{label} \u2014 arrival-hour"] = b.loc[name, met_b[canon]]
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), **ui.TABLE, hide_index=True)

            canon = st.radio(
                "Metric", common, horizontal=True,
                format_func=lambda m: config.METRIC_META[m]["label"],
                key="rb_metric")
            st.plotly_chart(
                charts.grouped_bars(
                    shared,
                    {"Primary target": [a.loc[n, met_a[canon]] for n in shared],
                     "Arrival-hour target": [b.loc[n, met_b[canon]]
                                             for n in shared]},
                    title=f"{config.METRIC_META[canon]['label']} under each "
                          "target construction",
                    y_title=config.METRIC_META[canon]["label"]),
                **ui.STRETCH)

            if "MASE" in common:
                kpi.caption(
                    "MASE is the most informative column here: because it is "
                    "scaled by a seasonal naive benchmark computed on each "
                    "target's own training data, it is the one metric that "
                    "remains interpretable across two series of different "
                    "scale."
                )

    # ---------------- Horizon ----------------
    st.markdown("### Accuracy by horizon under each construction")
    h1, h2 = st.columns(2, gap="medium")
    with h1:
        kpi.target_head(TARGET_A)
        _horizon_panel(HORIZONS[TARGET_A])
    with h2:
        kpi.target_head(TARGET_B)
        _horizon_panel(HORIZONS[TARGET_B])

    st.markdown("")
    kpi.note(config.TARGET_LIMITATION, label="Why this experiment exists.")
