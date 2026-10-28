"""Streamlit API compatibility.

`use_container_width` is deprecated in favour of `width="stretch"`, and which
one is valid depends on the installed Streamlit version. Detect once at import
so views contain no version checks.
"""

from __future__ import annotations

import inspect

import streamlit as st


def _supports_width(fn) -> bool:
    try:
        return "width" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


STRETCH: dict = ({"width": "stretch"} if _supports_width(st.plotly_chart)
                 else {"use_container_width": True})

TABLE: dict = ({"width": "stretch"} if _supports_width(st.dataframe)
               else {"use_container_width": True})

IMAGE: dict = ({"width": "stretch"} if _supports_width(st.image)
               else {"use_container_width": True})
