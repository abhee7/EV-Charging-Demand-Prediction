"""Model comparison.

All models are shown together: the four feature-based models plus the active
time-series comparator, SARIMAX + Fourier. The abandoned SARIMA output is
quarantined in a collapsed section and never enters the main tables.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from components import charts, empty_state, kpi, metric_table
from core import loaders
from core import ui


def _combine(*keys) -> tuple[pd.DataFrame | None, list]:
    frames, missing = [], []
    for key in keys:
        ds = loaders.load(key)
        if ds:
            frames.append(ds.df)
        else:
            missing.append(ds)
    if not frames:
        return None, missing
    return pd.concat(frames, ignore_index=True), missing


def render() -> None:
    st.markdown("## Model comparison")
    kpi.caption(
        "Every figure is read from the stored evaluation files. Models are "
        "listed alphabetically by default; that ordering carries no ranking."
    )

    # ---------------- Test metrics ----------------
    st.markdown("### Test metrics")
    combined, missing = _combine("test_metrics", "sarimax_test_metrics")
    if combined is not None:
        metrics = loaders.resolve_metrics(combined)
        sort_by = metric_table.sort_control(metrics, key="cmp_sort")
        metric_table.metric_table(combined, metrics, sort_by=sort_by)
        metric_table.metric_definitions()

        kpi.note(config.DM_STATEMENT, label="On the two closest models.")

        st.markdown("")
        cols = st.columns(2, gap="medium")
        for i, canon in enumerate([m for m in config.METRIC_ORDER
                                   if m in metrics]):
            with cols[i % 2]:
                st.plotly_chart(
                    charts.metric_bars(
                        combined, metrics[canon],
                        title=config.METRIC_META[canon]["label"]),
                    **ui.STRETCH,
                )
        for ds in missing:
            empty_state.from_dataset(ds)
    else:
        for ds in missing:
            empty_state.from_dataset(ds)

    # ---------------- Horizon ----------------
    st.markdown("### Accuracy by forecast horizon")
    kpi.caption(
        "One hour ahead and 24 hours ahead measure different things. The "
        "horizon curve separates models that pooled metrics do not."
    )
    hor, hor_missing = _combine("horizon_metrics", "sarimax_horizon_metrics")
    if hor is not None:
        hmetrics = loaders.resolve_metrics(hor)
        options = [m for m in ("MAE", "RMSE") if m in hmetrics]
        if options:
            canon = st.radio("Metric", options, horizontal=True,
                             key="cmp_hor_metric")
            st.plotly_chart(
                charts.error_over_horizon(
                    hor, metric=hmetrics[canon],
                    title=f"{config.METRIC_META[canon]['label']} by hours ahead"),
                **ui.STRETCH,
            )
        else:
            st.dataframe(hor, **ui.TABLE, hide_index=True)
        for ds in hor_missing:
            empty_state.from_dataset(ds)
    else:
        for ds in hor_missing:
            empty_state.from_dataset(ds)

    # ---------------- Validation ----------------
    st.markdown("### Validation results")
    kpi.caption(
        "Scored on the validation split and used for model selection. The "
        "test table above is the reported result."
    )
    val, val_missing = _combine("validation_metrics",
                                "sarimax_validation_metrics")
    if val is not None:
        model_col = loaders.model_column(val)
        names = loaders.sorted_models(val)
        picked = st.multiselect("Models", names, default=names,
                                key="cmp_val_models")
        subset = val[val[model_col].astype(str).isin(picked)] if picked else val
        st.dataframe(subset, **ui.TABLE, hide_index=True)
    else:
        for ds in val_missing:
            empty_state.from_dataset(ds)

    # ---------------- Legacy quarantine ----------------
    legacy = loaders.load("legacy_sarima")
    if legacy:
        with st.expander("Superseded / legacy \u2014 not part of the comparison"):
            kpi.note(
                "These figures come from an abandoned SARIMA implementation. "
                "They are excluded from every table and chart above. The "
                "active time-series comparator is SARIMAX + Fourier. Retained "
                "for traceability only.",
                label="Superseded.",
            )
            st.dataframe(legacy.df, **ui.TABLE, hide_index=True)
