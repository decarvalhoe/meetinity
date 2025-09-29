from __future__ import annotations

from datetime import datetime, timezone

from src.consumers import AnalyticsEventConsumer
from src.models import AnalyticsEvent


def test_consumer_processes_message(session):
    consumer = AnalyticsEventConsumer(session)
    message = {
        "event_type": "booking.started",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "user_id": "900",
    }
    processed = consumer.consume(message)
    assert processed == 1

    stored = session.query(AnalyticsEvent).count()
    assert stored == 1


def test_consumer_handles_string_payload(session):
    consumer = AnalyticsEventConsumer(session)
    message = {
        "payload": "{\"event_type\": \"booking.completed\", \"occurred_at\": \"%s\"}" % datetime.now(timezone.utc).isoformat()
    }
    processed = consumer.consume(message)
    assert processed == 1

    stored = session.query(AnalyticsEvent).filter_by(event_type="booking.completed").count()
    assert stored == 1
