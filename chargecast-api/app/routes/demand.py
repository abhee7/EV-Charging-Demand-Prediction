"""Demand analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app import config
from app.services import demand_service

router = APIRouter(prefix="/demand", tags=["demand"])


@router.get("/summary", summary="Demand summary statistics")
def summary() -> dict:
    return demand_service.summary()


@router.get("/hourly", summary="Hourly demand series (demand ribbon)")
def hourly(
    downsample: int = Query(1, ge=1, le=24,
                            description="Keep every Nth observation."),
    limit: int | None = Query(None, ge=1, le=20000,
                              description="Return only the last N points."),
) -> dict:
    return demand_service.hourly(downsample=downsample, limit=limit)


@router.get("/profile", summary="Mean demand by hour of day")
def profile() -> dict:
    return demand_service.profile()


@router.get("/weekday", summary="Weekday against weekend by hour")
def weekday() -> dict:
    return demand_service.weekday()


@router.get("/monthly", summary="Demand by calendar month")
def monthly() -> dict:
    return demand_service.monthly()


@router.get("/heatmap", summary="Hour by day-of-week demand surface")
def heatmap() -> dict:
    return demand_service.heatmap()


@router.get("/distribution", summary="Demand distribution with percentiles")
def distribution(bins: int = Query(48, ge=8, le=200)) -> dict:
    return demand_service.distribution(bins=bins)


@router.get("/acf", summary="Autocorrelation of hourly demand")
def acf(
    max_lag: int = Query(336, ge=1, le=1000),
    lag: int | None = Query(None, ge=1, le=1000,
                            description="Highlight a specific lag."),
) -> dict:
    return demand_service.autocorrelation(max_lag=max_lag, lag=lag)


@router.get("/scenario", summary="Arithmetic demand scenario")
def scenario(
    change: float = Query(0, ge=-20, le=50,
                          description="Percentage change applied to demand."),
) -> dict:
    return demand_service.scenario(change)


@router.get("/capacity", summary="Indicative sizing pressure")
def capacity(
    capacity_kw: int = Query(120, description="Nominal charger capacity."),
) -> dict:
    if capacity_kw not in config.CAPACITY_OPTIONS:
        return {"available": False,
                "reason": f"capacity_kw must be one of "
                          f"{config.CAPACITY_OPTIONS}",
                "path": "data/processed/hourly_demand.csv"}
    return demand_service.capacity(capacity_kw)
