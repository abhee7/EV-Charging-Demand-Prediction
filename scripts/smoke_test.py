#!/usr/bin/env python3
"""ChargeCast end-to-end smoke test.

Launches the FastAPI backend and the Vite dev server, verifies both answer
HTTP 200, walks every documented GET endpoint, checks all eight frontend
routes, and confirms the audited artefacts are genuinely read.

    python scripts/smoke_test.py                 # backend only
    python scripts/smoke_test.py --with-frontend # also start Vite

Nothing in this script writes to data/ or results/.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "chargecast-api"
WEB_DIR = ROOT / "chargecast-web"

API_URL = os.environ.get("CHARGECAST_API_URL", "http://127.0.0.1:8000")
WEB_URL = os.environ.get("CHARGECAST_WEB_URL", "http://127.0.0.1:5173")

FRONTEND_ROUTES = [
    "/", "/forecast", "/model-lab", "/analytics", "/peak",
    "/explainability", "/robustness", "/research",
]

SAMPLE_PARAMS = {
    "window_id": "1", "model": None, "model_a": None, "model_b": None,
    "hac_lag": "23", "percentile": "90", "metric": "mae",
    "prediction_set": "primary", "source": "shap", "capacity_kw": "120",
    "change": "10", "downsample": "2", "bins": "48", "max_lag": "336",
    "lag": "168", "horizon": "24",
}

VITE_LOG = Path(os.environ.get("TMPDIR", "/tmp")) / "chargecast-vite.log"


def _vite_log_tail() -> str:
    try:
        return VITE_LOG.read_text(errors="replace").strip().splitlines()[-1]
    except (OSError, IndexError):
        return "no dev-server output"


passed: list[str] = []
failed: list[tuple[str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    if ok:
        passed.append(name)
        print(f"  ok    {name}")
    else:
        failed.append((name, detail))
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))
    return ok


def get(url: str, timeout: float = 30):
    """JSON request, for the API."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    return urllib.request.urlopen(request, timeout=timeout)


def get_html(url: str, timeout: float = 15):
    """HTML navigation request, for the dev server.

    Vite serves index.html only for requests that accept HTML; asking it for
    application/json returns 404, so the frontend checks must not reuse get().
    """
    request = urllib.request.Request(
        url, headers={"Accept": "text/html,application/xhtml+xml"})
    return urllib.request.urlopen(request, timeout=timeout)


def wait_for(url: str, label: str, seconds: int = 45, html: bool = False) -> bool:
    deadline = time.time() + seconds
    fetch = get_html if html else get
    while time.time() < deadline:
        try:
            fetch(url, timeout=3)
            return True
        except Exception:
            time.sleep(1)
    return False


def discover_models() -> None:
    """Take real model names from the API so no name is hard-coded."""
    try:
        body = json.load(get(f"{API_URL}/api/models/metrics"))
        names = [m["model"] for m in body.get("models", [])]
    except Exception:
        names = []
    if names:
        SAMPLE_PARAMS["model"] = names[0]
        SAMPLE_PARAMS["model_a"] = names[0]
        SAMPLE_PARAMS["model_b"] = names[1] if len(names) > 1 else names[0]


def test_endpoints() -> None:
    print("\nAPI endpoints")
    spec = json.load(get(f"{API_URL}/openapi.json"))
    for path, methods in sorted(spec["paths"].items()):
        if not path.startswith("/api") or "get" not in methods:
            continue
        url, params = path, {}
        unfilled: list[str] = []
        for param in methods["get"].get("parameters", []):
            name = param["name"]
            value = SAMPLE_PARAMS.get(name)
            if value is None:
                # A required parameter we cannot sample (model names are
                # discovered from the API, so they are unavailable when the
                # artefacts are absent). Skip rather than send an invalid call.
                if param.get("required"):
                    unfilled.append(name)
                continue
            if param["in"] == "path":
                url = url.replace("{" + name + "}", value)
            elif param.get("required") or name in ("model", "metric", "percentile"):
                params[name] = value
        if unfilled:
            print(f"  skip  GET {path} (no sample for {', '.join(unfilled)})")
            continue
        if "{" in url:
            continue
        full = f"{API_URL}{url}"
        if params:
            full += "?" + urllib.parse.urlencode(params)
        try:
            response = get(full)
            check(f"GET {url}", response.status == 200, str(response.status))
        except Exception as exc:  # noqa: BLE001
            check(f"GET {url}", False, str(exc))


def test_audited_artifacts() -> None:
    print("\nAudited artefacts")
    try:
        dm = json.load(get(f"{API_URL}/api/models/dm/audited"))
    except Exception as exc:  # noqa: BLE001
        check("audited DM endpoint", False, str(exc))
        return

    if dm.get("available"):
        check("audited DM read from diebold_mariano_tests.csv",
              dm["source"].endswith("diebold_mariano_tests.csv"), dm.get("source", ""))
        check("audited DM exposes the stored columns", bool(dm.get("columns")))
        check("audited DM is labelled as the verified artefact",
              dm.get("provenance") == "VERIFIED RESEARCH ARTIFACT")
    else:
        print(f"  skip  audited DM not present ({dm.get('path')})")

    try:
        peak = json.load(get(f"{API_URL}/api/peak/audited"))
    except Exception as exc:  # noqa: BLE001
        check("audited peak endpoint", False, str(exc))
        return

    if peak.get("available"):
        check("audited peak read from model_peak_detection.csv",
              peak["source"].endswith("model_peak_detection.csv"), peak.get("source", ""))
        check("audited peak is labelled as the verified artefact",
              peak.get("provenance") == "VERIFIED RESEARCH ARTIFACT")
    else:
        print(f"  skip  audited peak not present ({peak.get('path')})")


def test_separation() -> None:
    print("\nAudited / interactive separation")
    try:
        before = json.load(get(f"{API_URL}/api/models/dm/audited"))
        params = {"percentile": "95"}
        interactive = json.load(
            get(f"{API_URL}/api/peak/interactive?" + urllib.parse.urlencode(params)))
        after = json.load(get(f"{API_URL}/api/models/dm/audited"))
    except Exception as exc:  # noqa: BLE001
        check("separation checks", False, str(exc))
        return

    check("audited result unchanged by an interactive request", before == after)
    if interactive.get("available"):
        check("interactive result is labelled exploratory",
              "EXPLORATORY" in str(interactive.get("provenance", "")))
        check("a non-audited percentile is flagged",
              interactive.get("differsFromAudited") is True)


def test_frontend() -> None:
    print("\nFrontend routes")
    for route in FRONTEND_ROUTES:
        try:
            response = get_html(f"{WEB_URL}{route}")
            check(f"GET {route}", response.status == 200)
        except Exception as exc:  # noqa: BLE001
            check(f"GET {route}", False, str(exc))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-frontend", action="store_true",
                        help="Also start the Vite dev server and check routes.")
    parser.add_argument("--no-launch", action="store_true",
                        help="Assume both services are already running.")
    args = parser.parse_args()

    processes: list[subprocess.Popen[bytes]] = []
    try:
        if not args.no_launch:
            print("Starting FastAPI ...")
            processes.append(subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app",
                 "--port", "8000", "--host", "127.0.0.1"],
                cwd=API_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))

        if not wait_for(f"{API_URL}/api/health", "FastAPI"):
            return 1
        check("FastAPI health returns 200", True)
        check("FastAPI docs returns 200",
              urllib.request.urlopen(f"{API_URL}/docs", timeout=10).status == 200)

        discover_models()
        test_endpoints()
        test_audited_artifacts()
        test_separation()

        if args.with_frontend:
            if not args.no_launch:
                print("\nStarting Vite ...")
                vite = WEB_DIR / "node_modules" / ".bin" / "vite"
                if not vite.exists():
                    check("Vite is installed (run npm install)", False,
                          str(vite))
                else:
                    log = open(VITE_LOG, "wb")
                    processes.append(subprocess.Popen(
                        [str(vite), "--port", "5173", "--strictPort",
                         "--host", "127.0.0.1"],
                        cwd=WEB_DIR, stdout=log, stderr=log))
            if check("Vite dev server started",
                     wait_for(WEB_URL, "Vite", seconds=90, html=True),
                     _vite_log_tail()):
                test_frontend()
    finally:
        for process in processes:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

    print(f"\n{len(passed)} passed, {len(failed)} failed")
    if failed:
        print("\nFailures:")
        for name, detail in failed:
            print(f"  {name}" + (f"  [{detail}]" if detail else ""))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
