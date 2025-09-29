"""Metadata endpoints exposing schemas and KPI catalog."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..services.warehouse import DEFAULT_KPIS


_SCHEMAS = {
    "event": {
        "description": "Canonical analytics event schema",
        "fields": {
            "event_type": "String identifier for the event name",
            "user_id": "Optional user identifier",
            "occurred_at": "ISO-8601 timestamp when the event occurred",
            "ingestion_id": "Idempotency key used to deduplicate events",
            "source": "Transport source such as http, kafka, or webhook",
            "payload": "Free-form JSON object describing event attributes",
            "context": "Additional metadata such as device, locale, or experiment ids",
        },
    }
}

_KPIS = {
    "events.total": "Total number of events received per day",
    "users.daily_active": "Distinct users who generated at least one event in the window",
    "funnel.booking_conversion": "Ratio of booking.completed over booking.started events",
}


metadata_bp = Blueprint("analytics_metadata", __name__)


@metadata_bp.get("/schemas")
def list_schemas():
    return jsonify({"schemas": _SCHEMAS})


@metadata_bp.get("/kpis")
def list_kpi_definitions():
    catalog = {name: _KPIS.get(name, "") for name in DEFAULT_KPIS}
    return jsonify({"kpis": catalog})
