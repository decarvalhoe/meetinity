from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Protocol

from flask import current_app

from .metrics import (
    record_dead_letter_depth,
    record_publish_failure,
    record_publish_success,
)

try:  # pragma: no cover - optional dependency
    from kafka import KafkaProducer
except ImportError:  # pragma: no cover - optional dependency
    KafkaProducer = None  # type: ignore

logger = logging.getLogger(__name__)


class Producer(Protocol):
    def send(self, topic: str, value: bytes) -> Any:  # pragma: no cover - interface definition
        ...


@dataclass
class QueueMessage:
    notification_id: int
    channel: str
    payload: dict[str, Any]
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DeadLetterQueue(Protocol):
    topic: str

    def send(self, message: QueueMessage, reason: str) -> None:  # pragma: no cover - interface definition
        ...

    def depth(self) -> int:  # pragma: no cover - interface definition
        ...


@dataclass
class DeadLetterEntry:
    message: QueueMessage
    reason: str
    failed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationQueue:
    """Abstraction around the outbound notification queue."""

    def __init__(
        self,
        producer: Producer,
        topic: str,
        *,
        dead_letter_queue: DeadLetterQueue | None = None,
    ) -> None:
        self.producer = producer
        self.topic = topic
        self.dead_letter_queue = dead_letter_queue

    def enqueue(self, message: QueueMessage) -> None:
        data = {
            "notification_id": message.notification_id,
            "channel": message.channel,
            "payload": message.payload,
        }
        body = current_app.json.dumps(data).encode("utf-8")

        try:
            result = self.producer.send(self.topic, value=body)
        except Exception as exc:  # pragma: no cover - exercised via tests
            self._handle_failure(message, exc)
            return

        if hasattr(result, "add_callback") and hasattr(result, "add_errback"):
            result.add_callback(lambda _metadata: self._handle_success(message))  # type: ignore[arg-type]
            result.add_errback(lambda exc: self._handle_failure(message, exc))  # type: ignore[arg-type]
        else:
            self._handle_success(message)

    def _handle_success(self, message: QueueMessage) -> None:
        lag_seconds = max((datetime.now(timezone.utc) - message.enqueued_at).total_seconds(), 0.0)
        record_publish_success(self.topic, lag_seconds)
        if self.dead_letter_queue is not None:
            record_dead_letter_depth(self.dead_letter_queue.topic, self.dead_letter_queue.depth())

    def _handle_failure(self, message: QueueMessage, exc: Exception) -> None:
        logger.warning(
            "Failed to enqueue notification",  # pragma: no cover - logging path
            exc_info=exc,
            extra={
                "notification_id": message.notification_id,
                "channel": message.channel,
            },
        )
        record_publish_failure(self.topic)
        if self.dead_letter_queue is None:
            return
        try:
            self.dead_letter_queue.send(message, str(exc))
        except Exception as dlq_exc:  # pragma: no cover - defensive guard
            logger.error("Failed to publish message to dead-letter queue", exc_info=dlq_exc)
        finally:
            record_dead_letter_depth(self.dead_letter_queue.topic, self.dead_letter_queue.depth())


class InMemoryQueue:
    """Simple queue backend used for tests and local development."""

    def __init__(self) -> None:
        self.messages: list[QueueMessage] = []

    def send(self, topic: str, value: bytes) -> None:  # type: ignore[override]
        payload = current_app.json.loads(value.decode("utf-8"))
        self.messages.append(
            QueueMessage(
                notification_id=payload["notification_id"],
                channel=payload["channel"],
                payload=payload["payload"],
            )
        )


class InMemoryDeadLetterQueue:
    """Dead-letter queue that keeps entries in memory for diagnostics/tests."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.entries: list[DeadLetterEntry] = []

    def send(self, message: QueueMessage, reason: str) -> None:
        self.entries.append(DeadLetterEntry(message=message, reason=reason))

    def depth(self) -> int:
        return len(self.entries)


class KafkaDeadLetterQueue:
    """Dead-letter queue that reuses the Kafka producer for fallback."""

    def __init__(self, producer: Producer, topic: str, source_topic: str) -> None:
        self._producer = producer
        self.topic = topic
        self._source_topic = source_topic
        self._approx_depth = 0

    def send(self, message: QueueMessage, reason: str) -> None:
        payload = {
            "notification_id": message.notification_id,
            "channel": message.channel,
            "payload": message.payload,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "original_topic": self._source_topic,
            "reason": reason,
        }
        body = current_app.json.dumps(payload).encode("utf-8")
        self._producer.send(self.topic, value=body)
        self._approx_depth += 1

    def depth(self) -> int:
        return self._approx_depth


def build_queue(topic: str | None = None) -> NotificationQueue:
    topic_name = topic or current_app.config.get("KAFKA_NOTIFICATION_TOPIC", "notifications.dispatch")
    dlq_topic = current_app.config.get("KAFKA_DLQ_TOPIC", f"{topic_name}.dlq")

    producer = current_app.config.get("KAFKA_PRODUCER")
    dead_letter_queue = current_app.config.get("KAFKA_DEAD_LETTER_QUEUE")

    if isinstance(producer, NotificationQueue):  # pragma: no cover - defensive branch
        return producer

    if producer is not None and not isinstance(producer, KafkaProducer):
        if not isinstance(dead_letter_queue, InMemoryDeadLetterQueue):
            dead_letter_queue = InMemoryDeadLetterQueue(dlq_topic)
            current_app.config["KAFKA_DEAD_LETTER_QUEUE"] = dead_letter_queue
        return NotificationQueue(producer, topic_name, dead_letter_queue=dead_letter_queue)

    bootstrap = current_app.config.get("KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap and KafkaProducer is not None:
        kafka_kwargs = _build_kafka_security_kwargs()
        kafka_producer = KafkaProducer(bootstrap_servers=_as_list(bootstrap), **kafka_kwargs)  # pragma: no cover - requires kafka
        current_app.config["KAFKA_PRODUCER"] = kafka_producer
        dead_letter_queue = KafkaDeadLetterQueue(kafka_producer, dlq_topic, topic_name)
        current_app.config["KAFKA_DEAD_LETTER_QUEUE"] = dead_letter_queue
        return NotificationQueue(kafka_producer, topic_name, dead_letter_queue=dead_letter_queue)

    # Default to the in-memory queue so development and tests can run without Kafka.
    queue_backend = InMemoryQueue()
    current_app.config.setdefault("KAFKA_IN_MEMORY_QUEUE", queue_backend)
    dead_letter_queue = InMemoryDeadLetterQueue(dlq_topic)
    current_app.config["KAFKA_DEAD_LETTER_QUEUE"] = dead_letter_queue
    return NotificationQueue(queue_backend, topic_name, dead_letter_queue=dead_letter_queue)


def _build_kafka_security_kwargs() -> dict[str, Any]:
    """Build security kwargs for Kafka producers from app config."""

    config = current_app.config
    kwargs: dict[str, Any] = {}
    security_protocol = config.get("KAFKA_SECURITY_PROTOCOL")
    if security_protocol:
        kwargs["security_protocol"] = security_protocol
    sasl_mechanism = config.get("KAFKA_SASL_MECHANISM")
    if sasl_mechanism:
        kwargs["sasl_mechanism"] = sasl_mechanism
    username = config.get("KAFKA_SASL_USERNAME")
    password = config.get("KAFKA_SASL_PASSWORD")
    if username and password:
        kwargs["sasl_plain_username"] = username
        kwargs["sasl_plain_password"] = password
    return kwargs


def _as_list(servers: str | Iterable[str]) -> list[str]:
    if isinstance(servers, str):
        return [s.strip() for s in servers.split(",") if s.strip()]
    return list(servers)


__all__ = [
    "DeadLetterEntry",
    "InMemoryDeadLetterQueue",
    "InMemoryQueue",
    "KafkaDeadLetterQueue",
    "NotificationQueue",
    "QueueMessage",
    "build_queue",
]
