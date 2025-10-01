"""Request scoped dependencies."""
from __future__ import annotations

from flask import current_app, g
from sqlalchemy.orm import Session

from .database import get_session
from .integrations import ModerationClient, NotificationClient
from .services.conversations import ConversationService


def get_db_session() -> Session:
    if "db_session" not in g:
        g.db_session = get_session()
    return g.db_session


def get_conversation_service() -> ConversationService:
    if "conversation_service" not in g:
        g.conversation_service = ConversationService(
            get_db_session(),
            get_moderation_client(),
            get_notification_client(),
        )
    return g.conversation_service


def get_moderation_client() -> ModerationClient:
    if "moderation_client" not in g:
        url = current_app.config.get("MODERATION_SERVICE_URL")
        g.moderation_client = ModerationClient(url)
    return g.moderation_client


def get_notification_client() -> NotificationClient:
    if "notification_client" not in g:
        url = current_app.config.get("NOTIFICATION_SERVICE_URL")
        g.notification_client = NotificationClient(url)
    return g.notification_client


def cleanup_services(exception: Exception | None = None) -> None:
    session = g.pop("db_session", None)
    if session is not None:
        session.close()
    g.pop("conversation_service", None)
    g.pop("moderation_client", None)
    g.pop("notification_client", None)
