"""Pytest configuration for the matching service tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import refresh_settings  # noqa: E402
from src.storage import init_db, reset_database, reset_engine  # noqa: E402


POSTGRES_CONTAINER: PostgresContainer | None = None
CONTAINER_ERROR: Exception | None = None


def _bootstrap_postgres() -> None:
    global POSTGRES_CONTAINER, CONTAINER_ERROR
    try:
        POSTGRES_CONTAINER = PostgresContainer("postgres:15-alpine")
        POSTGRES_CONTAINER.start()
        connection_url = POSTGRES_CONTAINER.get_connection_url()
        database_uri = connection_url.replace("psycopg2", "psycopg") + "?options=-csearch_path%3Dmatching"
        os.environ["DATABASE_URI"] = database_uri
        os.environ.pop("MATCHING_SKIP_DB_INIT", None)
        refresh_settings()
        reset_engine()
        init_db()
    except Exception as exc:  # pragma: no cover - infrastructure failure
        CONTAINER_ERROR = exc
        POSTGRES_CONTAINER = None
        os.environ["MATCHING_SKIP_DB_INIT"] = "1"


_bootstrap_postgres()


@pytest.fixture(scope="session", autouse=True)
def _postgres_database():
    if CONTAINER_ERROR is not None:
        pytest.skip(f"PostgreSQL container unavailable: {CONTAINER_ERROR}")
    yield
    if POSTGRES_CONTAINER is not None:
        POSTGRES_CONTAINER.stop()


@pytest.fixture(autouse=True)
def _clean_database():
    if CONTAINER_ERROR is not None:
        pytest.skip(f"PostgreSQL container unavailable: {CONTAINER_ERROR}")
    reset_database()
    yield
