"""Request scoped dependencies."""
from __future__ import annotations

from flask import g
from sqlalchemy.orm import Session

from .database import get_session
from .services.conversations import ConversationService


def get_db_session() -> Session:
    if "db_session" not in g:
        g.db_session = get_session()
    return g.db_session


def get_conversation_service() -> ConversationService:
    if "conversation_service" not in g:
        g.conversation_service = ConversationService(get_db_session())
    return g.conversation_service


def cleanup_services(exception: Exception | None = None) -> None:
    session = g.pop("db_session", None)
    if session is not None:
        session.close()
    g.pop("conversation_service", None)
