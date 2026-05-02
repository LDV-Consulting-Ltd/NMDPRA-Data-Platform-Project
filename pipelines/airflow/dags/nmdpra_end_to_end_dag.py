"""
NMDPRA End-to-End DAG: init -> discover -> download -> parse -> DQ -> silver -> gold -> publish -> finalize.
Runs ONCE per trigger; idempotent (content_hash skip). Supports schedule and manual trigger.
"""
import os
import uuid
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Ensure project root and core/parsers are on path when running in Airflow
AIRFLOW_DAGS = os.path.dirname(os.path.abspath(__file__))
for _ in ["", "/opt/airflow", os.path.dirname(os.path.dirname(os.path.dirname(AIRFLOW_DAGS)))]:
    root = _ or os.path.dirname(os.path.dirname(AIRFLOW_DAGS))
    if root and root not in os.sys.path:
        os.sys.path.insert(0, root)

# Set DB URL for pipeline (Airflow passes this via env in docker-compose)
NMDPRA_DB_URL = os.getenv("NMDPRA_DB_URL", "postgresql+psycopg2://nmdpra:nmdpra_secret@postgres:5432/nmdpra_data")
os.environ["NMDPRA_DB_URL"] = NMDPRA_DB_URL
os.environ.setdefault("NMDPRA_DATA_DIR", "/opt/airflow/data")


def run_init(**context):
    """Create a pipeline run_id (UUID), insert into bronze.ingest_run, push to XCom for downstream tasks."""
    from core.run_pipeline import get_engine
    from sqlalchemy import text
    run_id = str(uuid.uuid4())
    dag_run = context.get("dag_run")
    conf = {}
    if dag_run is not None:
        c = getattr(dag_run, "conf", None) or {}
        if isinstance(c, dict):
            conf = c
    triggered_by = conf.get("triggered_by") if isinstance(conf.get("triggered_by"), str) else None
    if not triggered_by:
        rid = (getattr(dag_run, "run_id", None) or "") if dag_run else ""
        triggered_by = "manual" if "manual" in rid else "schedule"
    with get_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO bronze.ingest_run (run_id, dag_id, triggered_by, started_at, status)
            VALUES (:run_id, 'nmdpra_end_to_end_dag', :triggered_by, :started_at, 'partial')
        """), {"run_id": run_id, "triggered_by": triggered_by, "started_at": datetime.utcnow()})
    return {"run_id": run_id}


def run_discover(**context):
    from core.run_pipeline import get_engine, run_discover
    n = run_discover(get_engine())
    return {"discovered": n}


def run_download(**context):
    from core.run_pipeline import get_engine, run_download
    n = run_download(get_engine())
    return {"downloaded": n}


def run_parse(**context):
    from core.run_pipeline import get_engine, run_parse
    counts = run_parse(get_engine())
    return {"row_counts": counts}


def run_dq(**context):
    from core.run_pipeline import get_engine, run_dq
    # Pipeline run_id (UUID) from init task; required for bronze.dq_result.run_id (UUID FK)
    xcom = (context.get("ti").xcom_pull(task_ids="init") or {}) if context.get("ti") else {}
    run_id = xcom.get("run_id") or (context.get("dag_run").run_id if context.get("dag_run") else None) or "manual"
    run_dq(get_engine(), run_id)
    return {"dq": "ok"}


def run_silver_gold(**context):
    from core.run_pipeline import get_engine, run_silver_gold
    run_silver_gold(get_engine())
    return {"silver_gold": "ok"}


def run_publish(**context):
    from core.run_pipeline import get_engine, run_publish_metadata_lineage
    run_publish_metadata_lineage(get_engine())
    return {"publish": "ok"}


def run_diagrams(**context):
    import subprocess
    script = "/opt/airflow/scripts/generate_diagrams.py"
    if os.path.isfile(script):
        subprocess.run(["/usr/local/bin/python", script], cwd=os.path.dirname(script), check=False)
    return {"diagrams": "ok"}


def run_finalize(**context):
    """Update bronze.ingest_run for this pipeline run (run_id from init task)."""
    from core.run_pipeline import get_engine
    from sqlalchemy import text
    xcom = (context.get("ti").xcom_pull(task_ids="init") or {}) if context.get("ti") else {}
    run_id = xcom.get("run_id")
    if not run_id:
        return {"run_id": None, "status": "skipped"}
    with get_engine().begin() as conn:
        conn.execute(text("""
            UPDATE bronze.ingest_run SET finished_at = :finished, status = 'success', notes = 'Pipeline completed'
            WHERE run_id = :run_id
        """), {"finished": datetime.utcnow(), "run_id": run_id})
    return {"run_id": run_id}


default_args = {
    "owner": "nmdpra",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    "nmdpra_end_to_end_dag",
    default_args=default_args,
    description="NMDPRA downstream regulatory intelligence: discover, download, parse, DQ, silver, gold, publish",
    schedule_interval=None,  # No fixed schedule; startup bootstrap or authorized run only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nmdpra", "data-product"],
)

t_init = PythonOperator(task_id="init", python_callable=run_init, dag=dag)
t_discover = PythonOperator(task_id="discover", python_callable=run_discover, dag=dag)
t_download = PythonOperator(task_id="download", python_callable=run_download, dag=dag)
t_parse = PythonOperator(task_id="parse", python_callable=run_parse, dag=dag)
t_dq = PythonOperator(task_id="dq_bronze", python_callable=run_dq, dag=dag)
t_silver_gold = PythonOperator(task_id="silver_gold", python_callable=run_silver_gold, dag=dag)
t_publish = PythonOperator(task_id="publish_metadata_lineage", python_callable=run_publish, dag=dag)
t_diagrams = PythonOperator(task_id="generate_diagrams", python_callable=run_diagrams, dag=dag)
t_finalize = PythonOperator(task_id="finalize", python_callable=run_finalize, dag=dag)

t_init >> t_discover >> t_download >> t_parse >> t_dq >> t_silver_gold >> t_publish >> t_diagrams >> t_finalize
