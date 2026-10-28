"""Overview — dataset status, demand summary, model snapshot."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from components import charts, empty_state, kpi, metric_table
from core import formatting as fmt
from core import loaders
from core import ui


def _combined_test_metrics():
    """Primary ML metrics plus the active time-series comparator."""
    primary = loaders.load("test_metrics")
    sarimax = loaders.load("sarimax_test_metrics")
    frames = [ds.df for ds in (primary, sarimax) if ds]
    if not frames:
        return None, primary
    combined = pd.concat(frames, ignore_index=True)
    return combined, primary


def render() -> None:
    st.markdown("## Charging demand at a glance")

    demand = loaders.load("hourly_demand")
    preds = loaders.load("test_predictions")
    combined, primary = _combined_test_metrics()

    # ---------------- Dataset status ----------------
    if demand:
        df = demand.df
        total = float(df["demand_kWh"].sum())
        mean = float(df["demand_kWh"].mean())
        peak = float(df["demand_kWh"].max())
        peak_row = df.loc[df["demand_kWh"].idxmax()]
        zero_share = float((df["demand_kWh"] <= 0).mean() * 100)

        kpi.kpi_row([
            {"label": "Energy analysed", "value": fmt.energy(total, 0),
             "sub": f"{len(df):,} hourly observations", "accent": "cyan"},
            {"label": "Average hourly demand", "value": fmt.energy(mean, 2)},
            {"label": "Peak hourly demand", "value": fmt.energy(peak, 1),
             "sub": f"{peak_row['timestamp']:%d %b %Y, %H:%M} local",
             "accent": "amber"},
            {"label": "Forecast horizon",
             "value": f"{config.FORECAST_HORIZON_HOURS} hours",
             "sub": "Day-ahead, recursive"},
        ])

        st.markdown("")
        st.plotly_chart(
            charts.demand_ribbon(df["timestamp"], df["demand_kWh"],
                                 title="Hourly demand across the study period"),
            **ui.STRETCH,
        )
        kpi.caption(
            f"Coverage {fmt.day_range(df['timestamp'])} (America/Los_Angeles). "
            f"{zero_share:.1f}% of hours record zero demand, which is why "
            "sMAPE and MASE are reported rather than MAPE."
        )
    else:
        empty_state.from_dataset(demand)

    # ---------------- Model snapshot ----------------
    st.markdown("### Test performance")
    if combined is not None:
        model_col = loaders.model_column(combined)
        metrics = loaders.resolve_metrics(combined)
        names = loaders.sorted_models(combined)
        cols = st.columns(min(len(names), 3) or 1, gap="small")
        for i, name in enumerate(names):
            row = combined[combined[model_col].astype(str) == name].iloc[0]
            values = {canon: row.get(col) for canon, col in metrics.items()}
            with cols[i % len(cols)]:
                kpi.model_card(name, values, loaders.model_color(name, i),
                               keys=["MAE", "RMSE", "R2", "MASE"])
        st.markdown("")
        kpi.note(config.DM_STATEMENT, label="On the two closest models.")
        metric_table.metric_definitions()
    else:
        empty_state.from_dataset(primary)

    # ---------------- Observed vs predicted ----------------
    st.markdown("### Observed and forecast demand over the test period")
    if preds:
        pdf = preds.df
        model_col = loaders.model_column(pdf)
        names = loaders.sorted_models(pdf)
        choice = st.selectbox("Model", names, key="ov_model")
        sub = pdf[pdf[model_col].astype(str) == choice].sort_values("timestamp")
        st.plotly_chart(charts.actual_vs_predicted(sub), **ui.STRETCH)
        kpi.caption(
            f"{len(sub):,} forecast hours across "
            f"{sub['origin'].nunique():,} forecast origins. Observed in cyan, "
            "forecast in amber. Timestamps are UTC."
        )
    else:
        empty_state.from_dataset(preds)

    # ---------------- Research context ----------------
    st.markdown("### Research context")
    kpi.caption(
        "Day-ahead forecasting of hourly EV charging demand at the Caltech "
        "ACN site. Four feature-based models are compared against a seasonal "
        "naive benchmark and a SARIMAX specification with Fourier terms, on a "
        "chronological split with no shuffling."
    )
    kpi.note(config.TARGET_LIMITATION, label="Target construction.")
