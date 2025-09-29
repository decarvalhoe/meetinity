"""HTTP endpoints for event ingestion."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from .. import schemas
from .dependencies import get_ingestion_service


ingestion_bp = Blueprint("analytics_ingestion", __name__)


@ingestion_bp.post("/events")
def ingest_event():
    payload = schemas.EventPayload(**request.get_json(force=True))
    service = get_ingestion_service()
    event = service.ingest(payload)
    return jsonify({"id": event.id, "event_type": event.event_type, "received_at": event.received_at.isoformat()}), 201


@ingestion_bp.post("/batch")
def ingest_batch():
    payload = schemas.BatchIngestRequest(**request.get_json(force=True))
    service = get_ingestion_service()
    events = service.ingest_batch(payload.events)
    return jsonify({"ingested": len(events)})
