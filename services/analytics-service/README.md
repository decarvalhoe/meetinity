# Meetinity Analytics Service

The analytics service centralises user and product telemetry, persists canonical
analytics events, and materialises business KPIs for downstream reporting. It
provides synchronous ingestion endpoints, asynchronous consumers, and REST
reporting APIs that expose the warehouse views consumed by dashboards.

## Features

- **Ingestion endpoints** – `/ingest/events` and `/ingest/batch` accept
  canonical events, enforce schema validation, and record Prometheus metrics.
- **Message consumers** – `AnalyticsEventConsumer` parses Kafka-style payloads
  to reuse the same ingestion pipeline for streaming sources.
- **Warehouse rollups** – the `WarehouseLoader` computes daily aggregates and
  stores KPI snapshots in the warehouse tables.
- **Reporting APIs** – `/reports/kpis` and `/reports/refresh` expose KPI
  snapshots and manual backfill triggers for operators.
- **Metadata catalog** – `/metadata/schemas` and `/metadata/kpis` document the
  available event schemas and KPI definitions for producers and analysts.

## Local development

```bash
pip install -r requirements.txt
FLASK_APP=src.main:create_app flask run --reload
```

Refer to [`docs/SCHEMAS.md`](docs/SCHEMAS.md) for the canonical event schema and
[`docs/KPIS.md`](docs/KPIS.md) for KPI definitions and SLIs.
