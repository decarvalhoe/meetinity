from __future__ import annotations

from datetime import datetime, timezone

from datetime import datetime, timezone

from src.models import AnalyticsEvent


def test_ingest_single_event(client, session):
    payload = {
        "event_type": "booking.started",
        "user_id": "42",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"plan": "premium"},
    }
    response = client.post("/ingest/events", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["event_type"] == "booking.started"

    stored = session.query(AnalyticsEvent).all()
    assert len(stored) == 1
    assert stored[0].payload["plan"] == "premium"


def test_ingest_batch(client, session):
    now = datetime.now(timezone.utc)
    events = [
        {
            "event_type": "booking.started",
            "occurred_at": now.isoformat(),
        },
        {
            "event_type": "booking.completed",
            "occurred_at": now.isoformat(),
        },
    ]
    response = client.post("/ingest/batch", json={"events": events})
    assert response.status_code == 200
    data = response.get_json()
    assert data["ingested"] == 2

    stored = session.query(AnalyticsEvent).count()
    assert stored >= 2
