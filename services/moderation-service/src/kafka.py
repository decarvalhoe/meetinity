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

    producer = _ensure_producer(config)
    try:
        future = producer.send(topic, key=key, value=payload)
    except Exception as exc:  # pragma: no cover - exercised in tests
        _handle_failure(config, producer, key, payload, exc)
        return

    future.add_errback(lambda exc: _handle_failure(config, producer, key, payload, exc))
    producer.flush(0.5)


def _ensure_producer(config):
    producer = getattr(current_app, "_moderation_kafka_producer", None)
    if producer is None:
        bootstrap = config.kafka_bootstrap
        producer = KafkaProducer(
            bootstrap_servers=_as_list(bootstrap),
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8"),
            **_build_security_kwargs(config),
        )
        current_app._moderation_kafka_producer = producer  # type: ignore[attr-defined]
    return producer


def _handle_failure(config, producer, key: str, payload: dict[str, Any], exc: Exception) -> None:
    logger.warning("Kafka publish failed", exc_info=exc, extra={"topic": config.moderation_topic})
    dlq_topic = config.kafka_dead_letter_topic
    if not dlq_topic:
        return
    failure_payload = dict(payload)
    failure_payload["_error"] = str(exc)
    failure_payload["_original_topic"] = config.moderation_topic
    try:
        producer.send(dlq_topic, key=key, value=failure_payload)
        producer.flush(0.5)
    except Exception as dlq_exc:  # pragma: no cover - defensive guard
        logger.error("Failed to publish moderation event to DLQ", exc_info=dlq_exc)


def _build_security_kwargs(config) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if config.kafka_security_protocol:
        kwargs["security_protocol"] = config.kafka_security_protocol
    if config.kafka_sasl_mechanism:
        kwargs["sasl_mechanism"] = config.kafka_sasl_mechanism
    if config.kafka_sasl_username and config.kafka_sasl_password:
        kwargs["sasl_plain_username"] = config.kafka_sasl_username
        kwargs["sasl_plain_password"] = config.kafka_sasl_password
    return kwargs


def _as_list(servers: str | None) -> list[str]:
    if not servers:
        return []
    return [s.strip() for s in servers.split(",") if s.strip()]


__all__ = ["publish_event"]
