# ChargeCast 3.0

React + FastAPI presentation layer for the EV charging demand forecasting
study. The existing Streamlit dashboard in `chargecast/` is untouched and
continues to work; these two services coexist with it over the same verified
artefacts.

```bash
# Backend  → http://localhost:8000  (docs at /docs)
cd chargecast-api
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend → http://localhost:5173
cd chargecast-web
npm install
npm run dev
```

Set `CHARGECAST_ROOT` if the repository root is not the parent of
`chargecast-api/`. Set `VITE_API_URL` in `chargecast-web/.env.local` if the API
is not on port 8000.

## Verify

```bash
cd chargecast-api && python -m pytest tests/ -q     # backend suite
cd chargecast-web && npm run lint && npm run build  # lint + typecheck + build
python scripts/smoke_test.py --with-frontend        # both services, HTTP 200
```

## Read this first

`CHARGECAST_REACT_ARCHITECTURE.md` documents the architecture, every endpoint,
the artefact mapping, the research-integrity rules and deployment.

## Research integrity in one paragraph

The API is read-only: it never writes to `data/` or `results/`, never retrains
anything, and accepts no filesystem path from the caller. Audited artefacts
(the Diebold-Mariano tests and the peak-analysis outputs) are served as stored
and clearly separated from the in-dashboard recomputations, which are labelled
exploratory. Missing artefacts produce a structured empty state naming the
expected path — never a fabricated chart. No model is described as best,
winner or superior anywhere, and the legacy SARIMA file stays quarantined.
