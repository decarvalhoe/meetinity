# Moderation Service

The moderation service centralises automated filters, case management, reviewer workflows and appeals.

## Features

- **Automated filters** combining heuristics, Redis-backed rate limits and optional ML classifier scoring.
- **User reports** API to open moderation cases from messaging or events.
- **Reviewer tooling** for assignments, resolutions, escalations and audit trails.
- **Appeals** workflow so impacted users can request a second look.
- **Kafka events** emitted for downstream analytics or notifications with dead-letter protection.

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL DSN used for persistence. | `sqlite:///:memory:` (tests only) |
| `REDIS_URL` | Redis connection string or `fakeredis://` for testing. | `fakeredis://` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers to publish lifecycle events. | _empty_ |
| `KAFKA_MODERATION_TOPIC` | Topic carrying moderation case lifecycle events. | `moderation.events` |
| `KAFKA_SCHEMA_REGISTRY_URL` | Schema registry endpoint for event contracts. | _empty_ |
| `KAFKA_SECURITY_PROTOCOL` | Kafka security protocol (e.g. `SASL_SSL`). | _empty_ |
| `KAFKA_SASL_MECHANISM` | SASL mechanism (e.g. `SCRAM-SHA-512`). | _empty_ |
| `KAFKA_SASL_USERNAME` | Username for SASL authentication. | _empty_ |
| `KAFKA_SASL_PASSWORD` | Password for SASL authentication. | _empty_ |
| `KAFKA_DLQ_TOPIC` | Dead-letter topic for failed moderation events. | `moderation.events.dlq` |
| `ML_CLASSIFIER_URL` | Optional external classifier endpoint. | _empty_ |
| `AUTO_APPROVE_THRESHOLD` | Score threshold to request manual review. | `0.55` |
| `AUTO_BLOCK_THRESHOLD` | Score threshold to block content. | `0.9` |

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
FLASK_APP=src.main:app flask run --host=0.0.0.0 --port=8080
```

Run tests:

```bash
pytest
```
