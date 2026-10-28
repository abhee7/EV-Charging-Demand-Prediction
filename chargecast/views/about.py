"""About the project — methodology, controls and live artefact status."""

from __future__ import annotations

import html

import streamlit as st

import config
from components import kpi
from core import loaders
from core import ui

PIPELINE = [
    "Charging sessions (Caltech ACN)",
    "Data cleaning",
    "Hourly demand reconstruction",
    "Feature engineering",
    "Chronological train / validation / test split",
    "Recursive 24-hour forecasting",
    "Model evaluation",
]

LEAKAGE_CONTROLS = [
    ("Chronological splitting", "Train, validation and test are contiguous "
     "periods in time order. Observations are never shuffled, so no model is "
     "fitted on data that follows its test period."),
    ("Shifted rolling statistics", "Rolling means and standard deviations are "
     "computed over windows ending before the hour being predicted, so the "
     "target never enters its own feature."),
    ("Lagged demand only", "Features use demand at 1, 2, 24, 48, 168 and 336 "
     "hours before the forecast origin. No contemporaneous or future value of "
     "the target is used as an input."),
    ("Selection on validation", "Hyperparameters are chosen on the validation "
     "split. The test period is used once, for the reported result."),
    ("Session fields excluded", "disconnectTime, doneChargingTime and the "
     "user input fields are only known after a session ends, so they are used "
     "in describing the data, never as forecasting features."),
]

LIMITATIONS = [
    ("Reconstructed target", config.TARGET_LIMITATION),
    ("Single site", "All sessions come from the Caltech campus. Findings "
     "describe one open-campus workplace site and do not generalise to public "
     "fast charging or residential use."),
    ("Study period", "Coverage is under a year, so annual seasonality cannot "
     "be estimated and monthly totals partly reflect uneven coverage."),
    ("No external variables", "Weather, traffic, electricity price and campus "
     "calendar data are absent from the dataset, so their influence cannot be "
     "tested."),
    ("Test period", "The test split is a single contiguous block of forecast "
     "origins. Metrics are conditional on that period."),
    ("Closeness of two models", config.DM_STATEMENT),
]


def render() -> None:
    st.markdown("## About the project")

    st.markdown("### Research question")
    st.markdown(
        "> Which machine-learning and time-series approaches provide accurate "
        "day-ahead forecasts of EV charging demand, and which factors "
        "influence demand?"
    )

    st.markdown("### Dataset")
    kpi.caption(
        "Caltech Adaptive Charging Network session records. Sessions are "
        "aggregated into an hourly demand series on a regular UTC timeline, "
        "with calendar features derived in America/Los_Angeles so the daily "
        "cycle aligns with campus activity rather than with UTC midnight."
    )

    st.markdown("### Target reconstruction")
    kpi.note(config.TARGET_LIMITATION, label="Primary target.")
    kpi.caption(
        "The arrival-hour construction assigns each session's entire energy "
        "to its connection hour instead. It is knowable at arrival time and "
        "is run as a separate experiment rather than treated as a correction."
    )

    st.markdown("### Pipeline")
    steps = []
    for i, step in enumerate(PIPELINE):
        steps.append(f'<div class="cc-flow-step">{html.escape(step)}</div>')
        if i < len(PIPELINE) - 1:
            steps.append('<div class="cc-flow-rule"></div>')
    st.markdown(f'<div class="cc-flow">{"".join(steps)}</div>',
                unsafe_allow_html=True)

    st.markdown("### Forecasting strategy")
    st.markdown(
        "- Day-ahead forecasts over a 24-hour horizon from each origin\n"
        "- Chronological train / validation / test split, no shuffling\n"
        "- Recursive multi-step forecasting for the feature-based models\n"
        "- Lagged demand at 1, 2, 24, 48, 168 and 336 hours, with rolling "
        "mean and standard deviation over 24 and 168 hours\n"
        "- Seasonal naive included as a benchmark, because a strongly "
        "seasonal series can be forecast well without any fitted model\n"
        "- SARIMAX with Fourier terms as the time-series comparator, which "
        "accommodates the daily cycle alongside weekly structure that a "
        "single-seasonality SARIMA cannot represent"
    )

    st.markdown("### Evaluation metrics")
    for canon in config.METRIC_ORDER:
        meta = config.METRIC_META[canon]
        st.markdown(f"**{meta['label']}** \u2014 {meta['help']}")
    kpi.caption(
        "MAPE is not reported. A substantial share of hours record zero "
        "demand, where MAPE is undefined; sMAPE and MASE remain defined."
    )

    st.markdown("### Data leakage controls")
    for title, body in LEAKAGE_CONTROLS:
        st.markdown(f"**{title}.** {body}")

    st.markdown("### Limitations")
    for title, body in LIMITATIONS:
        st.markdown(f"**{title}.** {body}")

    st.markdown("### Artefact status")
    kpi.caption(
        "Live status of every file this dashboard expects. The dashboard is "
        "read-only: it never writes to data/ or results/, and never fills a "
        "gap with an estimate."
    )
    st.dataframe(loaders.availability(), **ui.TABLE, hide_index=True)
    kpi.caption(f"Repository root resolved as: {config.ROOT}")

    st.markdown("### Citation")
    st.code(
        "@inproceedings{lee_acndata_2019,\n"
        "  author = {Lee, Zachary J. and Li, Tongxin and Low, Steven H.},\n"
        "  title = {{ACN}-{Data}: {Analysis} and {Applications} of an\n"
        "           {Open} {EV} {Charging} {Dataset}},\n"
        "  booktitle = {Proceedings of the Tenth International Conference\n"
        "               on Future Energy Systems},\n"
        "  series = {e-Energy '19},\n"
        "  month = jun,\n"
        "  year = {2019},\n"
        "  location = {Phoenix, Arizona}\n"
        "}",
        language="bibtex",
    )
