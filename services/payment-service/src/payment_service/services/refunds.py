"""Refund orchestration."""
from __future__ import annotations

from typing import Any, Mapping

from ..audit import audit_event
from ..gateways.paypal import PayPalGateway
from ..gateways.stripe import StripeGateway
from ..models import Refund


class RefundService:
    """Processes refunds across providers."""

    def __init__(self) -> None:
        self._gateways = {
            "stripe": StripeGateway(),
            "paypal": PayPalGateway(),
        }

    def issue(self, payload: Mapping[str, Any]) -> Refund:
        gateway = self._select_gateway(payload.get("provider"))
        response = gateway.refund_payment(payload)
        refund = Refund(
            id=str(payload.get("refund_id", payload.get("payment_id"))),
            payment_id=str(payload.get("payment_id")),
            amount=payload.get("amount"),
            currency=payload.get("currency"),
            provider=gateway.__class__.__name__.replace("Gateway", "").lower(),
            reason=payload.get("reason"),
            status=response.get("status", "refunded"),
        )
        audit_event(
            "refund_issued",
            {
                "payment_id": refund.payment_id,
                "refund_id": refund.refund_id,
                "provider": refund.provider,
                "status": refund.status,
            },
        )
        return refund

    def _select_gateway(self, provider: str | None) -> StripeGateway | PayPalGateway:
        key = (provider or "stripe").lower()
        try:
            return self._gateways[key]
        except KeyError as exc:  # pragma: no cover - guard rail
            raise ValueError(f"Unknown provider '{provider}'") from exc


__all__ = ["RefundService"]

