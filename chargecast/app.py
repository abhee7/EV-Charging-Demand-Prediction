"""ChargeCast — EV charging demand intelligence.

A read-only visualisation layer over the research outputs of
EV-Charging-Demand-Prediction. This application loads no models, fits nothing,
retrains nothing, and never writes to data/ or results/.

Run from the repository root:

    streamlit run chargecast/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run chargecast/app.py` puts chargecast/ on sys.path already, but
# other launchers (python -m, pytest, an IDE) do not. Adding it explicitly
# makes the flat imports below work however the app is started.
_PKG = Path(__file__).resolve().parent
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

import streamlit as st  # noqa: E402

import config  # noqa: E402
from core import loaders  # noqa: E402
from theme import plotly_theme  # noqa: E402
from views import (  # noqa: E402
    about, analytics, comparison, explainability, forecast, overview,
    robustness,
)

VIEWS = {
    "overview": overview.render,
    "forecast": forecast.render,
    "comparison": comparison.render,
    "analytics": analytics.render,
    "explainability": explainability.render,
    "robustness": robustness.render,
    "about": about.render,
}


def _inject_css() -> None:
    css_path = _PKG / "theme" / "styles.css"
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _masthead() -> None:
    demand = loaders.load("hourly_demand")
    if demand:
        ts = demand.df["timestamp"]
        right = f"Caltech ACN \u00b7 {ts.min():%b %Y} \u2013 {ts.max():%b %Y}"
    else:
        right = "Caltech ACN"
    st.markdown(
        f'<div class="cc-masthead">'
        f'<div class="cc-wordmark">Charge<span>Cast</span></div>'
        f'<div class="cc-mast-sub">{config.APP_SUBTITLE}</div>'
        f'<div class="cc-mast-right">{right}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="cc-side-brand">Charge<span>Cast</span></div>'
            '<div class="cc-side-tag">Day-ahead EV charging demand '
            'forecasting</div>',
            unsafe_allow_html=True,
        )
        labels = [label for _, label in config.NAV]
        keys = [key for key, _ in config.NAV]
        choice = st.radio("Sections", labels, label_visibility="collapsed",
                          key="nav")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="cc-side-tag">Read-only view of the research '
            'outputs. Every figure is loaded from a stored result file; '
            'nothing is computed, estimated or retrained here.</div>',
            unsafe_allow_html=True,
        )
        return keys[labels.index(choice)]


def main() -> None:
    st.set_page_config(
        page_title=f"{config.APP_NAME} \u2014 {config.APP_SUBTITLE}",
        page_icon="\u26a1",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    plotly_theme.register()
    _inject_css()

    view_key = _sidebar()
    _masthead()

    render = VIEWS.get(view_key, overview.render)
    try:
        render()
    except Exception as exc:  # noqa: BLE001
        st.error(
            f"This section could not be rendered: {exc}\n\n"
            "The rest of the dashboard is unaffected. Check the artefact "
            "status table on the About page to confirm which result files "
            "were found."
        )


if __name__ == "__main__":
    main()
