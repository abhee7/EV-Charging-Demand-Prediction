"""Robustness endpoints for the two target constructions."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import robustness_service as svc

router = APIRouter(prefix="/robustness", tags=["robustness"])


@router.get("/summary", summary="Series facts for both target constructions")
def summary() -> dict:
    return svc.summary()


@router.get("/metrics", summary="Model metrics under both constructions")
def metrics() -> dict:
    return svc.metrics()


@router.get("/horizon", summary="Horizon curves under both constructions")
def horizon(metric: str = Query("mae", max_length=20)) -> dict:
    return svc.horizon(metric)
