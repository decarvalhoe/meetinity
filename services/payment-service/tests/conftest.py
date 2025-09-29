from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

os.environ.setdefault("STRIPE__API_KEY", "test")
os.environ.setdefault("STRIPE__WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("PAYPAL__API_KEY", "test")
os.environ.setdefault("PAYPAL__WEBHOOK_SECRET", "whsec_test")

from payment_service.app import create_app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

