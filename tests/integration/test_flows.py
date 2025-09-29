from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt
import pytest
import requests

USER_ID = 9000
USER_EMAIL = "alice.martin@example.com"
USER_PROVIDER = "google"
EVENT_ID = 500
TARGET_USER_ID = 9001


@pytest.fixture(scope="session")
def auth_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": USER_ID,
        "email": USER_EMAIL,
        "provider": USER_PROVIDER,
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }
    return jwt.encode(payload, "change_me", algorithm="HS256")


@pytest.fixture(scope="session")
def auth_headers(auth_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.integration
@pytest.mark.usefixtures("docker_stack")
def test_login_flow_through_gateway(gateway_base_url: str, auth_token: str) -> None:
    response = requests.post(
        f"{gateway_base_url}/api/auth/verify",
        json={"token": auth_token},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    assert payload["valid"] is True
    assert payload["sub"] == USER_ID


@pytest.mark.integration
@pytest.mark.usefixtures("docker_stack")
def test_event_registration_roundtrip(gateway_base_url: str, auth_headers: Dict[str, str]) -> None:
    attendee_email = "integration.attendee@example.com"
    join_response = requests.post(
        f"{gateway_base_url}/api/events/events/{EVENT_ID}/join",
        headers=auth_headers,
        json={"email": attendee_email, "name": "Integration Attendee"},
        timeout=30,
    )
    join_response.raise_for_status()
    registration = join_response.json()
    assert registration["success"] is True
    registration_id = registration["registration_id"]
    assert registration_id

    list_response = requests.get(
        f"{gateway_base_url}/api/events/events/{EVENT_ID}/registrations",
        headers=auth_headers,
        timeout=30,
    )
    list_response.raise_for_status()
    registrations = list_response.json()["registrations"]
    assert any(item["attendee_email"] == attendee_email for item in registrations)

    cancel_response = requests.delete(
        f"{gateway_base_url}/api/events/events/{EVENT_ID}/join",
        headers=auth_headers,
        params={"registration_id": registration_id},
        timeout=30,
    )
    cancel_response.raise_for_status()
    cancel_payload = cancel_response.json()
    assert cancel_payload["success"] is True


@pytest.mark.integration
@pytest.mark.usefixtures("docker_stack")
def test_swipe_flow_triggers_match(gateway_base_url: str, auth_headers: Dict[str, str]) -> None:
    response = requests.post(
        f"{gateway_base_url}/api/matching/swipe",
        headers=auth_headers,
        json={"user_id": USER_ID, "target_id": TARGET_USER_ID, "action": "like"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    assert payload["user_id"] == USER_ID
    assert payload["target_id"] == TARGET_USER_ID
    assert payload["action"] == "like"
    assert payload["is_match"] is True
    assert payload.get("match_score") is not None
