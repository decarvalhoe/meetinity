"""Kafka publisher with graceful fallbacks."""
from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app

try:  # pragma: no cover - optional dependency
    from kafka import KafkaProducer
except Exception:  # pragma: no cover - fallback when kafka-python is unavailable
    KafkaProducer = None  # type: ignore

logger = logging.getLogger(__name__)


def publish_event(*, config, key: str, payload: dict[str, Any]) -> None:
    """Publish moderation lifecycle events to Kafka if configured."""

    topic = config.moderation_topic
    bootstrap = config.kafka_bootstrap

    if not bootstrap or KafkaProducer is None:
        logger.debug("Kafka producer unavailable; event dropped", extra={"payload": payload})
        return

    producer = getattr(current_app, "_moderation_kafka_producer", None)
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap.split(","),
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8"),
        )
        current_app._moderation_kafka_producer = producer  # type: ignore[attr-defined]

    future = producer.send(topic, key=key, value=payload)
    future.add_errback(lambda exc: logger.warning("Kafka publish failed", exc_info=exc))
    producer.flush(0.5)


__all__ = ["publish_event"]
