from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_invoice(client: TestClient) -> None:
    response = client.post(
        "/payments/invoices",
        json={
            "id": "inv_1",
            "subscription_id": "sub_123",
            "amount": 100.0,
            "currency": "usd",
            "provider": "stripe",
        },
    )
    assert response.status_code == 201
    payload = response.json()["invoice"]
    assert payload["invoice_id"] == "inv_1"
    assert payload["status"] == "sent"


def test_issue_refund(client: TestClient) -> None:
    response = client.post(
        "/payments/refunds",
        json={
            "payment_id": "pay_1",
            "amount": 100.0,
            "currency": "usd",
            "provider": "paypal",
            "reason": "requested_by_customer",
        },
    )
    assert response.status_code == 202
    payload = response.json()["refund"]
    assert payload["payment_id"] == "pay_1"
    assert payload["provider"] == "paypal"

