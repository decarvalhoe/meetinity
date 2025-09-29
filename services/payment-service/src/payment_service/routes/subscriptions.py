"""Subscription endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.subscriptions import SubscriptionService


class CreateSubscriptionRequest(BaseModel):
    subscription_id: str = Field(..., alias="id")
    customer_id: str
    plan_id: str
    provider: str = Field(default="stripe")


class CancelSubscriptionRequest(BaseModel):
    provider: str = Field(default="stripe")


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
service = SubscriptionService()


@router.post("", status_code=201)
async def create_subscription(body: CreateSubscriptionRequest) -> dict[str, Any]:
    subscription = service.create(body.model_dump(by_alias=True))
    return {"subscription": subscription.model_dump()}


@router.post("/{subscription_id}/cancel", status_code=202)
async def cancel_subscription(subscription_id: str, body: CancelSubscriptionRequest) -> dict[str, Any]:
    try:
        subscription = service.cancel(subscription_id, provider=body.provider)
    except ValueError as exc:  # pragma: no cover - guard rail
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"subscription": subscription.model_dump()}


__all__ = ["router"]

