import sys
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import Base, dispose_engine, get_engine
from src.main import create_app
from src.queue import InMemoryQueue
from src.metrics import reset_metrics


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value


@pytest.fixture
def app():
    dispose_engine()
    queue_backend = InMemoryQueue()
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": "sqlite:///:memory:",
        "KAFKA_PRODUCER": queue_backend,
    })
    app.config["REDIS_CLIENT"] = FakeRedis()
    with app.app_context():
        Base.metadata.create_all(get_engine())
    yield app
    dispose_engine()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _reset_notification_metrics():
    reset_metrics()
    yield
    reset_metrics()


def auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_id}"}
