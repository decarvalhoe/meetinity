"""Event consumers for asynchronous ingestion."""
from __future__ import annotations

import json
from typing import Iterable, Mapping

from sqlalchemy.orm import Session

from . import schemas
from .services.ingestion import IngestionService


class AnalyticsEventConsumer:
    """Consume events from a message queue and persist them."""

    def __init__(self, session: Session):
        self._ingestion = IngestionService(session)

    def _parse(self, message: Mapping[str, object]) -> schemas.EventPayload:
        if "payload" in message and isinstance(message["payload"], str):
            try:
                body = json.loads(message["payload"])
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("payload is not valid JSON") from exc
        else:
            body = message
        return schemas.EventPayload(**body)  # type: ignore[arg-type]

    def consume(self, message: Mapping[str, object]) -> int:
        payload = self._parse(message)
        self._ingestion.ingest(payload)
        return 1

    def consume_batch(self, messages: Iterable[Mapping[str, object]]) -> int:
        count = 0
        for message in messages:
            count += self.consume(message)
        return count


__all__ = ["AnalyticsEventConsumer"]
