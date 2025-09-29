from datetime import datetime, timezone

import pytest

from src.metrics import DLQ_DEPTH, PUBLISH_ATTEMPTS, QUEUE_LAG_SECONDS
from src.queue import (
    InMemoryDeadLetterQueue,
    InMemoryQueue,
    NotificationQueue,
    QueueMessage,
)

pytestmark = pytest.mark.eventdriven


class FailingProducer:
    def send(self, topic: str, value: bytes):  # pragma: no cover - exercised via tests
        raise RuntimeError("simulated failure")


def _metric_value(metric, **labels) -> float:
    return metric.labels(**labels)._value.get()  # type: ignore[attr-defined]


def test_successful_enqueue_updates_metrics(app):
    with app.app_context():
        queue_backend = InMemoryQueue()
        dlq = InMemoryDeadLetterQueue("notifications.dispatch.dlq")
        queue = NotificationQueue(queue_backend, "notifications.dispatch", dead_letter_queue=dlq)

        message = QueueMessage(
            notification_id=1,
            channel="email",
            payload={"body": "hello"},
            enqueued_at=datetime.now(timezone.utc),
        )

        queue.enqueue(message)

        assert len(queue_backend.messages) == 1
        assert _metric_value(PUBLISH_ATTEMPTS, topic="notifications.dispatch", result="published") == 1
        assert _metric_value(DLQ_DEPTH, topic="notifications.dispatch.dlq") == 0
        assert _metric_value(QUEUE_LAG_SECONDS, topic="notifications.dispatch") >= 0


def test_enqueue_failure_routes_to_dead_letter(app):
    with app.app_context():
        dlq = InMemoryDeadLetterQueue("notifications.dispatch.dlq")
        queue = NotificationQueue(FailingProducer(), "notifications.dispatch", dead_letter_queue=dlq)

        message = QueueMessage(notification_id=99, channel="sms", payload={})

        queue.enqueue(message)

        assert dlq.depth() == 1
        entry = dlq.entries[0]
        assert entry.message.notification_id == 99
        assert "simulated failure" in entry.reason
        assert _metric_value(PUBLISH_ATTEMPTS, topic="notifications.dispatch", result="failed") == 1
        assert _metric_value(DLQ_DEPTH, topic="notifications.dispatch.dlq") == 1
