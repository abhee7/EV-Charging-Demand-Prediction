"""ChargeCast API.

A read-only HTTP layer over the verified research outputs of
EV-Charging-Demand-Prediction.

The API opens files in data/ and results/ for reading only. It never writes,
retrains, regenerates or modifies any research artefact, and no endpoint
accepts a filesystem path from the caller: artefacts are addressed by key
through a fixed registry in services/artifact_loader.py.

Run:
    cd chargecast-api
    python -m uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.routes import (demand, explainability, forecast, health, models,
                        overview, peak, research, robustness)

log = logging.getLogger("chargecast")

DESCRIPTION = """
Read-only API over the verified research outputs of
*A Comparative Study of Machine Learning and Time-Series Approaches for EV
Charging Demand Prediction*.

**Research integrity**

* No endpoint writes to `data/` or `results/`.
* No model is loaded, fitted or retrained.
* Audited artefacts are served as stored. Where the dashboard also offers an
  interactive recomputation, the two are separate endpoints and the
  exploratory one is labelled as such.
* A missing artefact returns a structured `available: false` payload rather
  than an error page or fabricated values.
"""

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description=DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

for router in (health.router, overview.router, demand.router,
               forecast.router, models.router, peak.router,
               explainability.router, robustness.router, research.router):
    app.include_router(router, prefix="/api")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    """Clean error response; never leaks a traceback or environment detail."""
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"available": False,
                 "reason": "Internal error while reading research artefacts",
                 "path": request.url.path},
    )


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"service": config.APP_NAME, "version": config.APP_VERSION,
            "docs": "/docs", "health": "/api/health"}
