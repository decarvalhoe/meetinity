"""Notification queue integrations (Kafka or in-memory fallback)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from flask import current_app

try:  # pragma: no cover - optional dependency
    from kafka import KafkaProducer
except ImportError:  # pragma: no cover - optional dependency
    KafkaProducer = None  # type: ignore


class Producer(Protocol):
    def send(self, topic: str, value: bytes) -> Any:  # pragma: no cover - interface definition
        ...


@dataclass
class QueueMessage:
    notification_id: int
    channel: str
    payload: dict[str, Any]


class NotificationQueue:
    """Abstraction around the outbound notification queue."""

    def __init__(self, producer: Producer, topic: str):
        self.producer = producer
        self.topic = topic

    def enqueue(self, message: QueueMessage) -> None:
        data = {
            "notification_id": message.notification_id,
            "channel": message.channel,
            "payload": message.payload,
        }
        body = current_app.json.dumps(data).encode("utf-8")
        self.producer.send(self.topic, value=body)


class InMemoryQueue:
    """Simple queue backend used for tests and local development."""

    def __init__(self):
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


def build_queue(topic: str | None = None) -> NotificationQueue | InMemoryQueue:
    topic_name = topic or current_app.config.get("KAFKA_NOTIFICATION_TOPIC", "notifications.dispatch")
    producer = current_app.config.get("KAFKA_PRODUCER")
    if producer is not None:
        return NotificationQueue(producer, topic_name)

    bootstrap = current_app.config.get("KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap and KafkaProducer is not None:
        producer = KafkaProducer(bootstrap_servers=_as_list(bootstrap))  # pragma: no cover - requires kafka
        return NotificationQueue(producer, topic_name)

    # Default to the in-memory queue so development and tests can run without Kafka.
    queue = InMemoryQueue()
    current_app.config.setdefault("KAFKA_IN_MEMORY_QUEUE", queue)
    return queue


def _as_list(servers: str | Iterable[str]) -> list[str]:
    if isinstance(servers, str):
        return [s.strip() for s in servers.split(",") if s.strip()]
    return list(servers)
