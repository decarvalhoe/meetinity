from datetime import date, datetime, timedelta

from src.database import get_session
from src.models import Event, NoShowPenalty


def create_event(client, **overrides):
    payload = {
        "title": "Capacity Test",
        "date": (date.today() + timedelta(days=7)).isoformat(),
        "location": "Paris",
        "type": "workshop",
        "attendees": 2,
    }
    payload.update(overrides)
    response = client.post("/events", json=payload)
    assert response.status_code == 201
    return response.json["event_id"]


def join_event(client, event_id, email, name):
    response = client.post(
        f"/events/{event_id}/join",
        json={"email": email, "name": name},
    )
    return response


def cancel_event_registration(client, event_id, registration_id):
    response = client.delete(
        f"/events/{event_id}/join",
        query_string={"registration_id": registration_id},
    )
    return response


def test_join_event_handles_confirmation_and_waitlist(client):
    event_id = create_event(client, attendees=1)

    first = join_event(client, event_id, "alice@example.com", "Alice")
    assert first.status_code == 200
    assert first.json["success"] is True
    assert first.json["registration_id"]

    second = join_event(client, event_id, "bob@example.com", "Bob")
    assert second.status_code == 202
    assert second.json["status"] == "waitlisted"

    waitlist = client.get(f"/events/{event_id}/waitlist")
    assert waitlist.status_code == 200
    emails = [entry["email"] for entry in waitlist.json["waitlist"]]
    assert "bob@example.com" in emails


def test_waitlist_promotion_on_cancellation(client):
    event_id = create_event(client, attendees=1)

    confirmed = join_event(client, event_id, "first@example.com", "First")
    waitlisted = join_event(client, event_id, "second@example.com", "Second")
    assert confirmed.status_code == 200
    assert waitlisted.status_code == 202

    registration_id = confirmed.json["registration_id"]
    cancel = cancel_event_registration(client, event_id, registration_id)
    assert cancel.status_code == 200
    promoted = cancel.json.get("promoted", [])
    assert any(item["email"] == "second@example.com" for item in promoted)

    registrations = client.get(f"/events/{event_id}/registrations")
    assert registrations.status_code == 200
    statuses = {item["email"]: item["status"] for item in registrations.json["registrations"]}
    assert statuses.get("second@example.com") == "confirmed"


def test_join_event_rejects_when_closed(client):
    event_id = create_event(client, attendees=1)

    session = get_session()
    try:
        event = session.get(Event, event_id)
        event.registration_open = False
        session.commit()
    finally:
        session.close()

    response = join_event(client, event_id, "closed@example.com", "Closed")
    assert response.status_code == 403
    assert "fermées" in response.json["error"]["message"]


def test_join_event_prevents_duplicates(client):
    event_id = create_event(client, attendees=2)

    first = join_event(client, event_id, "duplicate@example.com", "Dup")
    assert first.status_code == 200

    second = join_event(client, event_id, "duplicate@example.com", "Dup")
    assert second.status_code == 409
    assert "déjà inscrit" in second.json["error"]["message"]


def test_join_event_blocks_penalized_attendees(client):
    event_id = create_event(client, attendees=2)
    blocked_email = "penalty@example.com"

    session = get_session()
    try:
        penalty = NoShowPenalty(
            attendee_email=blocked_email,
            event_id=event_id,
            reason="Previous no-show",
            expires_at=datetime.utcnow() + timedelta(days=5),
        )
        session.add(penalty)
        session.commit()
    finally:
        session.close()

    response = join_event(client, event_id, blocked_email, "Blocked")
    assert response.status_code == 403
    assert "bloqué" in response.json["error"]["message"]
