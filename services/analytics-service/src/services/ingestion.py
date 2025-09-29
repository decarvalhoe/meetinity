"""Ingestion service for analytics events."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import schemas
from ..metrics import observe_ingestion
from ..models import AnalyticsEvent


class IngestionError(Exception):
    """Raised when an event payload cannot be ingested."""


class IngestionService:
    """Persist analytics events received from APIs or consumers."""

    def __init__(self, session: Session):
        self._session = session

    def ingest(self, payload: schemas.EventPayload) -> AnalyticsEvent:
        event = AnalyticsEvent(
            event_type=payload.event_type,
            user_id=payload.user_id,
            occurred_at=payload.occurred_at,
            ingestion_id=payload.ingestion_id,
            source=payload.source or "http",
            payload=payload.payload,
            context=payload.context,
        )
        event.received_at = datetime.now(timezone.utc)
        latency = (event.received_at - event.occurred_at).total_seconds()
        try:
            self._session.add(event)
            self._session.flush()
            self._session.commit()
        except IntegrityError as exc:  # pragma: no cover - defensive branch
            self._session.rollback()
            raise IngestionError("Failed to persist event") from exc
        observe_ingestion(event.event_type, event.source, max(latency, 0.0))
        return event

    def ingest_batch(self, payloads: Iterable[schemas.EventPayload]) -> Sequence[AnalyticsEvent]:
        events = [self.ingest(payload) for payload in payloads]
        self._session.commit()
        return events
