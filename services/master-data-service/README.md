# Master Data Service

The Master Data Service (MDS) maintains canonical user and profile records for Meetinity. It provides deduplication, lineage tracking, and an authoritative data store that downstream services can safely consume.

## Responsibilities

- Persist canonical representations of users and profiles in PostgreSQL.
- Ingest user signals from upstream systems (sign-up events, CRM imports, support updates) and resolve them to existing canonical records.
- Capture provenance and lineage for each data attribute to support audit, regulatory compliance, and troubleshooting.
- Propagate normalized user/profile changes via Kafka topics and change data capture (CDC) streams.
- Offer query APIs for internal services that require authoritative user information.

## Architecture Overview

| Component | Description |
| --- | --- |
| **PostgreSQL** | Primary data store that houses canonical user and profile entities, deduplication artifacts, and lineage metadata. |
| **Ingestion Workers** | Consume upstream queues/streams and orchestrate matching, merging, and persistence workflows. |
| **Deduplication Engine** | Applies deterministic and probabilistic matching rules, tracks potential duplicates, and manages merge decisions. |
| **API Layer** | Exposes REST endpoints for internal services to query canonical user information and metadata. |
| **Streaming Connectors** | Publish outbound events (Kafka) and CDC streams (Debezium) for downstream synchronization. |

## Data Model Highlights

- `canonical_users`: core entity storing immutable identifiers and lifecycle statuses.
- `canonical_profiles`: normalized profile attributes (name, contact info, preferences) with attribute-level lineage references.
- `source_identities`: raw identities received from upstream systems to support matching.
- `attribute_lineage`: attribute-level provenance that links canonical fields back to contributing sources and timestamps.
- `potential_duplicates`: queue of records flagged for manual review or automated resolution.

See [`docs/data-model.md`](docs/data-model.md) for detailed schemas and migration notes.

## Operational Considerations

- Database migrations managed with Alembic; schema drift is tracked via automated CI checks.
- Background jobs recompute similarity scores and merge candidates nightly.
- CDC is powered by Debezium connectors managed through the platform's Kafka Connect cluster.
- High-risk merges (e.g., conflicting government ID values) require human approval logged via the moderation tooling.

## Local Development

1. Start dependencies: `docker compose up postgres kafka schema-registry` (see repo-level compose file).
2. Apply migrations: `alembic upgrade head`.
3. Run the service: `uvicorn mds.main:app --reload`.
4. Execute the test suite: `pytest`.

Environment variables:

- `DATABASE_URL` — PostgreSQL connection string.
- `KAFKA_BROKERS` — comma-separated broker list for publishing events.
- `SCHEMA_REGISTRY_URL` — Confluent-compatible registry URL for Avro schemas.
- `DEBEZIUM_CONNECT_URL` — Kafka Connect REST endpoint for managing CDC connectors.

## Security and Compliance

- PII is encrypted at rest via PostgreSQL column-level encryption and managed keys.
- Access to the service requires mTLS between services and OAuth2 service tokens.
- Audit trails persist lineage changes and manual merge decisions for 7 years.

## Related Documentation

- [`docs/deduplication-workflows.md`](docs/deduplication-workflows.md)
- [`docs/synchronization.md`](docs/synchronization.md)
- [`../../docs/data-architecture.md`](../../docs/data-architecture.md)
- [`../../docs/service-inventory.md`](../../docs/service-inventory.md)
