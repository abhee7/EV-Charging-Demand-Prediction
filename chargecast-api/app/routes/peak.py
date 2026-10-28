"""Peak analysis endpoints: audited artefacts and exploratory recomputation."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app import config
from app.services import peak_service

router = APIRouter(prefix="/peak", tags=["peak"])


@router.get("/audited", summary="Audited peak detection artefact")
def audited() -> dict:
    return peak_service.audited()


@router.get("/thresholds", summary="Audited high-demand thresholds")
def thresholds() -> dict:
    return peak_service.thresholds()


@router.get("/supplementary", summary="Further audited peak outputs")
def supplementary() -> dict:
    return {"available": True, "datasets": peak_service.supplementary()}


@router.get("/interactive", summary="Exploratory peak recomputation")
def interactive(
    percentile: int = Query(config.PEAK_PERCENTILE,
                            description="One of 75, 90, 95, 99."),
    model: str | None = Query(None, max_length=120),
) -> dict:
    if percentile not in config.PEAK_PERCENTILE_OPTIONS:
        return {"available": False,
                "reason": f"percentile must be one of "
                          f"{config.PEAK_PERCENTILE_OPTIONS}",
                "path": "results/predictions/test_predictions_corrected.csv"}
    return peak_service.interactive(percentile, model)
