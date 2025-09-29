# Meetinity Data Architecture

## Overview
The Meetinity data platform is composed of three tightly-integrated layers:

1. **Landing & storage** in an encrypted Amazon S3 data lake that is automatically catalogued by AWS Glue and queryable via Athena workgroups.
2. **Warehousing & serving** in Amazon Redshift, which provides governed access to curated marts and supports BI workloads.
3. **Transformation & orchestration** using Apache Airflow for ingestion scheduling and dbt for ELT modelling, all validated automatically in CI and monitored through Prometheus.

The infrastructure is codified in Terraform (`infra/terraform`) and data workflows live under `infra/data`.

## Object-store data lake
* `modules/data_lake` provisions an S3 bucket with versioning, strict TLS-only policies, and optional customer-managed KMS encryption.
* Glue catalogues (`aws_glue_catalog_database`) and crawlers maintain schema metadata for raw zones, while IAM roles restrict Glue and Athena to the bucket.
* An Athena workgroup publishes CloudWatch metrics, enforces encryption for query results, and uses a dedicated query-results prefix.
* The Glue crawler target defaults to the bucket's `/raw/` prefix, ensuring any new landing folders are automatically catalogued.

## Warehousing layer
* `modules/redshift` now attaches a managed IAM role that grants the cluster scoped access to data lake buckets and Glue catalog metadata.
* Encryption at rest is enforced via Redshift's `encrypted` flag and an optional KMS key can be supplied to both the cluster and IAM policies.
* Outputs expose the warehouse connection details and the IAM role ARN used for cross-service access, simplifying integration with orchestration tools.

## Transformation workflows
* Airflow orchestrates the daily ingestion DAG (`infra/data/airflow/dags/meetinity_daily_ingestion.py`) which sequences extraction, S3 compaction, dbt runs, and notifications.
* dbt models live under `infra/data/dbt`, using DuckDB in CI to compile and test transformations against representative seed data.
  * `staging` models clean seed inputs and enforce data quality tests.
  * `marts/fct_user_engagement.sql` aggregates events into a consumption-ready fact table that powers downstream dashboards.
* The `infra/data/Makefile` encapsulates workflow validation (Python compile, `dbt deps/seed/build`) making it easy to run locally or in automation.

## CI automation
A new `data-pipelines` job in `.github/workflows/ci.yml` installs dbt/duckdb tooling and executes `make ci`. This guarantees Airflow DAGs remain syntactically valid and dbt models/test suites continue to compile before merges.

## Monitoring & alerting
Prometheus now ships dedicated rules in `infra/monitoring/prometheus/values.yaml`:

* `AirflowDAGFailures` alerts on any failed Meetinity-prefixed DAG runs.
* `DataPipelineFreshnessSLO` fires if the daily ingestion DAG has no successful executions within a two-hour SLO window.
* `DbtBuildFailures` captures dbt build errors surfaced via exporter metrics.

These alerts inherit existing routing through Alertmanager and surface issues in the shared observability stack.

## Governance, catalog & access control
* All lake and warehouse resources share `meetinity` project tags, easing inventory and cost attribution.
* Glue catalog metadata under `data_lake_glue_database` provides a single source of truth for schema definitions and is referenced by both Athena and Redshift spectrum.
* IAM roles (`glue_role_arn`, `athena_role_arn`, and `analytics_warehouse_data_access_role_arn`) are exposed as Terraform outputs for downstream services to assume with least privilege.
* Encryption defaults are enabled everywhere (S3, Athena outputs, Redshift), ensuring regulatory compliance without additional configuration.
* Seeded dbt exposures document the downstream dashboard dependencies, forming the basis of a lightweight data catalog.

## Operational playbook
1. **Add new sources** by dropping landed files into the S3 raw prefix; the Glue crawler will detect partitions automatically.
2. **Model data** by adding dbt seeds/models/tests and running `make ci` locally before pushing.
3. **Deploy orchestration** by updating Airflow DAGs and validating via the CI pipeline.
4. **Monitor health** in Grafana/Alertmanager via the new Prometheus alerts.
5. **Audit & governance** leveraging Glue catalog, IAM outputs, and Terraform state for traceability.
