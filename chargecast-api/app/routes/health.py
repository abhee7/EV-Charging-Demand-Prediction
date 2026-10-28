"""Health and service status."""

from __future__ import annotations

from fastapi import APIRouter

from app import config, schemas
from app.services import artifact_loader as al

router = APIRouter(tags=["health"])


@router.get("/health", response_model=schemas.Health,
            summary="Service and artefact health")
def health() -> schemas.Health:
    root = config.repo_root()
    available = sum(1 for key in al.SPECS if al.load(key).available)
    return schemas.Health(
        service=config.APP_NAME,
        version=config.APP_VERSION,
        repositoryRoot=str(root),
        repositoryExists=root.exists(),
        artifactsAvailable=available,
        artifactsTotal=len(al.SPECS),
    )
