"""Subscription lifecycle management."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from ..audit import audit_event
from ..gateways.paypal import PayPalGateway
from ..gateways.stripe import StripeGateway
from ..models import Subscription
from ..repository import SubscriptionRecord, SubscriptionRepository


class SubscriptionService:
    """Coordinates subscription lifecycle operations."""

    def __init__(self, repository: SubscriptionRepository | None = None) -> None:
        self._repository = repository or SubscriptionRepository()
        self._gateways = {
            "stripe": StripeGateway(),
            "paypal": PayPalGateway(),
        }

    def create(self, payload: Mapping[str, Any]) -> Subscription:
        provider = self._select_gateway(payload.get("provider"))
        response = provider.create_subscription(payload)
        subscription_id = str(payload.get("subscription_id") or payload.get("id"))
        subscription = Subscription(
            id=subscription_id,
            customer_id=str(payload.get("customer_id")),
            plan_id=str(payload.get("plan_id")),
            provider=provider.__class__.__name__.replace("Gateway", "").lower(),
            status=response.get("status", "active"),
            metadata={"provider_reference": response.get("subscription_id") or subscription_id},
        )
        record = SubscriptionRecord(
            subscription_id=subscription_id,
            customer_id=subscription.customer_id,
            plan_id=subscription.plan_id,
            status=subscription.status,
            metadata=subscription.metadata,
        )
        self._repository.upsert(record)
        audit_event(
            "subscription_created",
            {
                "subscription_id": subscription.subscription_id,
                "customer_id": subscription.customer_id,
                "provider": subscription.provider,
            },
        )
        return subscription

    def cancel(self, subscription_id: str, *, provider: str) -> Subscription:
        gateway = self._select_gateway(provider)
        response = gateway.cancel_subscription(subscription_id)
        record = self._repository.get(subscription_id)
        if record is None:
            record = SubscriptionRecord(
                subscription_id=subscription_id,
                customer_id="unknown",
                plan_id="unknown",
                status=response.get("status", "canceled"),
            )
        else:
            record.status = response.get("status", "canceled")
        self._repository.upsert(record)
        subscription = Subscription(
            id=record.subscription_id,
            customer_id=record.customer_id,
            plan_id=record.plan_id,
            status=record.status,
            provider=gateway.__class__.__name__.replace("Gateway", "").lower(),
            metadata=record.metadata,
        )
        audit_event(
            "subscription_canceled",
            {
                "subscription_id": subscription.subscription_id,
                "provider": subscription.provider,
            },
        )
        return subscription

    def _select_gateway(self, provider: str | None) -> StripeGateway | PayPalGateway:
        key = (provider or "stripe").lower()
        try:
            return self._gateways[key]
        except KeyError as exc:  # pragma: no cover - guard rail
            raise ValueError(f"Unknown provider '{provider}'") from exc


__all__ = ["SubscriptionService"]

