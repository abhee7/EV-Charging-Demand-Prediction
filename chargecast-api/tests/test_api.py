"""API contract tests.

These pass whether or not the research artefacts are present: with artefacts
missing they assert the structured unavailable contract instead.
"""

from __future__ import annotations

import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["readOnly"] is True
    assert body["artifactsTotal"] > 0
    assert "repositoryRoot" in body


def test_root(client):
    assert client.get("/").status_code == 200


def test_openapi_lists_every_documented_endpoint(client):
    spec = client.get("/openapi.json").json()
    required = [
        "/api/health", "/api/overview",
        "/api/demand/hourly", "/api/demand/profile", "/api/demand/weekday",
        "/api/demand/monthly", "/api/demand/heatmap",
        "/api/demand/distribution", "/api/demand/acf",
        "/api/forecast/windows", "/api/forecast/{window_id}",
        "/api/forecast/models",
        "/api/models/metrics", "/api/models/horizon",
        "/api/models/dm/audited", "/api/models/dm/interactive",
        "/api/peak/audited", "/api/peak/thresholds", "/api/peak/interactive",
        "/api/explainability/shap", "/api/explainability/random-forest",
        "/api/explainability/xgboost",
        "/api/robustness/summary", "/api/robustness/metrics",
        "/api/robustness/horizon",
        "/api/research/artifacts", "/api/research/provenance",
    ]
    missing = [p for p in required if p not in spec["paths"]]
    assert not missing, f"undocumented endpoints: {missing}"


@pytest.mark.parametrize("path", [
    "/api/overview",
    "/api/demand/summary", "/api/demand/hourly", "/api/demand/profile",
    "/api/demand/weekday", "/api/demand/monthly", "/api/demand/heatmap",
    "/api/demand/distribution", "/api/demand/acf", "/api/demand/scenario",
    "/api/forecast/models", "/api/forecast/windows",
    "/api/models/metrics", "/api/models/validation", "/api/models/horizon",
    "/api/models/dm/audited",
    "/api/peak/audited", "/api/peak/thresholds", "/api/peak/supplementary",
    "/api/explainability/shap", "/api/explainability/random-forest",
    "/api/explainability/xgboost",
    "/api/robustness/summary", "/api/robustness/metrics",
    "/api/robustness/horizon",
    "/api/research/artifacts", "/api/research/provenance",
])
def test_endpoint_returns_200_and_json(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), dict)


def test_missing_artifact_contract(client):
    """A missing artefact returns a structured payload, never a 500."""
    r = client.get("/api/peak/thresholds")
    assert r.status_code == 200
    body = r.json()
    if body.get("available") is False:
        assert body["reason"]
        assert body["path"].startswith("results/")
        assert "fabricated" not in str(body).lower()


def test_metrics_ordering_is_not_by_performance(client):
    body = client.get("/api/models/metrics").json()
    if not body.get("available"):
        pytest.skip("metrics artefact not present")
    names = [m["model"] for m in body["models"]]
    assert names == sorted(names, key=str.lower), \
        "models must default to alphabetical order, not metric order"
    assert body["defaultOrder"] == "model-name"


# ---------------- Parameter validation ----------------
@pytest.mark.parametrize("path,status", [
    ("/api/demand/hourly?downsample=0", 422),
    ("/api/demand/hourly?downsample=999", 422),
    ("/api/demand/distribution?bins=1", 422),
    ("/api/demand/acf?max_lag=0", 422),
    ("/api/demand/scenario?change=-90", 422),
    ("/api/demand/scenario?change=500", 422),
    ("/api/forecast/windows?prediction_set=bogus", 422),
    ("/api/forecast/0?model=X", 422),
    ("/api/models/dm/interactive?model_a=A&model_b=B&hac_lag=-1", 422),
    ("/api/models/dm/interactive?model_a=A&model_b=B&hac_lag=999", 422),
    ("/api/explainability/random-forest?source=bogus", 422),
])
def test_invalid_parameters_rejected(client, path, status):
    assert client.get(path).status_code == status


def test_dm_interactive_requires_both_models(client):
    assert client.get("/api/models/dm/interactive?model_a=X").status_code == 422


def test_peak_percentile_validated(client):
    body = client.get("/api/peak/interactive?percentile=42").json()
    assert body["available"] is False
    assert "percentile" in body["reason"]


def test_capacity_validated(client):
    body = client.get("/api/demand/capacity?capacity_kw=77").json()
    assert body["available"] is False


def test_unknown_model_is_reported_not_guessed(client):
    """An unknown model name is rejected, never silently substituted."""
    body = client.get(
        "/api/models/dm/interactive"
        "?model_a=NotAModel&model_b=AlsoNot&hac_lag=23").json()
    assert body["available"] is False
    assert body["reason"]
    # With predictions present the rejection names the unknown model; without
    # them the artefact-missing contract applies instead.
    if "availableModels" in body:
        assert "Unknown model" in body["reason"]
    else:
        assert "not found" in body["reason"].lower()


def test_no_arbitrary_path_parameter(client):
    """No endpoint accepts a filesystem path from the caller."""
    spec = client.get("/openapi.json").json()
    suspicious = []
    for path, methods in spec["paths"].items():
        for method in methods.values():
            for param in method.get("parameters", []):
                if param["name"].lower() in ("path", "file", "filename",
                                             "filepath", "csv"):
                    suspicious.append(f"{path}:{param['name']}")
    assert not suspicious, suspicious
