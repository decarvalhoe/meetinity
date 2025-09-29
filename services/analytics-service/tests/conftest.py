from __future__ import annotations

from pathlib import Path
import sys

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from src.database import dispose_engine, get_session  # type: ignore  # noqa: E402
from src.main import create_app  # type: ignore  # noqa: E402


@pytest.fixture
def app():
    app = create_app({"DATABASE_URL": "sqlite+pysqlite:///:memory:"})
    app.config.update({"TESTING": True})
    yield app
    dispose_engine()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        db_session = get_session()
        yield db_session
        db_session.close()
