# Synchronization & Downstream Integrations

## Kafka Topics

| Topic | Key | Value Schema | Purpose |
| --- | --- | --- | --- |
| `mds.canonical-users.v1` | `canonical_user_id` (UUID) | `CanonicalUserValue` Avro | Broadcast canonical user lifecycle changes. |
| `mds.canonical-profiles.v1` | `canonical_user_id` (UUID) | `CanonicalProfileValue` Avro | Publish attribute-level updates with lineage hashes. |
| `mds.merge-decisions.v1` | `canonical_user_id` (UUID) | `MergeDecisionValue` Avro | Moderation decisions feeding back into MDS. |

Schemas are maintained in the central schema registry (see `contracts/kafka/master-data-service`).

## CDC Streams

- Debezium PostgreSQL connector configured for `canonical_users` and `canonical_profiles` tables.
- CDC topics (`mds.canonical-users.cdc` and `mds.canonical-profiles.cdc`) capture row-level changes for analytical consumers.
- Downstream services can opt into CDC for full-fidelity replication or consume curated Kafka events for business-level triggers.

## Subscription Patterns

- **User Service** – Subscribes to `mds.canonical-users.v1` to update local caches and align user activation flows.
- **Search Service** – Consumes `mds.canonical-profiles.v1` to keep search indexes synchronized.
- **Analytics Service** – Reads CDC topics to populate the warehouse with lineage-rich records.
- **Notification Service** – Listens for profile changes impacting communication preferences.

## Replay & Recovery

- Kafka topics configured with 14-day retention and log compaction on canonical topics to keep latest state.
- Use schema registry compatibility mode `BACKWARD_TRANSITIVE` to safeguard consumer upgrades.
- Reprocessing supported via consumer groups resetting offsets or replaying CDC snapshots.

## Conflict Resolution Propagation

- When conflicts are resolved manually, the moderation tooling produces `MergeDecisionValue` events.
- MDS ingestion workers reconcile the decision, update canonical records, and emit refreshed canonical events + CDC changes.
- Downstream services treat `version` field increments as signals to refresh caches.
