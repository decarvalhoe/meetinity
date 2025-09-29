"""Tests for the ingestion endpoints used by the user service."""

from __future__ import annotations

from src.main import app
from src.storage import get_user


def test_ingest_users_creates_profiles():
    payload = {
        "users": [
            {
                "id": 501,
                "email": "ingest-create@example.com",
                "full_name": "Ingest Create",
                "title": "Data Scientist",
                "company": "Meetinity",
                "preferences": {"skills": ["python", "ml"]},
            }
        ]
    }

    with app.test_client() as client:
        response = client.post("/internal/users", json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert body["ingested"] == 1
    stored_id = body["user_ids"][0]

    stored_user = get_user(stored_id)
    assert stored_user is not None
    assert stored_user.email == "ingest-create@example.com"
    assert any("python" in str(item).lower() for item in stored_user.preferences)


def test_ingest_users_updates_existing_profile():
    initial_payload = {
        "id": 777,
        "email": "ingest-update@example.com",
        "full_name": "Initial Name",
        "preferences": ["cloud"],
    }

    update_payload = {
        "id": 777,
        "email": "ingest-update@example.com",
        "full_name": "Updated Name",
        "preferences": {"skills": ["kafka"]},
    }

    with app.test_client() as client:
        first = client.post("/internal/users", json=initial_payload)
        assert first.status_code == 200
        second = client.post("/internal/users", json=update_payload)

    assert second.status_code == 200
    body = second.get_json()
    assert body["ingested"] == 1
    stored_user = get_user(777)
    assert stored_user is not None
    assert stored_user.full_name == "Updated Name"
    assert any("kafka" in str(item).lower() for item in stored_user.preferences)
