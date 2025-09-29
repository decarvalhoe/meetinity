from __future__ import annotations

from typing import Any

from flask import Response


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

    list_response = _get_json(client, f"/conversations/{conversation_id}/messages", user_id=1)
    assert list_response.status_code == 200
    messages = list_response.get_json()["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "Salut"


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
