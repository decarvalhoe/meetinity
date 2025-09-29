"""SQLAlchemy models for analytics data."""
from __future__ import annotations

from datetime import datetime, date
from typing import Any

from sqlalchemy import Column, Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("ix_analytics_events_type_time", "event_type", "occurred_at"),
        Index("ix_analytics_events_user_time", "user_id", "occurred_at"),
    )

    id = Column(Integer, primary_key=True)
    event_type = Column(String(120), nullable=False)
    user_id = Column(String(64), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ingestion_id = Column(String(64), nullable=True)
    source = Column(String(64), nullable=False, default="http")
    payload = Column(JSON, nullable=False, default=dict)
    context = Column(JSON, nullable=True)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "occurred_at": self.occurred_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "ingestion_id": self.ingestion_id,
            "source": self.source,
            "payload": self.payload,
            "context": self.context,
        }


class WarehouseLoad(Base):
    __tablename__ = "analytics_warehouse_loads"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(64), unique=True, nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default="running")
    row_count = Column(Integer, nullable=False, default=0)
    destination_table = Column(String(120), nullable=False, default="kpi_snapshots")
    error_message = Column(Text, nullable=True)


class KpiSnapshot(Base):
    __tablename__ = "analytics_kpi_snapshots"
    __table_args__ = (
        UniqueConstraint("kpi_name", "window_start", name="ux_kpi_window"),
        Index("ix_kpi_window", "window_start"),
    )

    id = Column(Integer, primary_key=True)
    kpi_name = Column(String(120), nullable=False)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    value = Column(Float, nullable=False)
    attributes = Column("metadata", JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kpi_name": self.kpi_name,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "value": self.value,
            "metadata": self.attributes,
            "computed_at": self.computed_at.isoformat(),
        }
