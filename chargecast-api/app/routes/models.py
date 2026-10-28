"""Model metrics, horizon curves and Diebold-Mariano endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app import config, schemas
from app.services import metrics_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/metrics", response_model=schemas.MetricsResponse,
            summary="Test metrics for every model")
def metrics(
    metric: str | None = Query(
        None, max_length=20,
        description="Optional metric key: mae, rmse, r2, smape, mase."),
) -> dict:
    return metrics_service.metrics(metric)


@router.get("/validation", summary="Validation metrics")
def validation() -> dict:
    return metrics_service.validation()


@router.get("/horizon", summary="Error by forecast horizon")
def horizon(
    metric: str = Query("mae", max_length=20),
) -> dict:
    return metrics_service.horizon(metric)


@router.get("/dm/audited", summary="Audited Diebold-Mariano artefact")
def dm_audited() -> dict:
    """The authoritative statistical result, read from the stored CSV."""
    return metrics_service.dm_audited()


@router.get("/dm/interactive", response_model=schemas.DMInteractive,
            summary="Exploratory Diebold-Mariano recomputation")
def dm_interactive(
    model_a: str = Query(..., min_length=1, max_length=120),
    model_b: str = Query(..., min_length=1, max_length=120),
    hac_lag: int = Query(config.DM_HAC_LAG, ge=0, le=72),
) -> dict:
    """Recomputed from stored predictions. Never replaces the audited result."""
    return metrics_service.dm_interactive(model_a, model_b, hac_lag)
