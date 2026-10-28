"""ChargeCast smoke test.

Verifies that every module imports, every page renders without raising, and no
ranking language appears in rendered copy. Run from the repository root:

    python chargecast/tests/smoke_test.py

Passes both when result files are present and when they are absent: with files
missing, it exercises the empty-state path instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ROOT = PKG.parent
for p in (str(PKG), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

APP = str(PKG / "app.py")

PAGES = [
    "Overview", "Forecast", "Model comparison", "Demand analytics",
    "Explainability", "Robustness", "About the project",
]


def check_imports() -> list[str]:
    problems = []
    modules = [
        "config", "core.schema", "core.loaders", "core.formatting", "core.ui",
        "theme.plotly_theme", "components.kpi", "components.charts",
        "components.empty_state", "components.metric_table",
        "views.overview", "views.forecast", "views.comparison",
        "views.analytics", "views.explainability", "views.robustness",
        "views.about",
    ]
    for name in modules:
        try:
            __import__(name)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{name}: {exc}")
    return problems


def main() -> int:
    print("ChargeCast smoke test")
    print(f"  package : {PKG}")
    print(f"  repo    : {ROOT}\n")

    problems = check_imports()
    if problems:
        print("Module import failures:")
        for p in problems:
            print(f"  {p}")
        return 1
    print("All modules import.\n")

    from streamlit.testing.v1 import AppTest

    from components.metric_table import assert_neutral

    failures = []
    for label in PAGES:
        at = AppTest.from_file(APP, default_timeout=180)
        at.run()
        if at.exception:
            failures.append((label, "boot",
                             [e.value for e in at.exception]))
            print(f"FAIL  {label:22s} boot exception")
            continue

        try:
            at.sidebar.radio[0].set_value(label).run()
        except Exception as exc:  # noqa: BLE001
            failures.append((label, "navigation", [str(exc)]))
            print(f"FAIL  {label:22s} navigation: {exc}")
            continue

        if at.exception:
            failures.append((label, "render",
                             [e.value for e in at.exception]))
            print(f"FAIL  {label:22s} render exception")
            continue

        errors = [e.value for e in at.error]
        if errors:
            failures.append((label, "st.error", errors))
            print(f"FAIL  {label:22s} st.error: {errors[0][:100]}")
            continue

        # Neutrality: no ranking language anywhere in rendered copy.
        copy = " ".join(m.value for m in at.markdown if isinstance(m.value, str))
        try:
            assert_neutral(copy)
        except AssertionError as exc:
            failures.append((label, "neutrality", [str(exc)]))
            print(f"FAIL  {label:22s} {exc}")
            continue

        print(f"ok    {label:22s} rendered, {len(at.markdown)} blocks")

    print()
    if failures:
        print(f"{len(failures)} page(s) failed")
        for label, stage, detail in failures:
            print(f"\n--- {label} [{stage}] ---")
            for d in detail:
                print(d)
        return 1

    print("All pages rendered without errors. No ranking language detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
