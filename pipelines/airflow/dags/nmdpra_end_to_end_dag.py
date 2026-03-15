"""
NMDPRA End-to-End DAG: discover -> download -> parse -> DQ -> silver -> gold -> publish -> finalize.
Runs ONCE per trigger; idempotent (content_hash skip). Supports schedule and manual trigger.
"""
import os
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
    run_id = context.get("dag_run").run_id or "manual"
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
    from core.run_pipeline import get_engine
    import uuid
    from sqlalchemy import text
    from datetime import datetime
    engine = get_engine()
    conn = engine.connect()
    try:
        run_id = str(uuid.uuid4())
        conn.execute(text("""
            INSERT INTO bronze.ingest_run (run_id, dag_id, triggered_by, started_at, finished_at, status, notes)
            VALUES (:run_id, 'nmdpra_end_to_end_dag', 'schedule', :started, :finished, 'success', 'Pipeline completed')
        """), {"run_id": run_id, "started": datetime.utcnow(), "finished": datetime.utcnow()})
        conn.commit()
        return {"run_id": run_id}
    finally:
        conn.close()


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
    description="NMDPRA data product: discover, download, parse, DQ, silver, gold, publish",
    schedule_interval=None,  # No fixed schedule; only trigger via API (startup bootstrap or Run button)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["nmdpra", "data-product"],
)

t_discover = PythonOperator(task_id="discover", python_callable=run_discover, dag=dag)
t_download = PythonOperator(task_id="download", python_callable=run_download, dag=dag)
t_parse = PythonOperator(task_id="parse", python_callable=run_parse, dag=dag)
t_dq = PythonOperator(task_id="dq_bronze", python_callable=run_dq, dag=dag)
t_silver_gold = PythonOperator(task_id="silver_gold", python_callable=run_silver_gold, dag=dag)
t_publish = PythonOperator(task_id="publish_metadata_lineage", python_callable=run_publish, dag=dag)
t_diagrams = PythonOperator(task_id="generate_diagrams", python_callable=run_diagrams, dag=dag)
t_finalize = PythonOperator(task_id="finalize", python_callable=run_finalize, dag=dag)

t_discover >> t_download >> t_parse >> t_dq >> t_silver_gold >> t_publish >> t_diagrams >> t_finalize
