"""Request scoped dependencies."""
from __future__ import annotations

from flask import g

from ..database import get_session
from ..services.ingestion import IngestionService
from ..services.reporting import ReportingService


def get_ingestion_service() -> IngestionService:
    if "analytics_session" not in g:
        g.analytics_session = get_session()
    if "ingestion_service" not in g:
        g.ingestion_service = IngestionService(g.analytics_session)
    return g.ingestion_service


def get_reporting_service() -> ReportingService:
    if "analytics_session" not in g:
        g.analytics_session = get_session()
    if "reporting_service" not in g:
        g.reporting_service = ReportingService(g.analytics_session)
    return g.reporting_service


def cleanup_services(exception: Exception | None = None) -> None:
    session = g.pop("analytics_session", None)
    if session is not None:
        session.close()
    g.pop("ingestion_service", None)
    g.pop("reporting_service", None)
