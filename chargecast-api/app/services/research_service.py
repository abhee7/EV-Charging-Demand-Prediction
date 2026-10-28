"""Artefact status and research provenance."""

from __future__ import annotations

from app import config
from app.services import artifact_loader as al

GROUP_LABELS = {
    "data": "Data",
    "primary": "Primary",
    "audited": "Audited research output",
    "sarimax": "SARIMAX + Fourier",
    "explain": "Explainability",
    "robustness": "Robustness",
    "legacy": "Superseded / legacy",
}

PROVENANCE_CHECKS = [
    ("Primary metrics", "test_metrics",
     "The reported model metrics, read from the research pipeline."),
    ("Forecast predictions", "test_predictions",
     "Stored test-period predictions, replayed by the Forecast page."),
    ("DM tests", "dm_tests",
     "The authoritative statistical result. The interactive explorer "
     "recomputes from stored predictions and is exploratory only."),
    ("Peak analysis", "peak_model_detection",
     "The authoritative peak result. The percentile explorer beside it is "
     "exploratory."),
    ("Explainability", "shap_combined",
     "SHAP attributions exported by the research pipeline."),
    ("Robustness", "arrival_test_metrics",
     "Arrival-hour target results, held separate from the primary target."),
    ("SARIMAX + Fourier", "sarimax_test_metrics",
     "The active time-series comparator."),
]


def artifacts() -> dict:
    rows = []
    for key, spec in al.SPECS.items():
        art = al.load(key)
        if art.available:
            status = "available"
        elif spec.optional or spec.group == "legacy":
            status = "optional"
        else:
            status = "missing"
        rows.append({
            "key": key,
            "label": spec.label,
            "group": GROUP_LABELS.get(spec.group, spec.group.title()),
            "path": spec.relative,
            "status": status,
            "rows": int(len(art.frame)) if art.available else None,
            "producedBy": spec.produced_by,
            "reason": None if art.available else art.reason,
            "expectedColumns": list(spec.required),
            "detectedColumns": art.detected_columns,
        })

    directories = []
    for key, (relative, label, pattern) in al.DIRECTORIES.items():
        files = al.list_directory(key)
        directories.append({
            "key": key, "label": label, "path": relative + "/",
            "pattern": pattern, "fileCount": len(files),
            "status": "available" if files else "optional",
            "files": [f.name for f in files],
        })

    return {"artifacts": rows, "directories": directories,
            "repositoryRoot": str(config.repo_root())}


def provenance() -> dict:
    rows = []
    for label, key, role in PROVENANCE_CHECKS:
        art = al.load(key)
        rows.append({"result": label, "path": art.spec.relative,
                     "status": "available" if art.available else "missing",
                     "role": role})

    legacy = al.load("legacy_sarima")
    rows.append({
        "result": "Legacy SARIMA",
        "path": legacy.spec.relative,
        "status": "quarantined" if legacy.available else "absent",
        "role": ("Superseded. Excluded from every metric, chart, comparison "
                 "and conclusion, and never surfaced as a current research "
                 "result."),
    })

    return {
        "rows": rows,
        "statements": {
            "targetLimitation": config.TARGET_LIMITATION,
            "crossTarget": config.CROSS_TARGET_WARNING,
            "notCausal": config.NOT_CAUSAL,
            "peak": config.PEAK_CAVEAT,
            "capacity": config.CAPACITY_CAVEAT,
            "audited": config.AUDITED_NOTE,
            "exploratory": config.EXPLORATORY_NOTE,
        },
        "study": {
            "title": ("A Comparative Study of Machine Learning and "
                      "Time-Series Approaches for EV Charging Demand "
                      "Prediction"),
            "dataset": config.DATASET_NAME,
            "split": "70 / 15 / 15 chronological, no shuffling",
            "forecasting": ("Recursive day-ahead forecasting over a 24-hour "
                            "horizon"),
            "models": ["Seasonal Naive", "Linear Regression",
                       "Random Forest", "XGBoost", "SARIMAX + Fourier"],
            "statisticalTesting": ("Diebold-Mariano on squared-error loss "
                                   "with a Newey-West HAC variance estimate"),
            "explainability": "SHAP attributions and built-in tree importance",
            "robustness": "Arrival-hour target construction",
        },
        "limitations": [
            {"title": "Retrospective target construction",
             "body": config.TARGET_LIMITATION},
            {"title": "Test-period conditional metrics",
             "body": ("Metrics are computed on a single contiguous test "
                      "block and are conditional on that period.")},
            {"title": "Dataset-specific findings",
             "body": ("All sessions come from one campus site. Findings do "
                      "not generalise to public fast charging or "
                      "residential use.")},
            {"title": "Peak classification is not electrical overload",
             "body": config.PEAK_CAVEAT},
            {"title": "SHAP is not causal inference",
             "body": config.NOT_CAUSAL},
        ],
    }
