"""Data models for the payment service."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class Subscription(BaseModel):
    """Represent a subscription lifecycle."""

    subscription_id: str = Field(..., alias="id")
    customer_id: str
    plan_id: str
    status: str = Field(default="pending")
    provider: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Invoice(BaseModel):
    """Represent an invoice."""

    invoice_id: str = Field(..., alias="id")
    subscription_id: str
    amount: float
    currency: str = Field(default="usd")
    provider: str
    status: str = Field(default="draft")
    issued_at: datetime = Field(default_factory=datetime.utcnow)


class Refund(BaseModel):
    """Represent a refund operation."""

    refund_id: str = Field(..., alias="id")
    payment_id: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: str = Field(default="refunded")
    provider: str
    reason: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["Subscription", "Invoice", "Refund"]

