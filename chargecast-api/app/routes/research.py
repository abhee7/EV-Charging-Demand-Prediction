"""Research provenance and artefact status."""

from __future__ import annotations

from fastapi import APIRouter

from app.services import research_service as svc

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/artifacts", summary="Live status of every expected artefact")
def artifacts() -> dict:
    return svc.artifacts()


@router.get("/provenance", summary="Study description and result provenance")
def provenance() -> dict:
    return svc.provenance()
