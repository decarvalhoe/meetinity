"""Warehouse rollup logic for analytics KPIs."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..metrics import observe_rows_materialised, record_warehouse_batch
from ..models import AnalyticsEvent, KpiSnapshot, WarehouseLoad

DEFAULT_KPIS = ("events.total", "users.daily_active", "funnel.booking_conversion")


def _normalize_dates(start: datetime | date | None, end: datetime | date | None) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    start_date = (start.date() if isinstance(start, datetime) else start) or today
    end_date = (end.date() if isinstance(end, datetime) else end) or today
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def _coerce_date(value: object) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"Cannot interpret {value!r} as date")


class WarehouseLoader:
    """Materialise aggregates into the warehouse tables."""

    def __init__(self, session: Session):
        self._session = session

    def refresh(
        self,
        start: datetime | date | None = None,
        end: datetime | date | None = None,
        *,
        force: bool = False,
    ) -> List[KpiSnapshot]:
        start_date, end_date = _normalize_dates(start, end)
        lower = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        upper = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

        batch = WarehouseLoad(batch_id=str(uuid4()), status="running")
        self._session.add(batch)
        self._session.flush()

        if force:
            self._session.query(KpiSnapshot).filter(
                KpiSnapshot.window_start >= start_date,
                KpiSnapshot.window_end <= end_date,
            ).delete(synchronize_session=False)

        with record_warehouse_batch("analytics_kpi_snapshots"):
            counts_stmt = (
                select(
                    func.date(AnalyticsEvent.occurred_at).label("bucket"),
                    AnalyticsEvent.event_type,
                    func.count().label("event_count"),
                )
                .where(AnalyticsEvent.occurred_at >= lower, AnalyticsEvent.occurred_at < upper)
                .group_by("bucket", AnalyticsEvent.event_type)
            )
            counts_rows = self._session.execute(counts_stmt).all()

            unique_stmt = (
                select(
                    func.date(AnalyticsEvent.occurred_at).label("bucket"),
                    func.count(func.distinct(AnalyticsEvent.user_id)).label("unique_users"),
                )
                .where(AnalyticsEvent.occurred_at >= lower, AnalyticsEvent.occurred_at < upper)
                .group_by("bucket")
            )
            unique_rows = self._session.execute(unique_stmt).all()
            unique_lookup: Dict[date, int] = {
                _coerce_date(bucket): int(unique or 0) for bucket, unique in unique_rows
            }

            grouped: Dict[date, Dict[str, int]] = {}
            for bucket, event_type, count in counts_rows:
                bucket_date = _coerce_date(bucket)
                grouped.setdefault(bucket_date, {})[event_type] = int(count or 0)

            snapshots: List[KpiSnapshot] = []
            for window_start, events_by_type in grouped.items():
                window_end = window_start
                total_events = sum(events_by_type.values())
                unique_users = unique_lookup.get(window_start, 0)

                metadata = {
                    "events": events_by_type,
                    "unique_users": unique_users,
                }

                snapshots.append(
                    KpiSnapshot(
                        kpi_name="events.total",
                        window_start=window_start,
                        window_end=window_end,
                        value=float(total_events),
                        attributes=metadata,
                    )
                )
                snapshots.append(
                    KpiSnapshot(
                        kpi_name="users.daily_active",
                        window_start=window_start,
                        window_end=window_end,
                        value=float(unique_users),
                        attributes=metadata,
                    )
                )

                bookings_started = events_by_type.get("booking.started", 0)
                bookings_completed = events_by_type.get("booking.completed", 0)
                conversion = (bookings_completed / bookings_started) if bookings_started else 0.0
                snapshots.append(
                    KpiSnapshot(
                        kpi_name="funnel.booking_conversion",
                        window_start=window_start,
                        window_end=window_end,
                        value=float(round(conversion, 4)),
                        attributes={
                            "started": bookings_started,
                            "completed": bookings_completed,
                        },
                    )
                )

            for snapshot in snapshots:
                self._session.add(snapshot)
            batch.row_count = len(snapshots)
            observe_rows_materialised("analytics_kpi_snapshots", batch.row_count)

        batch.status = "succeeded"
        batch.completed_at = datetime.now(timezone.utc)
        self._session.flush()
        self._session.commit()
        return snapshots

    def list_kpis(
        self,
        names: Sequence[str] | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> List[KpiSnapshot]:
        start_date, end_date = _normalize_dates(start, end)
        query = self._session.query(KpiSnapshot).filter(
            KpiSnapshot.window_start >= start_date,
            KpiSnapshot.window_end <= end_date,
        )
        if names:
            query = query.filter(KpiSnapshot.kpi_name.in_(names))
        return list(query.order_by(KpiSnapshot.window_start.asc(), KpiSnapshot.kpi_name.asc()).all())


__all__ = ["WarehouseLoader", "DEFAULT_KPIS"]
