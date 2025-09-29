"""Database helpers for the analytics service."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base


_engine: Engine | None = None
_Session = None


def init_engine(database_url: str) -> Engine:
    """Initialise the SQLAlchemy engine and session factory."""

    global _engine, _Session

    if _engine is not None:
        _engine.dispose()

    kwargs: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if database_url.startswith("sqlite"):  # pragma: no cover - configuration branch
        kwargs.setdefault("connect_args", {"check_same_thread": False})
        kwargs.setdefault("poolclass", StaticPool)

    _engine = create_engine(database_url, **kwargs)
    _Session = scoped_session(
        sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    )
    Base.metadata.create_all(_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine not initialised. Call init_engine() first.")
    return _engine


def get_session():
    if _Session is None:
        raise RuntimeError("Session factory not initialised. Call init_engine() first.")
    return _Session()


@contextmanager
def session_scope() -> Generator:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def dispose_engine() -> None:
    global _engine, _Session
    if _Session is not None:
        _Session.remove()
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None
