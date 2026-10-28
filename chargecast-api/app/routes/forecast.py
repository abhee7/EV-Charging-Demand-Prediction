"""Forecast replay endpoints. Read-only; no inference is performed."""

from __future__ import annotations

from fastapi import APIRouter, Path, Query

from app.services import forecast_service

router = APIRouter(prefix="/forecast", tags=["forecast"])

SET_PATTERN = "^(primary|sarimax|arrival)$"


@router.get("/models", summary="Models with stored predictions")
def models(
    prediction_set: str = Query("primary", pattern=SET_PATTERN),
) -> dict:
    return forecast_service.models(prediction_set)


@router.get("/windows", summary="Stored forecast windows")
def windows(
    prediction_set: str = Query("primary", pattern=SET_PATTERN),
    model: str | None = Query(None, max_length=120),
) -> dict:
    return forecast_service.windows(prediction_set, model)


@router.get("/{window_id}", summary="One stored 24-hour forecast window")
def window(
    window_id: int = Path(..., ge=1, le=100000),
    model: str = Query(..., min_length=1, max_length=120),
    prediction_set: str = Query("primary", pattern=SET_PATTERN),
    horizon: int | None = Query(None, ge=1, le=168),
) -> dict:
    return forecast_service.window(window_id, model, prediction_set, horizon)
