"""Invoicing orchestration."""
from __future__ import annotations

from typing import Any, Mapping

from ..audit import audit_event
from ..gateways.paypal import PayPalGateway
from ..gateways.stripe import StripeGateway
from ..models import Invoice
from ..repository import InvoiceRepository


class InvoicingService:
    """Generates invoices across providers."""

    def __init__(self, repository: InvoiceRepository | None = None) -> None:
        self._repository = repository or InvoiceRepository()
        self._gateways = {
            "stripe": StripeGateway(),
            "paypal": PayPalGateway(),
        }

    def create(self, payload: Mapping[str, Any]) -> Invoice:
        gateway = self._select_gateway(payload.get("provider"))
        response = gateway.invoice_subscription(payload)
        invoice_id = str(payload.get("invoice_id") or payload.get("id"))
        subscription_id = str(payload.get("subscription_id") or payload.get("id"))
        invoice = Invoice(
            id=invoice_id,
            subscription_id=subscription_id,
            amount=float(payload.get("amount", 0)),
            currency=str(payload.get("currency", "usd")),
            provider=gateway.__class__.__name__.replace("Gateway", "").lower(),
            status="sent",
        )
        self._repository.save(invoice.invoice_id, invoice.model_dump(mode="json"))
        audit_event(
            "invoice_sent",
            {
                "invoice_id": invoice.invoice_id,
                "subscription_id": invoice.subscription_id,
                "provider": invoice.provider,
            },
        )
        return invoice

    def _select_gateway(self, provider: str | None) -> StripeGateway | PayPalGateway:
        key = (provider or "stripe").lower()
        try:
            return self._gateways[key]
        except KeyError as exc:  # pragma: no cover - guard rail
            raise ValueError(f"Unknown provider '{provider}'") from exc


__all__ = ["InvoicingService"]

