"""Invoice and refund endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.invoicing import InvoicingService
from ..services.refunds import RefundService


class CreateInvoiceRequest(BaseModel):
    invoice_id: str = Field(..., alias="id")
    subscription_id: str
    amount: float
    currency: str = Field(default="usd")
    provider: str = Field(default="stripe")


class RefundRequest(BaseModel):
    payment_id: str
    refund_id: str | None = Field(default=None, alias="id")
    amount: float | None = None
    currency: str | None = None
    provider: str = Field(default="stripe")
    reason: str | None = None


router = APIRouter(prefix="/payments", tags=["payments"])
invoicing = InvoicingService()
refunds = RefundService()


@router.post("/invoices", status_code=201)
async def create_invoice(body: CreateInvoiceRequest) -> dict[str, Any]:
    invoice = invoicing.create(body.model_dump(by_alias=True))
    return {"invoice": invoice.model_dump()}


@router.post("/refunds", status_code=202)
async def issue_refund(body: RefundRequest) -> dict[str, Any]:
    try:
        refund = refunds.issue(body.model_dump(by_alias=True, exclude_none=True))
    except ValueError as exc:  # pragma: no cover - guard rail
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"refund": refund.model_dump()}


__all__ = ["router"]

