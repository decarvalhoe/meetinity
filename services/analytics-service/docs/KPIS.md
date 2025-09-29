# KPI Catalogue

| KPI | Description | Calculation |
| --- | ----------- | ----------- |
| `events.total` | Total number of analytics events per day. | Count of `analytics_events` grouped by day. |
| `users.daily_active` | Distinct users generating at least one event in the day. | Count of distinct `user_id` across all event types. |
| `funnel.booking_conversion` | Booking funnel conversion rate. | `booking.completed` / `booking.started` for the day. |

## Data Retention

Raw events are retained for 90 days in the operational store before archival.
Warehouse snapshots are kept indefinitely to support long term reporting.

## SLOs and SLIs

- **Ingestion latency** – 95% of events are available in the warehouse within 5
  minutes of occurrence (`analytics_event_ingest_latency_seconds`).
- **Warehouse freshness** – The last successful rollup timestamp
  (`analytics_warehouse_last_success_epoch`) must be less than 30 minutes old
  during business hours.
