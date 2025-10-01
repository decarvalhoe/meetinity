from __future__ import annotations

from typing import Any

from flask import Response

from src.integrations import ModerationClient, ModerationResponse, NotificationClient


def auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_id}"}


def _post_json(client, url: str, payload: dict[str, Any], user_id: int) -> Response:
    return client.post(url, json=payload, headers=auth_header(user_id))


def _get_json(client, url: str, user_id: int) -> Response:
    return client.get(url, headers=auth_header(user_id))


def test_create_conversation_with_initial_message(client):
    response = _post_json(
        client,
        "/conversations",
        {"participant_id": 2, "initial_message": "Bonjour"},
        user_id=1,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["last_message"]["text"] == "Bonjour"
    assert data["last_message"]["attachment"] is None
    assert data["unread_count"] == 0

    # Should appear in conversation list
    list_response = _get_json(client, "/conversations", user_id=1)
    assert list_response.status_code == 200
    conversations = list_response.get_json()["conversations"]
    assert len(conversations) == 1
    assert conversations[0]["id"] == data["id"]


def test_post_message_and_fetch_thread(client):
    create_response = _post_json(client, "/conversations", {"participant_id": 2}, user_id=1)
    conversation_id = create_response.get_json()["id"]

    send_response = _post_json(
        client,
        f"/conversations/{conversation_id}/messages",
        {"text": "Salut"},
        user_id=2,
    )
    assert send_response.status_code == 201
    message = send_response.get_json()
    assert message["conversation_id"] == conversation_id
    assert message["sender_id"] == 2
    assert message["moderation_status"] == "approved"
    assert message["moderation_labels"] == {}
    assert message["attachment"] is None

    list_response = _get_json(client, f"/conversations/{conversation_id}/messages", user_id=1)
    assert list_response.status_code == 200
    messages = list_response.get_json()["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "Salut"
    assert messages[0]["attachment"] is None


def test_mark_read_resets_unread_count(client):
    create_response = _post_json(
        client,
        "/conversations",
        {"participant_id": 2, "initial_message": "Salut"},
        user_id=1,
    )
    conversation_id = create_response.get_json()["id"]

    # Participant 2 has one unread message
    list_as_participant = _get_json(client, "/conversations", user_id=2)
    unread_before = list_as_participant.get_json()["conversations"][0]["unread_count"]
    assert unread_before == 1

    mark_response = client.post(
        f"/conversations/{conversation_id}/read",
        headers=auth_header(2),
    )
    assert mark_response.status_code == 204

    list_after = _get_json(client, "/conversations", user_id=2)
    unread_after = list_after.get_json()["conversations"][0]["unread_count"]
    assert unread_after == 0


def test_moderation_blocks_message(monkeypatch, app):
    app.config["MODERATION_SERVICE_URL"] = "http://moderation.local"

    def fake_enabled(self):
        return True

    def fake_review(self, text, **context):
        return ModerationResponse(status="blocked", score=0.99, labels={"reason": "policy"})

    monkeypatch.setattr(ModerationClient, "is_enabled", fake_enabled)
    monkeypatch.setattr(ModerationClient, "review_message", fake_review)

    client = app.test_client()
    response = _post_json(
        client,
        "/conversations",
        {"participant_id": 2, "initial_message": "contenu interdit"},
        user_id=1,
    )
    assert response.status_code == 400
    body = response.get_json()
    assert "Le message a été bloqué" in body["details"]["initial_message"][0]


def test_send_message_with_attachment_flow(client):
    create_response = _post_json(client, "/conversations", {"participant_id": 2}, user_id=1)
    conversation_id = create_response.get_json()["id"]

    upload_response = _post_json(
        client,
        f"/conversations/{conversation_id}/attachments",
        {"file_name": "photo.png", "size": 2048, "encryption_key": "secret-key"},
        user_id=1,
    )
    assert upload_response.status_code == 201
    upload_data = upload_response.get_json()

    attachment_payload = {
        "url": upload_data["file_url"],
        "size": upload_data["size"],
        "encryption_key": upload_data["encryption_key"],
    }

    send_response = _post_json(
        client,
        f"/conversations/{conversation_id}/messages",
        {"text": "Voici le fichier", "attachment": attachment_payload},
        user_id=2,
    )
    assert send_response.status_code == 201
    message = send_response.get_json()
    assert message["attachment"]["url"] == attachment_payload["url"]
    assert message["attachment"]["size"] == 2048

    download_response = client.get(
        f"/conversations/{conversation_id}/attachments/{message['id']}",
        headers=auth_header(1),
    )
    assert download_response.status_code == 200
    metadata = download_response.get_json()
    assert metadata["url"] == attachment_payload["url"]
    assert metadata["encryption_key"] == "secret-key"


def test_websocket_event_and_notification_published(
    client, socketio_client, monkeypatch, app
):
    app.config["NOTIFICATION_SERVICE_URL"] = "http://notification.local"

    monkeypatch.setattr(NotificationClient, "is_enabled", lambda self: True)
    published: dict[str, Any] = {}

    def fake_publish(self, **payload):
        published.update(payload)

    monkeypatch.setattr(NotificationClient, "publish_new_message", fake_publish)

    create_response = _post_json(client, "/conversations", {"participant_id": 2}, user_id=1)
    conversation_id = create_response.get_json()["id"]

    socketio_client.emit("join_conversation", {"conversation_id": conversation_id})
    socketio_client.get_received()  # drain join ack

    send_response = _post_json(
        client,
        f"/conversations/{conversation_id}/messages",
        {"text": "Salut temps réel"},
        user_id=2,
    )
    assert send_response.status_code == 201

    events = socketio_client.get_received()
    assert any(event["name"] == "message.created" for event in events)
    created_events = [event for event in events if event["name"] == "message.created"]
    assert created_events
    payload = created_events[-1]["args"][0]
    assert payload["text"] == "Salut temps réel"

    assert published["conversation_id"] == conversation_id
    assert published["sender_id"] == 2
    assert published["recipient_id"] == 1
