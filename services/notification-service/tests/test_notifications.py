from datetime import datetime, timezone

from src.queue import InMemoryQueue


def auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_id}"}


def test_schedule_notification_respects_preferences(app, client):
    # Recipient disables SMS notifications
    response = client.put(
        "/preferences",
        json={"preferences": {"sms": False}},
        headers=auth_header(2),
    )
    assert response.status_code == 200

    payload = {
        "recipient_id": 2,
        "channels": ["email", "sms"],
        "template": "welcome",
        "payload": {"name": "Bob"},
    }
    response = client.post("/notifications", json=payload, headers=auth_header(1))
    assert response.status_code == 201
    data = response.get_json()
    assert data["channels"] == ["email"]
    assert len(data["deliveries"]) == 1
    assert data["deliveries"][0]["channel"] == "email"

    queue_backend: InMemoryQueue = app.config["KAFKA_PRODUCER"]
    assert len(queue_backend.messages) == 1
    assert queue_backend.messages[0].channel == "email"


def test_schedule_notification_all_channels_disabled(client):
    client.put(
        "/preferences",
        json={"preferences": {"email": False, "sms": False, "push": False, "in_app": False}},
        headers=auth_header(3),
    )

    response = client.post(
        "/notifications",
        json={
            "recipient_id": 3,
            "channels": ["email", "sms"],
            "template": "digest",
        },
        headers=auth_header(4),
    )
    assert response.status_code == 400
    body = response.get_json()
    assert body["message"] == "Aucun canal disponible."


def test_update_delivery_status(client):
    schedule_resp = client.post(
        "/notifications",
        json={
            "recipient_id": 5,
            "channels": ["email", "push"],
            "template": "reminder",
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
        },
        headers=auth_header(6),
    )
    assert schedule_resp.status_code == 201
    notification = schedule_resp.get_json()

    update_resp = client.post(
        f"/notifications/{notification['id']}/deliveries",
        json={"channel": "email", "status": "delivered", "detail": "SMTP 250 OK"},
        headers=auth_header(5),
    )
    assert update_resp.status_code == 200
    delivery = update_resp.get_json()
    assert delivery["status"] == "delivered"
    assert delivery["detail"] == "SMTP 250 OK"

    list_resp = client.get(
        f"/notifications/{notification['id']}/deliveries",
        headers=auth_header(5),
    )
    assert list_resp.status_code == 200
    deliveries = list_resp.get_json()["deliveries"]
    assert any(d["status"] == "delivered" for d in deliveries if d["channel"] == "email")


def test_list_notifications_requires_auth(client):
    response = client.get("/notifications")
    assert response.status_code == 401
