"""Prometheus metrics exported by the analytics service."""
from __future__ import annotations

from contextlib import contextmanager
from time import time
from typing import Iterator

from prometheus_client import Counter, Gauge, Histogram

EVENTS_INGESTED = Counter(
    "analytics_events_ingested_total",
    "Number of events accepted by the ingestion API",
    labelnames=("source", "event_type"),
)

EVENT_INGEST_LATENCY = Histogram(
    "analytics_event_ingest_latency_seconds",
    "Latency between event occurrence and ingestion",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)

WAREHOUSE_LOAD_DURATION = Histogram(
    "analytics_warehouse_load_duration_seconds",
    "Duration of warehouse rollup batches",
)

WAREHOUSE_ROWS = Counter(
    "analytics_warehouse_rows_total",
    "Rows materialised into the warehouse",
    labelnames=("table",),
)

WAREHOUSE_STATUS = Gauge(
    "analytics_warehouse_last_success_epoch",
    "Unix timestamp of the last successful warehouse rollup",
)


def observe_ingestion(event_type: str, source: str, latency_seconds: float) -> None:
    EVENTS_INGESTED.labels(source=source, event_type=event_type).inc()
    EVENT_INGEST_LATENCY.observe(latency_seconds)


@contextmanager
def record_warehouse_batch(table: str) -> Iterator[None]:
    start = time()
    try:
        yield
    finally:
        duration = max(time() - start, 0.0)
        WAREHOUSE_LOAD_DURATION.observe(duration)
        WAREHOUSE_STATUS.set(time())


def observe_rows_materialised(table: str, count: int) -> None:
    if count:
        WAREHOUSE_ROWS.labels(table=table).inc(count)
