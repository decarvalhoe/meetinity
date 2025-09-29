"""Pydantic schemas for request validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class EventPayload(BaseModel):
    event_type: str = Field(..., description="Canonical analytics event name")
    occurred_at: datetime = Field(..., description="Event timestamp in ISO-8601 format")
    user_id: Optional[str] = Field(None, description="User identifier when available")
    ingestion_id: Optional[str] = Field(None, description="Idempotency key supplied by producers")
    source: str = Field("http", description="Event source channel")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary event attributes")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual metadata such as device or locale")

    @validator("event_type")
    def _normalize_event_type(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("event_type must be provided")
        return normalized


class BatchIngestRequest(BaseModel):
    events: List[EventPayload]

    @validator("events")
    def _non_empty(cls, value: List[EventPayload]) -> List[EventPayload]:
        if not value:
            raise ValueError("events must contain at least one event")
        return value


class KpiRequest(BaseModel):
    kpis: List[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RefreshRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    force_recompute: bool = False
