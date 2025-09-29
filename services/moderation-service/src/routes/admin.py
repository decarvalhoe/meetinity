"""Administrative endpoints for escalations and audits."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..config import ModerationConfig
from ..database import session_scope
from ..models import ModerationCase
from ..services.cases import ModerationCaseService, get_case

admin_bp = Blueprint("moderation_admin", __name__)


@admin_bp.post("/escalations")
def escalate_cases():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Payload JSON invalide."}), 400

    case_ids = payload.get("case_ids") or []
    reason = payload.get("reason") or "Escalade manuelle"
    actor = payload.get("actor") or "system"

    if not isinstance(case_ids, list) or not case_ids:
        return jsonify({"error": "Liste de cas requise."}), 400

    config = ModerationConfig.from_app(current_app)
    escalated: list[int] = []
    with session_scope() as session:
        service = ModerationCaseService(session, config)
        for case_id in case_ids:
            try:
                case = get_case(session, int(case_id))
            except (LookupError, ValueError):
                continue
            service.escalate_case(case, actor=actor, reason=reason)
            escalated.append(case.id)
    return jsonify({"escalated": escalated, "reason": reason}), 200


@admin_bp.get("/cases")
def list_cases():
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        return jsonify({"error": "Paramètre limit invalide."}), 400
    limit = max(1, min(limit, 200))

    with session_scope() as session:
        cases = (
            session.query(ModerationCase)
            .order_by(ModerationCase.created_at.desc())
            .limit(limit)
            .all()
        )
        return jsonify({"cases": [_serialize_case_summary(case) for case in cases]}), 200


def _serialize_case_summary(case: ModerationCase) -> dict[str, object]:
    return {
        "id": case.id,
        "content_reference": case.content_reference,
        "status": case.status,
        "assigned_reviewer": case.assigned_reviewer,
        "score": case.automated_score,
        "created_at": case.created_at.isoformat(),
    }


__all__ = ["admin_bp"]
