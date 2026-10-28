# ChargeCast API

Read-only FastAPI layer over the verified research outputs of
*A Comparative Study of Machine Learning and Time-Series Approaches for EV
Charging Demand Prediction*.

## Research integrity

* No endpoint writes to `data/` or `results/`. The test suite asserts this by
  hashing both trees before and after exercising the API.
* No model is loaded, fitted, retrained or regenerated.
* No endpoint accepts a filesystem path from the caller. Artefacts are
  addressed by key through a fixed registry in
  `app/services/artifact_loader.py`.
* Audited artefacts are served as stored. Where the dashboard also offers an
  in-memory recomputation, the two live on separate endpoints and the
  exploratory one is labelled in its payload.
* A missing artefact returns `{"available": false, "reason": ..., "path": ...}`
  with the expected and detected columns, never a fabricated value.

## Run

```bash
cd chargecast-api
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs> · OpenAPI: `/openapi.json`

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `CHARGECAST_ROOT` | parent of `chargecast-api/` | Repository root holding `data/` and `results/` |
| `CHARGECAST_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins |

Copy `.env.example` and adjust. No absolute path is baked into application
logic.

## Tests

```bash
cd chargecast-api
python -m pytest tests/ -q
```

`tests/test_api.py` covers the endpoint contract, parameter validation and the
structured unavailable payload. `tests/test_research_integrity.py` inspects the
actual repository: it asserts that the audited CSVs are genuinely read, that
served values equal the file's values cell for cell, that audited and
interactive results are separate, and that no research value is hard-coded in
source. Tests that need an artefact skip when it is absent rather than passing
vacuously.

## Layout

```
app/
├── main.py                 FastAPI app, CORS, error handler
├── config.py               paths, palette-independent constants, research wording
├── schemas.py              Pydantic response models
├── routes/                 one module per endpoint group
│   ├── health.py  overview.py  demand.py  forecast.py
│   └── models.py  peak.py  explainability.py  robustness.py  research.py
├── services/               all data access and computation
│   ├── artifact_loader.py  the only place a CSV is opened; caching, registry
│   ├── stats.py            Diebold-Mariano, peak scoring, ACF, summaries
│   ├── demand_service.py   metrics_service.py   forecast_service.py
│   └── peak_service.py     explainability_service.py  robustness_service.py
│                           research_service.py
└── utils/
    └── columns.py          runtime column resolution
```

## Schema adaptation

Some audited artefacts had no inspected header when this service was written.
Their `ArtifactSpec` entries declare **no required columns**, and the services
resolve columns at request time in `app/utils/columns.py` against candidate
spellings. Every audited endpoint also returns the stored table under `rows`
with its `columns`, so nothing in an artefact is hidden by a failed resolution,
and an unresolved field is reported in `absentFields` rather than invented.

Metric headers are resolved the same way: `sMAPE_percent`, `sMAPE`, `SMAPE` and
`smape_percent` all map to the canonical `smape` key.

## Caching

`artifact_loader` caches parsed frames on `(path, mtime, size)`. Rerunning a
research script is picked up on the next request without restarting the API,
and repeated requests never reparse a CSV.
