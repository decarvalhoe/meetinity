"""Daily ingestion DAG that coordinates data movement into the object-store lake and warehouse."""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


def extract_partner_events(**context) -> str:
    """Placeholder extraction task that would normally land files in the raw S3 zone."""
    execution_ts = context["data_interval_start"].isoformat()
    print(f"Fetching incremental partner events for window starting at {execution_ts}")
    # Real implementation would land files into s3://<bucket>/raw/events/date=<ds>/
    return execution_ts


def compact_raw_files(**context) -> None:
    """Placeholder compaction that prepares data for Glue crawlers."""
    print("Optimising raw event files and ensuring partition manifests are available")


def notify_analytics(**context) -> None:
    """Send a notification that fresh data is ready for consumption."""
    print("Analytics stakeholders notified of fresh data availability")


def _default_schedule() -> str:
    return "0 1 * * *"


def _create_dag() -> DAG:
    dag = DAG(
        dag_id="meetinity_daily_ingestion",
        description="Coordinates daily ingestion from SaaS systems into the data lake and warehouse",
        start_date=datetime(2024, 1, 1),
        schedule=_default_schedule(),
        catchup=False,
        max_active_runs=1,
        default_args={
            "owner": "data-platform",
            "email_on_failure": True,
            "email": ["data-alerts@meetinity.io"],
            "retries": 1,
            "retry_delay": timedelta(minutes=10),
        },
        params={
            "dbt_target": Param("ci", type="string", description="dbt target to execute"),
        },
        tags=["meetinity", "data-platform"],
    )

    with dag:
        start = EmptyOperator(task_id="start")

        extract = PythonOperator(
            task_id="extract_partner_events",
            python_callable=extract_partner_events,
        )

        compact = PythonOperator(
            task_id="compact_raw_files",
            python_callable=compact_raw_files,
        )

        dbt_run = BashOperator(
            task_id="dbt_run",
            bash_command=(
                "cd /opt/airflow/dags/repo/infra/data/dbt && "
                "dbt build --target {{ params.dbt_target }}"
            ),
        )

        analytics_ready = PythonOperator(
            task_id="notify_analytics",
            python_callable=notify_analytics,
            trigger_rule="all_done",
        )

        finish = EmptyOperator(task_id="finish")

        start >> extract >> compact >> dbt_run >> analytics_ready >> finish

    return dag


globals()["meetinity_daily_ingestion"] = _create_dag()
