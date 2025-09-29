"""Business logic for moderation case lifecycle."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from ..config import ModerationConfig
from ..models import ModerationAction, ModerationAppeal, ModerationCase
from ..services.filters import FilterResult
from ..kafka import publish_event


class ModerationCaseService:
    """Create and manage moderation cases, reviewer flows, and appeals."""

    def __init__(self, session: Session, config: ModerationConfig) -> None:
        self.session = session
        self.config = config

    def create_report(
        self,
        *,
        content_type: str,
        content_reference: str,
        reporter_id: int | None,
        source: str | None,
        summary: str | None,
        context: Mapping[str, Any] | None,
        filter_result: FilterResult | None = None,
    ) -> ModerationCase:
        case = ModerationCase(
            content_type=content_type,
            content_reference=content_reference,
            reporter_id=reporter_id,
            source=source,
            summary=summary,
            context=dict(context or {}),
        )
        if filter_result is not None:
            case.automated_score = filter_result.score
            case.automated_labels = filter_result.labels
            if filter_result.status == "blocked":
                case.status = "escalated"
            elif filter_result.status == "needs_review":
                case.status = "under_review"
        self.session.add(case)
        self.session.flush()

        publish_event(
            config=self.config,
            key=str(case.id),
            payload={
                "type": "case.created",
                "case_id": case.id,
                "content_reference": case.content_reference,
                "status": case.status,
                "score": case.automated_score,
            },
        )
        return case

    def assign_case(self, case: ModerationCase, reviewer: str, actor: str) -> ModerationCase:
        case.assigned_reviewer = reviewer
        case.status = "under_review"
        self.session.add(
            ModerationAction(
                case_id=case.id,
                actor=actor,
                action_type="assign",
                details={"reviewer": reviewer},
            )
        )
        publish_event(
            config=self.config,
            key=str(case.id),
            payload={
                "type": "case.assigned",
                "case_id": case.id,
                "reviewer": reviewer,
            },
        )
        return case

    def resolve_case(
        self,
        case: ModerationCase,
        *,
        status: str,
        actor: str,
        notes: str | None = None,
    ) -> ModerationCase:
        if status not in {"action_taken", "dismissed", "escalated"}:
            raise ValueError("Statut de résolution invalide.")
        case.status = status
        case.resolution_notes = notes
        case.resolved_at = datetime.now(timezone.utc)
        self.session.add(
            ModerationAction(
                case_id=case.id,
                actor=actor,
                action_type="resolve",
                details={"status": status, "notes": notes},
            )
        )
        publish_event(
            config=self.config,
            key=str(case.id),
            payload={
                "type": "case.resolved",
                "case_id": case.id,
                "status": status,
            },
        )
        return case

    def escalate_case(self, case: ModerationCase, *, actor: str, reason: str) -> ModerationCase:
        case.status = "escalated"
        self.session.add(
            ModerationAction(
                case_id=case.id,
                actor=actor,
                action_type="escalate",
                details={"reason": reason},
            )
        )
        publish_event(
            config=self.config,
            key=str(case.id),
            payload={
                "type": "case.escalated",
                "case_id": case.id,
                "reason": reason,
            },
        )
        return case

    def create_appeal(
        self,
        case: ModerationCase,
        *,
        submitted_by: str,
        reason: str,
    ) -> ModerationAppeal:
        appeal = ModerationAppeal(case_id=case.id, submitted_by=submitted_by, reason=reason)
        case.status = "appealed"
        self.session.add(appeal)
        publish_event(
            config=self.config,
            key=str(case.id),
            payload={
                "type": "appeal.created",
                "case_id": case.id,
                "appeal_id": appeal.id,
            },
        )
        return appeal

    def resolve_appeal(
        self,
        appeal: ModerationAppeal,
        *,
        decision: str,
        reviewer: str,
        notes: str | None = None,
    ) -> ModerationAppeal:
        if decision not in {"upheld", "overturned"}:
            raise ValueError("Décision d'appel invalide.")
        appeal.status = decision
        appeal.reviewer = reviewer
        appeal.resolution_notes = notes
        appeal.resolved_at = datetime.now(timezone.utc)
        self.session.add(
            ModerationAction(
                case_id=appeal.case_id,
                actor=reviewer,
                action_type="appeal_" + decision,
                details={"notes": notes},
            )
        )
        publish_event(
            config=self.config,
            key=str(appeal.case_id),
            payload={
                "type": "appeal.resolved",
                "case_id": appeal.case_id,
                "appeal_id": appeal.id,
                "decision": decision,
            },
        )
        return appeal


def get_case(session: Session, case_id: int) -> ModerationCase:
    case = session.get(ModerationCase, case_id)
    if case is None:
        raise LookupError("Dossier de modération introuvable.")
    return case


def get_appeal(session: Session, appeal_id: int) -> ModerationAppeal:
    appeal = session.get(ModerationAppeal, appeal_id)
    if appeal is None:
        raise LookupError("Appel introuvable.")
    return appeal


__all__ = [
    "ModerationCaseService",
    "get_case",
    "get_appeal",
]
