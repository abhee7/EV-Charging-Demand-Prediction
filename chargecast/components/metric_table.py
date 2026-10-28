"""Neutral metric presentation.

The neutrality requirement lives here rather than in page copy, so it cannot
drift as pages are added:

* default ordering is alphabetical by model name
* ordering by a metric requires an explicit argument, and renders a label
  saying it is a display sort and not a scientific ranking
* no badge, trophy, highlight row, medal or superlative is emitted anywhere

`assert_neutral` lets the test suite check the rule mechanically.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from core import loaders
from core import ui

# Terms that are never acceptable, in any context.
BANNED_TERMS = (
    "best model", "best-model", "winner", "champion", "top model",
    "#1 model", "best accuracy", "superior model", "trophy",
    "rank 1", "1st place", "gold medal", "best performing",
    "outperforms all", "leading model",
)

# Terms acceptable only when negated, e.g. "not a scientific ranking".
NEGATABLE_TERMS = ("ranking", "best")

NEGATORS = ("no ", "not ", "never ", "without ", "neither ", "rather than ",
            "cannot ", "does not ", "is not ", "are not ", "carries no ")

SORT_DISCLAIMER = (
    "Display sort only. This ordering is a viewing convenience and not a "
    "scientific ranking: the models differ in which metric favours them, and "
    "ordering by one metric does not establish overall performance."
)


def _is_negated(text: str, position: int, window: int = 60) -> bool:
    """True if a negator appears shortly before `position`."""
    lead = text[max(0, position - window):position]
    return any(neg in lead for neg in NEGATORS)


def assert_neutral(text: str) -> None:
    """Raise if rendered copy asserts a ranking.

    Negated mentions are allowed, so a disclaimer saying the ordering is "not
    a scientific ranking" passes while a claim that a model is best does not.
    """
    lowered = text.lower()

    hits = [term for term in BANNED_TERMS if term in lowered]

    for term in NEGATABLE_TERMS:
        start = 0
        while True:
            idx = lowered.find(term, start)
            if idx == -1:
                break
            if not _is_negated(lowered, idx):
                hits.append(f"{term} (not negated)")
                break
            start = idx + len(term)

    if hits:
        raise AssertionError(f"Ranking language in dashboard copy: {hits}")


def _display_frame(df: pd.DataFrame, model_col: str,
                   metrics: dict[str, str]) -> pd.DataFrame:
    cols = [model_col] + [metrics[k] for k in config.METRIC_ORDER
                          if k in metrics]
    out = df[cols].copy()
    rename = {model_col: "Model"}
    for canon in config.METRIC_ORDER:
        if canon not in metrics:
            continue
        meta = config.METRIC_META[canon]
        unit = meta["unit"]
        rename[metrics[canon]] = (f"{meta['label']} ({unit})" if unit
                                  else meta["label"])
    return out.rename(columns=rename)


def metric_table(df: pd.DataFrame, metrics: dict[str, str] | None = None,
                 sort_by: str | None = None, caption: str = "") -> None:
    """Render stored metrics. `sort_by` is a canonical metric key."""
    model_col = loaders.model_column(df)
    if model_col is None:
        st.info("No model column found in this file.")
        return

    metrics = metrics or loaders.resolve_metrics(df)
    if not metrics:
        st.dataframe(df, **ui.TABLE, hide_index=True)
        return

    frame = df.copy()
    note = caption
    if sort_by and sort_by in metrics:
        ascending = config.METRIC_META[sort_by]["lower_is_better"]
        frame = frame.sort_values(metrics[sort_by], ascending=ascending)
        note = SORT_DISCLAIMER
    else:
        frame = frame.sort_values(
            model_col, key=lambda s: s.astype(str).str.lower())

    st.dataframe(_display_frame(frame, model_col, metrics),
                 **ui.TABLE, hide_index=True)
    if note:
        st.markdown(f'<div class="cc-section-note">{note}</div>',
                    unsafe_allow_html=True)


def sort_control(metrics: dict[str, str], key: str) -> str | None:
    """Selectbox returning a canonical metric key, or None for name order."""
    labels = ["Model name (default)"]
    mapping: dict[str, str | None] = {"Model name (default)": None}
    for canon in config.METRIC_ORDER:
        if canon in metrics:
            label = config.METRIC_META[canon]["label"]
            labels.append(label)
            mapping[label] = canon
    choice = st.selectbox("Display order", labels, key=key)
    return mapping[choice]


def metric_definitions() -> None:
    with st.expander("How to read these metrics"):
        for canon in config.METRIC_ORDER:
            meta = config.METRIC_META[canon]
            st.markdown(f"**{meta['label']}** \u2014 {meta['help']}")
        st.markdown(
            "No single metric settles the comparison. MAE and RMSE answer "
            "different questions about error size, and a model can lead on "
            "one while trailing on the other."
        )
