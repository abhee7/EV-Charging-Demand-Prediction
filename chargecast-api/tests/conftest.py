import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pytest  # noqa: E402


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import artifact_loader as al
    al.clear_cache()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def repo_root() -> Path:
    from app import config
    return config.repo_root()
