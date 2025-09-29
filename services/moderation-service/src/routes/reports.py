"""User-facing moderation report endpoints."""
from __future__ import annotations

from typing import Any, Mapping

from flask import Blueprint, current_app, jsonify, request

from ..config import ModerationConfig
from ..database import session_scope
from ..services.cases import ModerationCaseService, get_case, get_appeal
from ..services.filters import FilterResult

reports_bp = Blueprint("reports", __name__)


def _get_payload() -> Mapping[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, Mapping):
        return {}
    return data


@reports_bp.post("")
def create_report():
    payload = _get_payload()
    content_type = payload.get("content_type")
    content_reference = payload.get("content_reference")
    if not isinstance(content_type, str) or not isinstance(content_reference, str):
        return jsonify({"error": "Type et référence du contenu requis."}), 400

    reporter_id = payload.get("reporter_id")
    reporter_id = int(reporter_id) if reporter_id is not None else None
    summary = payload.get("summary") if isinstance(payload.get("summary"), str) else None
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else None
    filter_payload = payload.get("filter_result") if isinstance(payload.get("filter_result"), Mapping) else None

    filter_result = None
    if filter_payload:
        filter_result = FilterResult(
            status=str(filter_payload.get("status", "needs_review")),
            score=float(filter_payload.get("score", 0.0)),
            labels=dict(filter_payload.get("labels", {})),
            reasons=list(filter_payload.get("reasons", [])),
        )

    config = ModerationConfig.from_app(current_app)
    with session_scope() as session:
        service = ModerationCaseService(session, config)
        case = service.create_report(
            content_type=content_type,
            content_reference=content_reference,
            reporter_id=reporter_id,
            source=payload.get("source"),
            summary=summary,
            context=metadata,
            filter_result=filter_result,
        )
        session.commit()
        return jsonify(_serialize_case(case)), 201


@reports_bp.post("/<int:case_id>/assign")
def assign_case(case_id: int):
    payload = _get_payload()
    reviewer = payload.get("reviewer")
    actor = payload.get("actor")
    if not reviewer or not actor:
        return jsonify({"error": "Reviewer et acteur requis."}), 400

    config = ModerationConfig.from_app(current_app)
    with session_scope() as session:
        case = get_case(session, case_id)
        service = ModerationCaseService(session, config)
        service.assign_case(case, reviewer=reviewer, actor=actor)
        session.commit()
        return jsonify(_serialize_case(case)), 200


@reports_bp.post("/<int:case_id>/decision")
def resolve_case(case_id: int):
    payload = _get_payload()
    status = payload.get("status")
    actor = payload.get("actor")
    if status not in {"action_taken", "dismissed", "escalated"} or not actor:
        return jsonify({"error": "Statut ou acteur invalide."}), 400

    config = ModerationConfig.from_app(current_app)
    with session_scope() as session:
        case = get_case(session, case_id)
        service = ModerationCaseService(session, config)
        service.resolve_case(case, status=status, actor=actor, notes=payload.get("notes"))
        session.commit()
        return jsonify(_serialize_case(case)), 200


@reports_bp.post("/<int:case_id>/appeals")
def create_appeal(case_id: int):
    payload = _get_payload()
    submitted_by = payload.get("submitted_by")
    reason = payload.get("reason")
    if not submitted_by or not reason:
        return jsonify({"error": "L'appel requiert un auteur et une raison."}), 400

    config = ModerationConfig.from_app(current_app)
    with session_scope() as session:
        case = get_case(session, case_id)
        service = ModerationCaseService(session, config)
        appeal = service.create_appeal(case, submitted_by=submitted_by, reason=reason)
        session.commit()
        return jsonify(_serialize_appeal(appeal)), 201


@reports_bp.post("/appeals/<int:appeal_id>/decision")
def resolve_appeal(appeal_id: int):
    payload = _get_payload()
    reviewer = payload.get("reviewer")
    decision = payload.get("decision")
    if decision not in {"upheld", "overturned"} or not reviewer:
        return jsonify({"error": "Décision ou reviewer invalide."}), 400

    config = ModerationConfig.from_app(current_app)
    with session_scope() as session:
        appeal = get_appeal(session, appeal_id)
        service = ModerationCaseService(session, config)
        service.resolve_appeal(
            appeal,
            decision=decision,
            reviewer=reviewer,
            notes=payload.get("notes"),
        )
        session.commit()
        return jsonify(_serialize_appeal(appeal)), 200


def _serialize_case(case) -> dict[str, Any]:
    return {
        "id": case.id,
        "content_type": case.content_type,
        "content_reference": case.content_reference,
        "status": case.status,
        "reporter_id": case.reporter_id,
        "source": case.source,
        "summary": case.summary,
        "metadata": case.context or {},
        "assigned_reviewer": case.assigned_reviewer,
        "automated_score": case.automated_score,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


def _serialize_appeal(appeal) -> dict[str, Any]:
    return {
        "id": appeal.id,
        "case_id": appeal.case_id,
        "submitted_by": appeal.submitted_by,
        "reason": appeal.reason,
        "status": appeal.status,
        "decision": appeal.status,
        "reviewer": appeal.reviewer,
        "resolution_notes": appeal.resolution_notes,
        "created_at": appeal.created_at.isoformat(),
        "resolved_at": appeal.resolved_at.isoformat() if appeal.resolved_at else None,
    }
