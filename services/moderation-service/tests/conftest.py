from __future__ import annotations

import pytest

from src.database import Base, get_engine, reset_engine
from src.main import create_app


@pytest.fixture()
def app(tmp_path):
    reset_engine()
    db_path = tmp_path / "moderation.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{db_path}",
            "REDIS_URL": "fakeredis://",
            "KAFKA_BOOTSTRAP_SERVERS": None,
        }
    )
    yield app
    Base.metadata.drop_all(get_engine())
    reset_engine()


@pytest.fixture()
def client(app):
    return app.test_client()
