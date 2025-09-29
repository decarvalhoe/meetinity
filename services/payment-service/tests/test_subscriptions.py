from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_subscription(client: TestClient) -> None:
    response = client.post(
        "/subscriptions",
        json={
            "id": "sub_123",
            "customer_id": "cust_1",
            "plan_id": "plan_monthly",
            "provider": "stripe",
        },
    )
    assert response.status_code == 201
    payload = response.json()["subscription"]
    assert payload["subscription_id"] == "sub_123"
    assert payload["status"] == "active"


def test_cancel_subscription(client: TestClient) -> None:
    client.post(
        "/subscriptions",
        json={
            "id": "sub_456",
            "customer_id": "cust_2",
            "plan_id": "plan_annual",
            "provider": "paypal",
        },
    )
    response = client.post(
        "/subscriptions/sub_456/cancel",
        json={"provider": "paypal"},
    )
    assert response.status_code == 202
    payload = response.json()["subscription"]
    assert payload["subscription_id"] == "sub_456"
    assert payload["status"] == "canceled"

