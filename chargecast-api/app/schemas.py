"""Pydantic response models.

Applied where the shape is stable. Endpoints that surface audited artefacts
whose schema has not been inspected return validated envelopes with an
open payload, so a real column is never dropped because a model did not
anticipate it.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    repositoryRoot: str
    repositoryExists: bool
    artifactsAvailable: int
    artifactsTotal: int
    readOnly: bool = True


class Unavailable(BaseModel):
    """Structured response for a missing or unreadable artefact."""
    available: Literal[False] = False
    reason: str
    path: str
    label: str | None = None
    producedBy: str | None = None
    detail: str | None = None
    expectedColumns: list[str] = Field(default_factory=list)
    detectedColumns: list[str] = Field(default_factory=list)
    missingColumns: list[str] = Field(default_factory=list)


class ModelMetric(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())
    model: str
    mae: float | None = None
    rmse: float | None = None
    r2: float | None = None
    smape: float | None = None
    mase: float | None = None


class MetricDescriptor(BaseModel):
    key: str
    label: str
    unit: str
    lowerIsBetter: bool


class MetricsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    available: bool
    models: list[ModelMetric] = Field(default_factory=list)
    metrics: list[MetricDescriptor] = Field(default_factory=list)
    defaultOrder: str | None = None
    orderingNote: str | None = None
    selectedMetric: str | None = None
    sources: list[str] = Field(default_factory=list)


class DemandSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    available: bool
    observations: int | None = None
    totalKwh: float | None = None
    mean: float | None = None
    median: float | None = None
    maximum: float | None = None
    zeroHours: int | None = None
    p90: float | None = None
    p95: float | None = None
    p99: float | None = None
    peakOverAverage: float | None = None
    unit: str | None = None


class DMInteractive(BaseModel):
    model_config = ConfigDict(extra="allow")
    available: bool
    modelA: str | None = None
    modelB: str | None = None
    statistic: float | None = None
    pValue: float | None = None
    observations: int | None = None
    hacLag: int | None = None
    loss: str | None = None
    significantAt5Pct: bool | None = None
    provenance: str | None = None
    note: str | None = None


class PeakModelRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None


class Envelope(BaseModel):
    """Open envelope for audited artefacts with uninspected schemas."""
    model_config = ConfigDict(extra="allow")
    available: bool
    source: str | None = None
    note: str | None = None
    provenance: str | None = None


AnyPayload = dict[str, Any]
