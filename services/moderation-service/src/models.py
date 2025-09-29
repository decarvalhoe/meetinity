"""SQLAlchemy models representing moderation workflows."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ModerationCase(TimestampMixin, Base):
    __tablename__ = "moderation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_id: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "escalated",
            "under_review",
            "action_taken",
            "dismissed",
            "appealed",
            name="moderation_status",
        ),
        nullable=False,
        default="pending",
    )
    severity: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON)
    automated_score: Mapped[float | None] = mapped_column(Float)
    automated_labels: Mapped[dict | None] = mapped_column(JSON)
    assigned_reviewer: Mapped[str | None] = mapped_column(String(120))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    actions: Mapped[list["ModerationAction"]] = relationship(
        "ModerationAction", back_populates="case", cascade="all, delete-orphan"
    )
    appeals: Mapped[list["ModerationAppeal"]] = relationship(
        "ModerationAppeal", back_populates="case", cascade="all, delete-orphan"
    )


class ModerationAction(TimestampMixin, Base):
    __tablename__ = "moderation_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON)

    case: Mapped[ModerationCase] = relationship("ModerationCase", back_populates="actions")


class ModerationAppeal(TimestampMixin, Base):
    __tablename__ = "moderation_appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "upheld", "overturned", name="appeal_status"), nullable=False, default="pending"
    )
    reviewer: Mapped[str | None] = mapped_column(String(120))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[ModerationCase] = relationship("ModerationCase", back_populates="appeals")


__all__ = ["ModerationCase", "ModerationAction", "ModerationAppeal"]
