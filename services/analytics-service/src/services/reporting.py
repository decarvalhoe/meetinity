"""Reporting service exposing aggregated KPIs."""
from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Sequence

from sqlalchemy.orm import Session

from ..models import KpiSnapshot
from ..services.warehouse import DEFAULT_KPIS, WarehouseLoader


def _normalize_window(start: date | datetime | None, end: date | datetime | None) -> tuple[date, date]:
    if isinstance(start, datetime):
        start_date = start.date()
    else:
        start_date = start or datetime.utcnow().date()
    if isinstance(end, datetime):
        end_date = end.date()
    else:
        end_date = end or datetime.utcnow().date()
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


class ReportingService:
    def __init__(self, session: Session):
        self._session = session
        self._warehouse = WarehouseLoader(session)

    @property
    def warehouse(self) -> WarehouseLoader:
        return self._warehouse

    def list_available_kpis(self) -> Sequence[str]:
        rows = self._session.query(KpiSnapshot.kpi_name).distinct().order_by(KpiSnapshot.kpi_name.asc()).all()
        discovered = [row[0] for row in rows]
        combined = list(dict.fromkeys([*DEFAULT_KPIS, *discovered]))
        return combined

    def fetch_snapshots(
        self,
        names: Sequence[str] | None = None,
        *,
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> List[dict[str, object]]:
        start_date, end_date = _normalize_window(start, end)
        snapshots = self._warehouse.list_kpis(names, start=start_date, end=end_date)
        return [snapshot.as_dict() for snapshot in snapshots]

    def refresh(self, *, start: date | datetime | None = None, end: date | datetime | None = None, force: bool = False) -> Dict[str, int]:
        snapshots = self._warehouse.refresh(start=start, end=end, force=force)
        return {"rows_materialised": len(snapshots)}


__all__ = ["ReportingService"]
