"""Audit logging helpers for the payment service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import structlog

from .config import get_settings


def configure_audit_logger() -> structlog.BoundLogger:
    """Return a structured logger configured for audit trails."""

    settings = get_settings()
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
    )
    logger = structlog.get_logger(settings.service_name).bind(
        environment=settings.environment,
        sink=settings.audit.sink,
    )
    return logger


def audit_event(event_type: str, payload: Mapping[str, Any]) -> None:
    """Emit an audit event."""

    logger = configure_audit_logger()
    logger.info(
        "audit_event",
        event_type=event_type,
        event_time=datetime.now(timezone.utc).isoformat(),
        **payload,
    )


__all__ = ["audit_event", "configure_audit_logger"]

