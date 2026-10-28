"""Forecast — replay of stored test predictions.

No model is loaded and no inference runs here, so what is displayed is exactly
what the research pipeline produced.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import charts, empty_state, kpi
from core import formatting as fmt
from core import loaders
from core import ui

SOURCES = {
    "Primary target (interval allocation)": "test_predictions",
    "SARIMAX + Fourier": "sarimax_test_predictions",
    "Arrival-hour target": "arrival_test_predictions",
}


def _window_column(df: pd.DataFrame) -> str | None:
    for col in ("forecast_window", "window", "origin"):
        if col in df.columns:
            return col
    return None


def render() -> None:
    st.markdown("## Day-ahead forecast replay")
    kpi.caption(
        "Stored predictions only. Selecting a window reads back a forecast "
        "that was produced by the research pipeline; nothing is retrained and "
        "no live inference runs."
    )

    available = {label: key for label, key in SOURCES.items()
                 if loaders.load(key).ok}
    if not available:
        empty_state.from_dataset(loaders.load("test_predictions"))
        return

    source_label = st.selectbox("Prediction set", list(available.keys()),
                                key="fc_source")
    ds = loaders.load(available[source_label])
    df = ds.df

    model_col = loaders.model_column(df)
    if model_col is None:
        empty_state.empty("No model column",
                          f"{loaders.rel(ds.spec.path)} has no model column.")
        return

    win_col = _window_column(df)
    has_origin = "origin" in df.columns
    origins = (sorted(df["origin"].dropna().unique()) if has_origin
               else sorted(df[win_col].dropna().unique()) if win_col else [])

    if not origins:
        empty_state.empty(
            "No forecast windows found",
            "The predictions file loaded but contains no window or origin "
            "values to select.")
        return

    c1, c2 = st.columns([2, 1], gap="medium")
    with c1:
        def _fmt(o):
            if has_origin:
                return f"{pd.Timestamp(o):%d %b %Y, %H:%M} UTC"
            return f"Window {o}"
        origin = st.selectbox("Forecast window", origins,
                              index=len(origins) - 1, format_func=_fmt,
                              key="fc_origin")
    with c2:
        model = st.selectbox("Model", loaders.sorted_models(df),
                             key="fc_model")

    sel_col = "origin" if has_origin else win_col
    window = df[(df[sel_col] == origin) &
                (df[model_col].astype(str) == model)]
    if "horizon" in window.columns:
        window = window.sort_values("horizon")
    elif "timestamp" in window.columns:
        window = window.sort_values("timestamp")

    if window.empty:
        empty_state.empty(
            "No forecast for this combination",
            f"{model} has no stored predictions for the selected window. "
            "Try another window or model.")
        return

    has_actual = "actual" in window.columns and window["actual"].notna().any()

    if "horizon" in window.columns:
        peak_row = window.loc[window["prediction"].idxmax()]
        peak_hour = (f"{pd.Timestamp(peak_row['timestamp']):%H:%M} UTC"
                     if "timestamp" in window.columns else "\u2014")
        peak_sub = f"{int(peak_row['horizon'])} hours ahead"
    else:
        peak_hour, peak_sub = "\u2014", ""

    kpi.kpi_row([
        {"label": "Peak forecast demand",
         "value": fmt.energy(float(window["prediction"].max()), 2),
         "accent": "amber"},
        {"label": "Peak hour", "value": peak_hour, "sub": peak_sub},
        {"label": "Average forecast demand",
         "value": fmt.energy(float(window["prediction"].mean()), 2)},
        {"label": "Forecast energy",
         "value": fmt.energy(float(window["prediction"].sum()), 1)},
    ])

    st.markdown("")
    if "horizon" in window.columns and has_actual:
        fig = charts.forecast_window(
            window, title=f"{model} \u2014 {_fmt(origin)}")
    else:
        fig = charts.actual_vs_predicted(
            window, title=f"{model} \u2014 {_fmt(origin)}")
    st.plotly_chart(fig, **ui.STRETCH)

    if has_actual:
        err = window["prediction"] - window["actual"]
        kpi.kpi_row([
            {"label": "Observed energy",
             "value": fmt.energy(float(window["actual"].sum()), 1),
             "accent": "cyan"},
            {"label": "Observed peak",
             "value": fmt.energy(float(window["actual"].max()), 2)},
            {"label": "MAE, this window",
             "value": f"{float(np.abs(err).mean()):.4f} kWh"},
            {"label": "RMSE, this window",
             "value": f"{float(np.sqrt((err ** 2).mean())):.4f} kWh"},
        ])
        kpi.caption(
            "Window-level errors come from the stored values for this window "
            "only. They are not comparable with the pooled test metrics on "
            "the Model comparison page."
        )

    with st.expander("Hourly detail"):
        table = window.copy()
        if "timestamp" in table.columns:
            table["timestamp"] = table["timestamp"].dt.strftime(
                "%d %b %Y %H:%M")
        keep = [c for c in ("horizon", "timestamp", "actual", "prediction")
                if c in table.columns]
        st.dataframe(table[keep].rename(columns={
            "horizon": "Hours ahead", "timestamp": "Target hour (UTC)",
            "actual": "Observed (kWh)", "prediction": "Forecast (kWh)",
        }), **ui.TABLE, hide_index=True)
