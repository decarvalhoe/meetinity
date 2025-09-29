"""Prometheus metrics for Kafka publishing health."""
from __future__ import annotations

from prometheus_client import Counter, Gauge

PUBLISH_ATTEMPTS = Counter(
    "notification_events_total",
    "Number of notification events published to Kafka",
    labelnames=("topic", "result"),
)

QUEUE_LAG_SECONDS = Gauge(
    "notification_queue_lag_seconds",
    "Observed enqueue lag for notification events",
    labelnames=("topic",),
)

DLQ_DEPTH = Gauge(
    "notification_dead_letter_queue_size",
    "Messages pending in the notification dead-letter queue",
    labelnames=("topic",),
)


def record_publish_success(topic: str, lag_seconds: float) -> None:
    """Record a successful enqueue with lag observations."""

    PUBLISH_ATTEMPTS.labels(topic=topic, result="published").inc()
    QUEUE_LAG_SECONDS.labels(topic=topic).set(max(lag_seconds, 0.0))


def record_publish_failure(topic: str) -> None:
    """Record a failed enqueue attempt."""

    PUBLISH_ATTEMPTS.labels(topic=topic, result="failed").inc()


def record_dead_letter_depth(topic: str, depth: int) -> None:
    """Update the DLQ depth gauge for the topic."""

    DLQ_DEPTH.labels(topic=topic).set(float(max(depth, 0)))


def reset_metrics() -> None:
    """Clear metric series (useful for tests)."""

    PUBLISH_ATTEMPTS._metrics.clear()  # type: ignore[attr-defined]
    QUEUE_LAG_SECONDS._metrics.clear()  # type: ignore[attr-defined]
    DLQ_DEPTH._metrics.clear()  # type: ignore[attr-defined]


__all__ = [
    "DLQ_DEPTH",
    "PUBLISH_ATTEMPTS",
    "QUEUE_LAG_SECONDS",
    "record_dead_letter_depth",
    "record_publish_failure",
    "record_publish_success",
    "reset_metrics",
]
