# Meetinity Search Service

The Search Service exposes REST and GraphQL APIs backed by Elasticsearch/OpenSearch.
It is responsible for ingestion pipelines, unified search, and search relevance tuning
across Meetinity domains (events, users, conversations, etc.).

## Features

- Modular ingestion pipelines with schema validation per domain.
- REST endpoints for ingesting documents and executing typed search queries.
- GraphQL endpoint (`/graphql`) returning consolidated results.
- Index lifecycle helpers and snapshot-friendly mappings.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:create_app --reload --port 8080
```

When running locally without an Elasticsearch cluster you can export
`SEARCH_USE_IN_MEMORY=1` to enable the lightweight in-memory search backend that powers
the automated tests.

## Configuration

Configuration is handled through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_NODES` | Comma-separated list of Elasticsearch hosts | `http://localhost:9200` |
| `SEARCH_USERNAME` | Optional basic auth username | *empty* |
| `SEARCH_PASSWORD` | Optional basic auth password | *empty* |
| `SEARCH_VERIFY_CERTS` | Set to `0` to disable TLS verification | `1` |
| `SEARCH_TIMEOUT` | Request timeout (seconds) | `10` |
| `SEARCH_USE_IN_MEMORY` | Use in-memory backend when set to `1` | `0` |

## Testing

```bash
pytest -vv
```

## Health Checks

- `GET /health` returns service health and backend availability.

