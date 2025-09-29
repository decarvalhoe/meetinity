from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "services" / "payment-service" / "src"))

import os

os.environ.setdefault("STRIPE__API_KEY", "contract")
os.environ.setdefault("STRIPE__WEBHOOK_SECRET", "contract")
os.environ.setdefault("PAYPAL__API_KEY", "contract")
os.environ.setdefault("PAYPAL__WEBHOOK_SECRET", "contract")

from fastapi.testclient import TestClient

from payment_service.app import create_app


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_payment_contract_create_subscription_schema() -> None:
    client = _client()
    response = client.post(
        "/subscriptions",
        json={
            "id": "sub_contract",
            "customer_id": "cust_contract",
            "plan_id": "plan_contract",
        },
    )
    assert response.status_code == 201
    payload = response.json()["subscription"]
    assert {"subscription_id", "customer_id", "plan_id", "status"}.issubset(payload.keys())


def test_payment_contract_refund_flow() -> None:
    client = _client()
    response = client.post(
        "/payments/refunds",
        json={
            "payment_id": "pay_contract",
        },
    )
    assert response.status_code == 202
    body = response.json()["refund"]
    assert body["payment_id"] == "pay_contract"
    assert body["status"] == "refunded"

