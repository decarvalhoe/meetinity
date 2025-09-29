"""Reporting API endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from .. import schemas
from .dependencies import get_reporting_service


reporting_bp = Blueprint("analytics_reporting", __name__)


@reporting_bp.get("/kpis")
def list_kpis():
    service = get_reporting_service()
    params = schemas.KpiRequest(**request.args.to_dict(flat=True)) if request.args else schemas.KpiRequest()
    snapshots = service.fetch_snapshots(
        params.kpis or None,
        start=params.start_date,
        end=params.end_date,
    )
    return jsonify({"kpis": snapshots})


@reporting_bp.post("/refresh")
def refresh_kpis():
    payload = schemas.RefreshRequest(**request.get_json(force=True))
    service = get_reporting_service()
    result = service.refresh(start=payload.start_date, end=payload.end_date, force=payload.force_recompute)
    return jsonify(result)
