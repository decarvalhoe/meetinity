from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _seed_events(client):
    base = datetime.now(timezone.utc)
    events = []
    for offset, event_type in enumerate(["booking.started", "booking.completed", "booking.started"]):
        events.append(
            {
                "event_type": event_type,
                "user_id": str(offset + 1),
                "occurred_at": (base + timedelta(minutes=offset)).isoformat(),
            }
        )
    client.post("/ingest/batch", json={"events": events})


def test_refresh_and_fetch_kpis(client, session):
    _seed_events(client)

    response = client.post("/reports/refresh", json={})
    assert response.status_code == 200
    assert response.get_json()["rows_materialised"] >= 3

    response = client.get("/reports/kpis")
    assert response.status_code == 200
    payload = response.get_json()
    assert any(item["kpi_name"] == "events.total" for item in payload["kpis"])


def test_refresh_force_recompute(client, session):
    _seed_events(client)
    client.post("/reports/refresh", json={})
    response = client.post("/reports/refresh", json={"force_recompute": True})
    assert response.status_code == 200
    assert response.get_json()["rows_materialised"] >= 3
