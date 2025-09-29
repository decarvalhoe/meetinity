# Notification Service

The notification service coordinates multi-channel alerts (email, SMS, push, in-app) for Meetinity users. It exposes REST endpoints for scheduling notifications, managing user preferences, and tracking delivery outcomes. Persistence relies on PostgreSQL while Redis caches preference lookups. Outbound dispatch events are queued on Kafka (with an in-memory fallback for local tests).

## Features

- Schedule notifications across multiple channels with preference-aware filtering.
- Manage per-user channel preferences via REST endpoints.
- Track delivery attempts for each channel and update statuses.
- Publish queue messages per delivery (Kafka topic configurable via environment variables).

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string (falls back to SQLite when empty). | `""` |
| `REDIS_URL` | Redis connection URI used for caching preferences. | `redis://redis:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated Kafka bootstrap servers. | `""` (in-memory queue) |
| `KAFKA_NOTIFICATION_TOPIC` | Kafka topic for queued deliveries. | `notifications.dispatch` |

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
