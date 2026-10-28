"""KPI cards, model metric cards and inline notes."""

from __future__ import annotations

import html

import streamlit as st

import config
from core import formatting as fmt


def kpi(label: str, value: str, sub: str = "", accent: str = "") -> None:
    accent_cls = f" cc-kpi-accent-{accent}" if accent else ""
    sub_html = f'<div class="cc-kpi-sub">{html.escape(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="cc-card cc-kpi{accent_cls}">'
        f'<div class="cc-kpi-label">{html.escape(label)}</div>'
        f'<div class="cc-kpi-value">{html.escape(value)}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict]) -> None:
    if not items:
        return
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            kpi(item.get("label", ""), item.get("value", "\u2014"),
                item.get("sub", ""), item.get("accent", ""))


def model_card(name: str, values: dict, colour: str,
               keys: list[str] | None = None) -> None:
    """Metric card for one model. Carries no ranking, badge or superlative."""
    keys = keys or config.METRIC_ORDER
    cells = []
    for key in keys:
        if key not in values:
            continue
        label = config.METRIC_META.get(key, {}).get("label", key)
        cells.append(
            f'<div><div class="cc-metric-label">{html.escape(label)}</div>'
            f'<div class="cc-metric-value">'
            f'{html.escape(fmt.metric(values.get(key), key))}</div></div>'
        )
    st.markdown(
        f'<div class="cc-card cc-model-card">'
        f'<div class="cc-model-name">'
        f'<span class="cc-dot" style="background:{colour}"></span>'
        f'{html.escape(str(name))}</div>'
        f'<div class="cc-model-grid">{"".join(cells)}</div></div>',
        unsafe_allow_html=True,
    )


def note(text: str, label: str = "") -> None:
    prefix = f"<strong>{html.escape(label)}</strong> " if label else ""
    st.markdown(f'<div class="cc-note">{prefix}{html.escape(text)}</div>',
                unsafe_allow_html=True)


def caption(text: str) -> None:
    st.markdown(f'<div class="cc-section-note">{html.escape(text)}</div>',
                unsafe_allow_html=True)


def target_head(text: str) -> None:
    st.markdown(f'<div class="cc-target-head">{html.escape(text)}</div>',
                unsafe_allow_html=True)
