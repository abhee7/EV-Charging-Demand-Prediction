"""Research-integrity tests.

These inspect the actual repository rather than asserting hard-coded research
values. When an artefact is absent the relevant test skips rather than
passing vacuously, so a green run against a real repository means the file
was genuinely read.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parent.parent
APP_DIR = API_DIR / "app"


# ---------------- Registration ----------------
def test_audited_artifacts_registered():
    from app.services import artifact_loader as al
    for key in ("dm_tests", "peak_model_detection", "peak_thresholds"):
        assert key in al.SPECS, f"{key} is not registered"
        assert al.SPECS[key].group == "audited"


def test_audited_specs_assert_no_uninspected_schema():
    """Audited artefacts must not assert columns this service never saw."""
    from app.services import artifact_loader as al
    for key, spec in al.SPECS.items():
        if spec.group == "audited":
            assert spec.required == (), (
                f"{key} asserts columns {spec.required} that were never "
                "inspected; resolve them at runtime instead")


def test_audited_paths_match_the_verified_filenames():
    from app.services import artifact_loader as al
    assert al.SPECS["dm_tests"].relative == \
        "results/metrics/diebold_mariano_tests.csv"
    assert al.SPECS["peak_model_detection"].relative == \
        "results/peak_analysis/model_peak_detection.csv"
    assert al.SPECS["peak_thresholds"].relative == \
        "results/peak_analysis/high_demand_thresholds.csv"


# ---------------- Real artefact reading ----------------
def _require(key):
    from app.services import artifact_loader as al
    art = al.load(key)
    if not art.available:
        pytest.skip(f"{al.SPECS[key].relative} not present in this repository")
    return art


def test_dm_artifact_is_actually_read(client):
    art = _require("dm_tests")
    assert len(art.frame) > 0
    body = client.get("/api/models/dm/audited").json()
    assert body["available"] is True
    assert body["source"] == "results/metrics/diebold_mariano_tests.csv"
    assert body["columns"] == [str(c) for c in art.frame.columns]
    assert len(body["comparisons"]) == len(art.frame)
    assert body["provenance"] == "VERIFIED RESEARCH ARTIFACT"


def test_dm_values_come_from_the_file_not_from_source(client):
    """Served values must equal the file's values, cell for cell."""
    art = _require("dm_tests")
    from app.utils import columns as cols
    res = cols.resolve(art.frame, cols.DM_FIELDS, numeric=cols.DM_NUMERIC)
    stat_col = res.get("statistic")
    if stat_col is None:
        pytest.skip("no statistic column resolved in this artefact")

    served = client.get("/api/models/dm/audited").json()["comparisons"]
    expected = [float(v) for v in art.frame[stat_col]]
    actual = [c["statistic"] for c in served]
    assert actual == pytest.approx(expected)


def test_peak_detection_artifact_is_actually_read(client):
    art = _require("peak_model_detection")
    body = client.get("/api/peak/audited").json()
    assert body["available"] is True
    assert body["source"] == "results/peak_analysis/model_peak_detection.csv"
    assert body["columns"] == [str(c) for c in art.frame.columns]
    assert len(body["models"]) == len(art.frame)


def test_peak_thresholds_artifact_is_actually_read(client):
    art = _require("peak_thresholds")
    body = client.get("/api/peak/thresholds").json()
    assert body["available"] is True
    assert body["source"] == \
        "results/peak_analysis/high_demand_thresholds.csv"
    assert body["columns"] == [str(c) for c in art.frame.columns]


# ---------------- Audited vs interactive separation ----------------
def test_audited_and_interactive_are_separate_endpoints(client):
    spec = client.get("/openapi.json").json()["paths"]
    assert "/api/models/dm/audited" in spec
    assert "/api/models/dm/interactive" in spec
    assert "/api/peak/audited" in spec
    assert "/api/peak/interactive" in spec


def test_interactive_results_are_labelled_exploratory(client):
    body = client.get("/api/peak/interactive?percentile=95").json()
    if not body.get("available"):
        pytest.skip("predictions not present")
    assert "EXPLORATORY" in body["provenance"]
    assert body["differsFromAudited"] is True
    assert "differs from audited" in body["thresholdNotice"].lower()


def test_interactive_default_matches_audited_percentile(client):
    from app import config
    body = client.get("/api/peak/interactive").json()
    if not body.get("available"):
        pytest.skip("predictions not present")
    assert body["percentile"] == config.PEAK_PERCENTILE == 90
    assert body["differsFromAudited"] is False


def test_interactive_does_not_mutate_the_audited_response(client):
    before = client.get("/api/models/dm/audited").json()
    client.get("/api/models/dm/interactive"
               "?model_a=Random%20Forest&model_b=XGBoost&hac_lag=5")
    after = client.get("/api/models/dm/audited").json()
    assert before == after


# ---------------- Read-only and no fabrication ----------------
def test_no_write_operations_in_source():
    pattern = re.compile(
        r"\b(to_csv|to_excel|to_parquet|savefig|rmtree|os\.remove|"
        r"\.unlink\(|shutil\.)")
    offenders = [p.name for p in APP_DIR.rglob("*.py")
                 if pattern.search(p.read_text(encoding="utf-8"))]
    assert not offenders, offenders


def test_no_fabricated_data_sources_in_source():
    pattern = re.compile(r"(np\.random|numpy\.random|\brandom\.|\bfaker\b|"
                         r"\bdummy\b|\bmock_data\b)")
    offenders = [p.name for p in APP_DIR.rglob("*.py")
                 if pattern.search(p.read_text(encoding="utf-8"))]
    assert not offenders, offenders


def test_no_research_values_hard_coded_in_source():
    forbidden = ("0.239843", "0.8104517", "6.383066", "6.492867",
                 "11.056872", "12.424506", "136.3581", "155616",
                 "0.6504", "0.7407", "0.6926")
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.name}:{token}")
    assert not offenders, offenders


def test_repository_files_unchanged_by_requests(client, repo_root):
    """Exercise the API, then confirm no artefact changed on disk."""
    import hashlib

    def digest() -> str:
        h = hashlib.sha256()
        for folder in ("data", "results"):
            base = repo_root / folder
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if f.is_file():
                    h.update(f.name.encode())
                    h.update(str(f.stat().st_size).encode())
                    h.update(str(f.stat().st_mtime_ns).encode())
        return h.hexdigest()

    before = digest()
    for path in ("/api/overview", "/api/demand/hourly", "/api/models/metrics",
                 "/api/models/dm/audited", "/api/peak/audited",
                 "/api/peak/interactive", "/api/robustness/metrics",
                 "/api/research/artifacts"):
        client.get(path)
    assert digest() == before, "a request modified data/ or results/"


# ---------------- Neutrality ----------------
def test_no_ranking_language_in_api_source():
    banned = (r"\bbest[- ]model\b", r"\bwinner\b", r"\bchampion\b",
              r"\btop\s+model\b", r"\bsuperior\s+model\b",
              r"\bmost\s+accurate\b", r"\bhighest[- ]performing\b",
              r"\bstrongest\s+model\b", r"\bweakest\s+model\b")
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for pattern in banned:
            match = re.search(pattern, text)
            if match:
                offenders.append(f"{path.name}:{match.group(0)}")
    assert not offenders, offenders


def test_legacy_sarima_is_quarantined(client):
    body = client.get("/api/research/provenance").json()
    legacy = [r for r in body["rows"] if "Legacy" in r["result"]]
    assert legacy, "legacy SARIMA must be listed explicitly"
    assert legacy[0]["status"] in ("quarantined", "absent")

    metrics = client.get("/api/models/metrics").json()
    if metrics.get("available"):
        names = " ".join(m["model"] for m in metrics["models"]).lower()
        assert "sarima" not in names or "sarimax" in names, \
            "legacy SARIMA must not appear in the active metric set"
