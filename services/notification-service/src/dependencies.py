"""Request scoped dependencies for the notification service."""
from __future__ import annotations

from flask import g
from sqlalchemy.orm import Session

from .cache import get_redis_client
from .database import get_session
from .queue import InMemoryQueue, NotificationQueue, build_queue
from .services.notifications import NotificationService, PreferenceService


def get_db_session() -> Session:
    if "db_session" not in g:
        g.db_session = get_session()
    return g.db_session


def get_cache_client():
    if "cache_client" not in g:
        g.cache_client = get_redis_client()
    return g.cache_client


def get_queue() -> NotificationQueue | InMemoryQueue:
    if "notification_queue" not in g:
        g.notification_queue = build_queue()
    return g.notification_queue


def get_preference_service() -> PreferenceService:
    if "preference_service" not in g:
        g.preference_service = PreferenceService(get_db_session(), get_cache_client())
    return g.preference_service


def get_notification_service() -> NotificationService:
    if "notification_service" not in g:
        g.notification_service = NotificationService(
            get_db_session(), get_preference_service(), get_queue()
        )
    return g.notification_service


def cleanup_services(exception: Exception | None = None) -> None:
    session = g.pop("db_session", None)
    if session is not None:
        session.close()
    g.pop("cache_client", None)
    g.pop("preference_service", None)
    g.pop("notification_service", None)
    g.pop("notification_queue", None)
