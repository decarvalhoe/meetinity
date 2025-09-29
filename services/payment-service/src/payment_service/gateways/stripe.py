"""Stripe integration shim."""
from __future__ import annotations

from typing import Any, Mapping

from ..config import get_settings
from .base import PaymentGateway


class StripeGateway(PaymentGateway):
    """Minimal Stripe adapter for the sandbox implementation."""

    def __init__(self) -> None:
        self._settings = get_settings().stripe

    def create_subscription(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        subscription_id = payload.get("subscription_id") or payload.get("id")
        return {
            "subscription_id": subscription_id,
            "status": "active",
            "provider": "stripe",
            "webhook_secret": self._settings.webhook_secret,
        }

    def cancel_subscription(self, subscription_id: str) -> Mapping[str, Any]:
        return {
            "subscription_id": subscription_id,
            "status": "canceled",
            "provider": "stripe",
        }

    def invoice_subscription(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "invoice_id": payload.get("invoice_id") or payload.get("id"),
            "subscription_id": payload.get("subscription_id") or payload.get("id"),
            "amount": payload.get("amount"),
            "currency": payload.get("currency", "usd"),
            "provider": "stripe",
        }

    def refund_payment(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "payment_id": payload.get("payment_id"),
            "status": "refunded",
            "provider": "stripe",
        }


__all__ = ["StripeGateway"]

