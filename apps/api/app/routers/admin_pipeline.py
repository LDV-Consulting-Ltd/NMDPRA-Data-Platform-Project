"""
Admin pipeline: trigger DAG and list runs via Airflow REST API.
Protected by ADMIN_RUN_TOKEN (Header: X-Admin-Token).
"""
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/admin", tags=["admin"])

AIRFLOW_BASE = os.getenv("AIRFLOW_API_BASE", "http://localhost:8080/api/v1")
AIRFLOW_USER = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASSWORD", "admin")
ADMIN_RUN_TOKEN = os.getenv("ADMIN_RUN_TOKEN", "")


def require_admin(x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token")):
    if not ADMIN_RUN_TOKEN:
        raise HTTPException(500, "ADMIN_RUN_TOKEN not set on server")
    if x_admin_token != ADMIN_RUN_TOKEN:
        raise HTTPException(401, "Unauthorized")


@router.post("/pipeline/run")
def run_pipeline(x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token")):
    """Trigger nmdpra_end_to_end_dag via Airflow REST API."""
    require_admin(x_admin_token)

    url = f"{AIRFLOW_BASE}/dags/nmdpra_end_to_end_dag/dagRuns"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            auth=(AIRFLOW_USER, AIRFLOW_PASS),
            json={"conf": {"triggered_by": "ui"}},
        )
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Airflow trigger failed: {r.text}")

    return {"ok": True, "dag_run": r.json()}


@router.get("/pipeline/runs")
def list_runs(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    limit: int = 10,
):
    """List recent DAG runs (for Pipeline Status card)."""
    require_admin(x_admin_token)

    url = f"{AIRFLOW_BASE}/dags/nmdpra_end_to_end_dag/dagRuns"
    params = {"limit": limit, "order_by": "-execution_date"}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, auth=(AIRFLOW_USER, AIRFLOW_PASS), params=params)
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Airflow list failed: {r.text}")

    return {"ok": True, "runs": r.json().get("dag_runs", r.json())}


@router.get("/pipeline/runs/{dag_run_id}")
def get_run(
    dag_run_id: str,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Get a single DAG run (for progress / current task)."""
    require_admin(x_admin_token)

    url = f"{AIRFLOW_BASE}/dags/nmdpra_end_to_end_dag/dagRuns/{dag_run_id}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, auth=(AIRFLOW_USER, AIRFLOW_PASS))
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Airflow get run failed: {r.text}")

    return {"ok": True, "dag_run": r.json()}
