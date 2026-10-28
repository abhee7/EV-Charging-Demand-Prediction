"""Explainability — SHAP importance and tree feature importance.

Everything shown is read from the research exports. The dashboard computes no
SHAP values and fits no explainer.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from components import charts, empty_state, kpi
from core import loaders
from core import ui

SHAP_IMPORTANCE = {
    "Random Forest": "rf_shap_importance",
    "XGBoost": "xgb_shap_importance",
}
TREE_IMPORTANCE = {
    "Random Forest": "rf_importance",
    "XGBoost": "xgb_importance",
}
SHAP_VALUES = {
    "Random Forest": "rf_shap_values",
    "XGBoost": "xgb_shap_values",
}


def _frames(mapping: dict) -> dict:
    """Return {model: (df, feature_col, value_col)} for available files."""
    out = {}
    for name, key in mapping.items():
        ds = loaders.load(key)
        if not ds:
            continue
        fcol, vcol = loaders.feature_value_columns(ds.df)
        if fcol is None or vcol is None:
            continue
        out[name] = (ds.df, fcol, vcol)
    return out


def _section(title: str, mapping: dict, blurb: str) -> None:
    st.markdown(f"### {title}")
    kpi.caption(blurb)

    frames = _frames(mapping)
    if not frames:
        for name, key in mapping.items():
            empty_state.from_dataset(loaders.load(key))
        return

    if len(frames) > 1:
        fig = charts.importance_compare(
            frames, {}, title=f"{title} \u2014 models side by side")
        if fig is not None:
            st.plotly_chart(fig, **ui.STRETCH)
            kpi.caption(
                "Values are shown as each model's share of its own total, "
                "because importance scales are not comparable across models "
                "in raw units."
            )

    cols = st.columns(len(frames), gap="medium")
    for i, (name, (df, fcol, vcol)) in enumerate(frames.items()):
        with cols[i]:
            kpi.target_head(name)
            st.plotly_chart(
                charts.importance_bars(df, fcol, vcol,
                                       loaders.model_color(name, i)),
                **ui.STRETCH)

    for name, key in mapping.items():
        if name not in frames:
            empty_state.from_dataset(loaders.load(key))


def render() -> None:
    st.markdown("## Explainability")
    kpi.note(config.NOT_CAUSAL, label="Not causal inference.")

    # ---------------- Combined SHAP ----------------
    st.markdown("### Combined SHAP importance")
    combined = loaders.load("shap_combined")
    if combined:
        df = combined.df
        model_col = loaders.model_column(df)
        fcol, vcol = loaders.feature_value_columns(df)
        if model_col is not None and fcol is not None and vcol is not None:
            names = loaders.sorted_models(df)
            choice = st.selectbox("Model", names, key="ex_combined_model")
            sub = df[df[model_col].astype(str) == choice]
            st.plotly_chart(
                charts.importance_bars(sub, fcol, vcol,
                                       loaders.model_color(choice),
                                       title=f"{choice} \u2014 SHAP importance"),
                **ui.STRETCH)
        elif fcol is not None and vcol is not None:
            st.plotly_chart(
                charts.importance_bars(df, fcol, vcol, config.CYAN,
                                       title="Combined SHAP importance"),
                **ui.STRETCH)
        else:
            st.dataframe(df, **ui.TABLE, hide_index=True)
    else:
        empty_state.from_dataset(combined)

    # ---------------- Per-model SHAP ----------------
    _section(
        "SHAP importance by model", SHAP_IMPORTANCE,
        "Mean absolute SHAP contribution per feature, as exported for each "
        "model. Larger values mean the feature moved that model's predictions "
        "more, on average.",
    )

    # ---------------- Tree importance ----------------
    _section(
        "Tree feature importance", TREE_IMPORTANCE,
        "Built-in importance from the fitted tree ensembles. Random Forest "
        "and XGBoost compute this differently, so scores are comparable "
        "within a model rather than between models.",
    )

    # ---------------- Raw SHAP values ----------------
    st.markdown("### Per-observation SHAP values")
    kpi.caption(
        "The raw exported SHAP matrices, one row per scored observation. "
        "Shown as a sample for inspection rather than plotted in full."
    )
    available = {name: key for name, key in SHAP_VALUES.items()
                 if loaders.load(key).ok}
    if available:
        choice = st.selectbox("Model", sorted(available.keys()),
                              key="ex_values_model")
        ds = loaders.load(available[choice])
        st.dataframe(ds.df.head(50), **ui.TABLE, hide_index=True)
        kpi.caption(
            f"{len(ds.df):,} rows and {len(ds.df.columns)} columns in "
            f"{loaders.rel(ds.spec.path)}. First 50 rows shown."
        )
    else:
        for name, key in SHAP_VALUES.items():
            empty_state.from_dataset(loaders.load(key))

    st.markdown("")
    kpi.note(config.NOT_CAUSAL, label="Reading these results.")
