"""Explainability endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import explainability_service as svc

router = APIRouter(prefix="/explainability", tags=["explainability"])

SOURCE_PATTERN = "^(shap|importance)$"


@router.get("/shap", summary="Combined SHAP importance")
def shap() -> dict:
    return svc.combined_shap()


@router.get("/random-forest", summary="Random Forest attribution")
def random_forest(
    source: str = Query("shap", pattern=SOURCE_PATTERN),
) -> dict:
    return svc.model_view("random-forest", source)


@router.get("/xgboost", summary="XGBoost attribution")
def xgboost(
    source: str = Query("shap", pattern=SOURCE_PATTERN),
) -> dict:
    return svc.model_view("xgboost", source)
