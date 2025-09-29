"""Common abstractions for payment gateways."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class PaymentGateway(Protocol):
    """A payment provider client."""

    def create_subscription(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Create a subscription with the external provider."""

    def cancel_subscription(self, subscription_id: str) -> Mapping[str, Any]:
        """Cancel a subscription."""

    def invoice_subscription(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Create an invoice for the subscription."""

    def refund_payment(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Refund a payment."""


@dataclass(slots=True)
class GatewayResponse:
    """Wrapper for provider responses."""

    payload: Mapping[str, Any]


__all__ = ["PaymentGateway", "GatewayResponse"]

