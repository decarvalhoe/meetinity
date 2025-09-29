"""SQLAlchemy-powered persistence layer for the matching service."""

from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    aliased,
    mapped_column,
    relationship,
    sessionmaker,
)

from src.config import get_settings

from .models import Swipe, SwipeEvent, User

SCHEMA_NAME = "matching"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA_NAME)


class UserORM(Base):
    """SQLAlchemy model storing matchmaking users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    preferences: Mapped[List[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class SwipeORM(Base):
    """Model storing swipe interactions between users."""

    __tablename__ = "swipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class MatchORM(Base):
    """Match between two profiles."""

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_id", "matched_user_id", name="uq_match"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    matched_user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    score: Mapped["MatchScoreORM"] = relationship(
        "MatchScoreORM", back_populates="match", uselist=False
    )


class MatchScoreORM(Base):
    """Score associated with a match."""

    __tablename__ = "match_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.matches.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    match: Mapped[MatchORM] = relationship("MatchORM", back_populates="score")


class SwipeEventORM(Base):
    """Analytical events for swipe actions."""

    __tablename__ = "swipe_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    swipe_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.swipes.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_NAME}.users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return (and lazily create) the SQLAlchemy engine."""

    global _ENGINE
    if _ENGINE is None:
        settings = get_settings()
        _ENGINE = create_engine(settings.database_uri, **settings.engine_options)
    return _ENGINE


def reset_engine() -> None:
    """Dispose of the existing engine and session factory."""

    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None


def _get_session_factory() -> sessionmaker[Session]:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=get_engine(), expire_on_commit=False, future=True
        )
    return _SESSION_FACTORY


@contextmanager
def transaction_scope(commit: bool = True) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    settings = get_settings()
    attempts = max(1, settings.max_retries)
    delay = settings.retry_backoff
    retries = 0

    while True:
        session = _get_session_factory()()
        try:
            yield session
            if commit:
                session.commit()
            else:
                session.rollback()
            return
        except OperationalError:
            session.rollback()
            retries += 1
            if retries >= attempts:
                raise
            time.sleep(delay)
            delay *= 2
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _alembic_config() -> Config:
    service_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(service_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(service_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_uri)
    return cfg


def init_db() -> None:
    """Ensure the database schema is up to date via Alembic migrations."""

    command.upgrade(_alembic_config(), "head")


def reset_database() -> None:
    """Truncate all matching tables while preserving schema and migrations."""

    engine = get_engine()
    tables = ["swipe_events", "match_scores", "matches", "swipes", "users"]
    with engine.begin() as connection:
        for table in tables:
            connection.execute(
                text(
                    f'TRUNCATE TABLE "{SCHEMA_NAME}"."{table}" RESTART IDENTITY CASCADE'
                )
            )


def _to_domain_user(instance: UserORM) -> User:
    return User(
        id=instance.id,
        email=instance.email,
        full_name=instance.full_name,
        title=instance.title,
        company=instance.company,
        bio=instance.bio,
        preferences=list(instance.preferences or []),
        is_active=bool(instance.is_active),
        created_at=instance.created_at,
        updated_at=instance.updated_at,
    )


def _ensure_datetimes(user: User) -> None:
    if user.created_at is None:
        user.created_at = _utcnow()
    if user.updated_at is None:
        user.updated_at = _utcnow()


def upsert_user(user: User) -> User:
    """Insert or update a user profile."""

    _ensure_datetimes(user)
    with transaction_scope() as session:
        instance: UserORM | None = None
        if user.id is not None:
            instance = session.get(UserORM, user.id)
        if instance is None:
            stmt = select(UserORM).where(UserORM.email == user.email)
            instance = session.execute(stmt).scalar_one_or_none()
        if instance is None:
            instance = UserORM()
        if user.id is not None:
            instance.id = user.id
        instance.email = user.email
        instance.full_name = user.full_name
        instance.title = user.title
        instance.company = user.company
        instance.bio = user.bio
        instance.preferences = list(user.preferences or [])
        instance.is_active = bool(user.is_active)
        instance.created_at = user.created_at
        instance.updated_at = user.updated_at
        session.add(instance)
        session.flush()
        user.id = instance.id
        return _to_domain_user(instance)


def create_user(user: User) -> User:
    """Compatibility wrapper calling :func:`upsert_user`."""

    return upsert_user(user)


def get_user(user_id: int) -> Optional[User]:
    with transaction_scope(commit=False) as session:
        instance = session.get(UserORM, user_id)
        if instance is None:
            return None
        return _to_domain_user(instance)


def list_users(
    exclude_user_id: int | None = None, only_active: bool = True
) -> List[User]:
    with transaction_scope(commit=False) as session:
        stmt = select(UserORM)
        if only_active:
            stmt = stmt.where(UserORM.is_active.is_(True))
        if exclude_user_id is not None:
            stmt = stmt.where(UserORM.id != exclude_user_id)
        stmt = stmt.order_by(UserORM.id)
        rows = session.execute(stmt).scalars().all()
        return [_to_domain_user(row) for row in rows]


def create_swipe(swipe: Swipe) -> Swipe:
    if swipe.created_at is None:
        swipe.created_at = _utcnow()
    with transaction_scope() as session:
        instance = SwipeORM(
            user_id=swipe.user_id,
            target_id=swipe.target_id,
            action=swipe.action,
            created_at=swipe.created_at,
        )
        session.add(instance)
        session.flush()
        swipe.id = instance.id
        return swipe


def has_mutual_like(user_id: int, target_id: int) -> bool:
    with transaction_scope(commit=False) as session:
        stmt = select(SwipeORM.id).where(
            SwipeORM.user_id == target_id,
            SwipeORM.target_id == user_id,
            SwipeORM.action == "like",
        )
        return session.execute(stmt).first() is not None


def create_matches(
    user_id: int,
    target_id: int,
    score: float,
    common_interests: Iterable[str],
) -> List[int]:
    details = {"common_interests": list(common_interests)}
    match_ids: List[int] = []
    with transaction_scope() as session:
        now = _utcnow()
        for left, right in ((user_id, target_id), (target_id, user_id)):
            stmt = select(MatchORM).where(
                MatchORM.user_id == left, MatchORM.matched_user_id == right
            )
            match = session.execute(stmt).scalar_one_or_none()
            if match is None:
                match = MatchORM(user_id=left, matched_user_id=right, created_at=now)
                session.add(match)
                session.flush()
            match_ids.append(match.id)
            if match.score is None:
                match.score = MatchScoreORM(
                    match_id=match.id, score=score, details=details, created_at=now
                )
            else:
                match.score.score = score
                match.score.details = details
                match.score.created_at = now
            session.add(match)
    return match_ids


def log_swipe_event(event: SwipeEvent) -> SwipeEvent:
    if event.created_at is None:
        event.created_at = _utcnow()
    with transaction_scope() as session:
        instance = SwipeEventORM(
            swipe_id=event.swipe_id,
            event_type=event.event_type,
            user_id=event.user_id,
            target_id=event.target_id,
            action=event.action,
            score=event.score,
            payload=dict(event.payload or {}),
            created_at=event.created_at,
        )
        session.add(instance)
        session.flush()
        event.id = instance.id
        return event


def fetch_matches_for_user(user_id: int) -> List[Dict[str, Any]]:
    partner = aliased(UserORM)
    with transaction_scope(commit=False) as session:
        stmt = (
            select(
                MatchORM.id.label("match_id"),
                MatchORM.created_at.label("created_at"),
                partner.id.label("partner_id"),
                partner.full_name.label("full_name"),
                partner.title.label("title"),
                partner.company.label("company"),
                partner.preferences.label("preferences"),
                MatchScoreORM.score.label("score"),
                MatchScoreORM.details.label("details"),
            )
            .join(partner, MatchORM.matched_user_id == partner.id)
            .outerjoin(MatchScoreORM, MatchScoreORM.match_id == MatchORM.id)
            .where(MatchORM.user_id == user_id)
            .order_by(MatchORM.created_at.desc())
        )
        results: List[Dict[str, Any]] = []
        for row in session.execute(stmt):
            preferences = list(row.preferences or [])
            details = dict(row.details or {})
            results.append(
                {
                    "id": row.match_id,
                    "user_id": row.partner_id,
                    "name": row.full_name,
                    "title": row.title,
                    "company": row.company,
                    "match_score": row.score,
                    "preferences": preferences,
                    "common_interests": details.get("common_interests", []),
                    "created_at": row.created_at.isoformat(),
                }
            )
        return results


def count_rows(table: str) -> int:
    with transaction_scope(commit=False) as session:
        stmt = text(f'SELECT COUNT(*) FROM "{SCHEMA_NAME}"."{table}"')
        return int(session.execute(stmt).scalar_one())


def fetch_swipe_events() -> List[Dict[str, Any]]:
    with transaction_scope(commit=False) as session:
        stmt = select(SwipeEventORM).order_by(SwipeEventORM.id)
        events: List[Dict[str, Any]] = []
        for instance in session.execute(stmt).scalars():
            events.append(
                {
                    "id": instance.id,
                    "swipe_id": instance.swipe_id,
                    "event_type": instance.event_type,
                    "user_id": instance.user_id,
                    "target_id": instance.target_id,
                    "action": instance.action,
                    "score": instance.score,
                    "payload": dict(instance.payload or {}),
                    "created_at": instance.created_at.isoformat(),
                }
            )
        return events


__all__ = [
    "Base",
    "count_rows",
    "create_matches",
    "create_swipe",
    "create_user",
    "fetch_matches_for_user",
    "fetch_swipe_events",
    "get_engine",
    "get_user",
    "has_mutual_like",
    "init_db",
    "log_swipe_event",
    "reset_database",
    "reset_engine",
    "transaction_scope",
    "upsert_user",
]
