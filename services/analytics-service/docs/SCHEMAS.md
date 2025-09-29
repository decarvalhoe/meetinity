# Analytics Event Schemas

## Canonical Event Envelope

| Field        | Type    | Description |
| ------------ | ------- | ----------- |
| `event_type` | string  | Canonical name of the event (e.g. `booking.started`). |
| `user_id`    | string? | Optional user identifier for authenticated events. |
| `occurred_at`| string  | ISO-8601 timestamp when the action happened. |
| `ingestion_id` | string? | Optional idempotency key supplied by producers to deduplicate events. |
| `source`     | string  | Origin transport (`http`, `kafka`, `webhook`). |
| `payload`    | object  | Free-form JSON payload describing the event. |
| `context`    | object  | Optional metadata such as device, locale, experiment IDs. |

### Common Event Types

- `booking.started` – triggered when a user initiates a meeting booking workflow.
- `booking.completed` – emitted once the booking is confirmed.
- `session.active` – emitted every five minutes while the user remains active.

All event producers must publish envelopes that comply with the schema above to
ensure consistent ingestion and downstream warehousing.
