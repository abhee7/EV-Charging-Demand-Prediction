"""Overview aggregate for the command-centre page."""

from __future__ import annotations

from fastapi import APIRouter

from app import config
from app.services import artifact_loader as al
from app.services import demand_service, forecast_service, stats
from app.utils import columns as cols

router = APIRouter(tags=["overview"])


@router.get("/overview", summary="Command-centre summary")
def overview() -> dict:
    summary = demand_service.summary()

    acf_highlights = []
    demand = al.load("hourly_demand")
    if demand:
        series = demand.frame.sort_values("timestamp")["demand_kWh"]
        for lag, label in ((1, "Lag 1"), (24, "Daily"), (168, "Weekly")):
            value = stats.acf_at(series, lag)
            if value is not None:
                acf_highlights.append({"lag": lag, "label": label,
                                       "value": value})

    predictions = al.load("test_predictions")
    forecast_meta = {"available": False}
    if predictions:
        frame = predictions.frame
        model_col = cols.model_column(frame)
        windows = forecast_service.windows("primary")
        forecast_meta = {
            "available": True,
            "models": (sorted(frame[model_col].astype(str).unique())
                       if model_col else []),
            "windowCount": windows.get("count", 0),
            "latestWindow": (windows["windows"][-1]
                             if windows.get("windows") else None),
            "horizonHours": config.FORECAST_HORIZON_HOURS,
        }

    return {
        "dataset": config.DATASET_NAME,
        "unit": config.UNIT,
        "demand": summary,
        "temporalSignals": acf_highlights,
        "forecast": forecast_meta,
        "targetLimitation": config.TARGET_LIMITATION,
    }
