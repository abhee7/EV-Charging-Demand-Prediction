"""Empty states: direction rather than apology."""

from __future__ import annotations

import html

import streamlit as st

from core.loaders import Dataset

_LEAD = {
    "missing": "Results not available yet \u2014 run the corresponding experiment first.",
    "columns": "The file was found but its columns do not match what this panel needs.",
    "empty": "The file exists but contains no rows.",
    "error": "The file could not be read.",
}


def empty(title: str, body: str, path: str = "") -> None:
    path_html = (f'<div class="cc-empty-path">{html.escape(path)}</div>'
                 if path else "")
    st.markdown(
        f'<div class="cc-empty">'
        f'<div class="cc-empty-title">{html.escape(title)}</div>'
        f'<div class="cc-empty-body">{html.escape(body)}</div>'
        f'{path_html}</div>',
        unsafe_allow_html=True,
    )


def from_dataset(ds: Dataset, extra: str = "") -> None:
    body = _LEAD.get(ds.reason, _LEAD["missing"])
    path = ""
    if ds.reason == "missing":
        body += f" Produced by {ds.spec.produced_by}."
        path = ds.detail.replace("Expected at ", "")
    else:
        body += f" {ds.detail}"
    if extra:
        body += f" {extra}"
    empty(ds.spec.label, body, path)


def pending(title: str, body: str, path: str = "") -> None:
    empty(title, body, path)
