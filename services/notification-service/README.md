# Notification Service

The notification service coordinates multi-channel alerts (email, SMS, push, in-app) for Meetinity users. It exposes REST endpoints for scheduling notifications, managing user preferences, and tracking delivery outcomes. Persistence relies on PostgreSQL while Redis caches preference lookups. Outbound dispatch events are queued on Kafka (with an in-memory fallback for local tests).

## Features

- Schedule notifications across multiple channels with preference-aware filtering.
- Manage per-user channel preferences via REST endpoints.
- Track delivery attempts for each channel and update statuses.
- Publish queue messages per delivery (Kafka topic configurable via environment variables).
- Expose Prometheus metrics for queue health (publish counts, lag) and persist failures into a dead-letter queue.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string (falls back to SQLite when empty). | `""` |
| `REDIS_URL` | Redis connection URI used for caching preferences. | `redis://redis:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated Kafka bootstrap servers. | `""` (in-memory queue) |
| `KAFKA_NOTIFICATION_TOPIC` | Kafka topic for queued deliveries. | `notifications.dispatch` |
| `KAFKA_SCHEMA_REGISTRY_URL` | Schema registry endpoint used by producers. | `""` |
| `KAFKA_SECURITY_PROTOCOL` | Kafka security protocol (e.g. `SASL_SSL`). | `""` |
| `KAFKA_SASL_MECHANISM` | SASL mechanism (e.g. `SCRAM-SHA-512`). | `""` |
| `KAFKA_SASL_USERNAME` | Username for SASL authentication. | `""` |
| `KAFKA_SASL_PASSWORD` | Password for SASL authentication. | `""` |
| `KAFKA_DLQ_TOPIC` | Dead-letter topic used when publishing fails. | `notifications.dispatch.dlq` |

All settings can also be provided via individual `DB_*` / `REDIS_*` environment variables as supported by the helper modules.

## Local development

Install dependencies and run the Flask development server:

```bash
pip install -r requirements.txt
export FLASK_APP=src.main:create_app
flask --app src.main:create_app run --debug
```

Integration with the monorepo `docker-compose.dev.yml` automatically sets the correct environment variables and mounts the source tree for hot reload.

## Testing

The `tests/` directory contains pytest suites that exercise the HTTP API and business logic using SQLite and an in-memory queue. Run them with:

```bash
pip install -r requirements.txt
pip install pytest
pytest tests -vv
```
