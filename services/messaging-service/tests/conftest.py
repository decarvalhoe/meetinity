from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import Base, dispose_engine, get_engine
from src.main import create_app


@pytest.fixture
def app():
    dispose_engine()
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"})
    with app.app_context():
        Base.metadata.create_all(get_engine())
    yield app
    dispose_engine()


@pytest.fixture
def client(app):
    return app.test_client()


def auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_id}"}
