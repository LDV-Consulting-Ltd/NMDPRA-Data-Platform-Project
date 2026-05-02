"""
Admin pipeline: trigger ingestion, inspect orchestration health (admin-only).
Protected by ADMIN_RUN_TOKEN (Header: X-Admin-Token).
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/admin")

AIRFLOW_BASE = os.getenv("AIRFLOW_API_BASE", "http://localhost:8080/api/v1").rstrip("/")
AIRFLOW_USER = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASSWORD", "admin")
ADMIN_RUN_TOKEN = os.getenv("ADMIN_RUN_TOKEN", "")
DAG_ID = "nmdpra_end_to_end_dag"


def require_admin(x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token")):
    if not ADMIN_RUN_TOKEN:
        raise HTTPException(500, "ADMIN_RUN_TOKEN not set on server")
    if x_admin_token != ADMIN_RUN_TOKEN:
        raise HTTPException(401, "Unauthorized")


def _airflow_ready() -> bool:
    try:
        root = AIRFLOW_BASE.replace("/api/v1", "")
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{root}/health")
            return r.status_code < 300
    except Exception:
        return False


def _scheduler_detect_ready() -> bool:
    """Best-effort: scheduler healthy if recent DAG runs can transition from queued."""
    try:
        url = f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns"
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url, auth=(AIRFLOW_USER, AIRFLOW_PASS), params={"limit": 1})
            return r.status_code < 300
    except Exception:
        return False


@router.post("/pipeline/run", response_model=dict)
def run_pipeline(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Trigger end-to-end ingestion via orchestrator REST API."""
    require_admin(x_admin_token)

    if not _airflow_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Orchestration service is not ready yet. Wait a minute after startup and try again.",
                "orchestration_ready": False,
            },
        )

    url = f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns"
    body = {"conf": {"triggered_by": "admin_ui", "reason": "manual_run"}}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, auth=(AIRFLOW_USER, AIRFLOW_PASS), json=body)

    if r.status_code >= 300:
        raise HTTPException(r.status_code, {"detail": r.text, "message": "Orchestration trigger failed"})

    data = r.json()
    dr = data.get("dag_run") or data
    dag_run_id = dr.get("dag_run_id") if isinstance(dr, dict) else None

    return {
        "dag_run_id": dag_run_id,
        "status": "queued",
        "triggered_by": "admin_ui",
        "detail": dr if isinstance(dr, dict) else data,
    }


@router.get("/pipeline/status")
def admin_pipeline_status(
    db=Depends(get_db),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Latest pipeline state including orchestration run id when available."""
    require_admin(x_admin_token)

    row = db.execute(text("""
        SELECT run_id, status, triggered_by, started_at, finished_at, notes
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()

    ingested = db.execute(text(
        "SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL"
    )).scalar() or 0
    has_success = bool(db.execute(text(
        "SELECT EXISTS (SELECT 1 FROM bronze.ingest_run WHERE status = 'success' LIMIT 1)"
    )).scalar())

    ui_status = "unknown"
    latest_run_id = None
    triggered_by = None
    started_at = finished_at = None
    notes = None
    if row and row[0]:
        latest_run_id = str(row[0])
        db_status = row[1]
        triggered_by = str(row[2]) if row[2] is not None else None
        started_at = row[3].isoformat() if row[3] else None
        finished_at = row[4].isoformat() if row[4] else None
        notes = str(row[5]) if row[5] is not None else None
        if db_status == "partial":
            ui_status = "running"
        elif db_status == "success":
            ui_status = "success"
        elif db_status == "fail":
            ui_status = "failed"
        else:
            ui_status = "unknown"

    current_task = None
    if _airflow_ready() and ui_status == "running":
        try:
            url = f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns"
            with httpx.Client(timeout=15.0) as client:
                r = client.get(
                    url,
                    auth=(AIRFLOW_USER, AIRFLOW_PASS),
                    params={"limit": 1, "order_by": "-start_date"},
                )
            if r.status_code < 300:
                dag_runs = r.json().get("dag_runs") or []
                if dag_runs:
                    drid = dag_runs[0].get("dag_run_id")
                    if drid:
                        tr = httpx.get(
                            f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns/{drid}/taskInstances",
                            auth=(AIRFLOW_USER, AIRFLOW_PASS),
                            params={"limit": 100},
                            timeout=15.0,
                        )
                        if tr.status_code < 300:
                            for ti in tr.json().get("task_instances") or []:
                                st = ti.get("state")
                                if st == "running":
                                    current_task = ti.get("task_id")
                                    break
        except Exception:
            pass

    return {
        "latest_run_id": latest_run_id,
        "status": ui_status,
        "started_at": started_at,
        "finished_at": finished_at,
        "triggered_by": triggered_by,
        "current_task": current_task,
        "message": notes,
        "data_ready": bool(has_success and ingested > 0),
        "ingested_file_count": int(ingested),
    }


@router.get("/pipeline/runs")
def list_runs(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    limit: int = 20,
):
    """Recent orchestration runs (admin)."""
    require_admin(x_admin_token)

    url = f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns"
    params = {"limit": limit, "order_by": "-execution_date"}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, auth=(AIRFLOW_USER, AIRFLOW_PASS), params=params)
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"List runs failed: {r.text}")

    return {"runs": r.json().get("dag_runs", []), "dag_id": DAG_ID}


@router.get("/pipeline/runs/{dag_run_id}")
def get_run(
    dag_run_id: str,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    require_admin(x_admin_token)

    url = f"{AIRFLOW_BASE}/dags/{DAG_ID}/dagRuns/{dag_run_id}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, auth=(AIRFLOW_USER, AIRFLOW_PASS))
    if r.status_code >= 300:
        raise HTTPException(r.status_code, f"Get run failed: {r.text}")

    return {"dag_run": r.json()}


@router.get("/pipeline/health")
def pipeline_orchestration_health(
    db=Depends(get_db),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Orchestration and data-plane readiness (admin)."""
    require_admin(x_admin_token)

    db_ready = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ready = False

    last_success_time = None
    r = db.execute(text("""
        SELECT finished_at FROM bronze.ingest_run
        WHERE status = 'success'
        ORDER BY finished_at DESC NULLS LAST
        LIMIT 1
    """)).fetchone()
    if r and r[0]:
        last_success_time = r[0].isoformat()

    return {
        "api_ready": True,
        "db_ready": db_ready,
        "airflow_ready": _airflow_ready(),
        "scheduler_ready": _scheduler_detect_ready(),
        "last_successful_run_finished_at": last_success_time,
    }


class BackfillBody(BaseModel):
    source: str = Field(default="oilgasdata", description="Logical source key")
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@router.post("/pipeline/backfill")
def admin_backfill(
    body: BackfillBody,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Run full pipeline logic in-process (same steps as automated ingestion)."""
    require_admin(x_admin_token)
    try:
        from core.run_pipeline import run_full_pipeline
    except ImportError as e:
        raise HTTPException(
            503,
            "Pipeline modules not on PYTHONPATH (mount core/ in API container). " + str(e),
        )

    result = run_full_pipeline(triggered_by="backfill")
    if result.get("status") == "fail":
        raise HTTPException(500, result)
    return result


@router.get("/pipeline/runs/db")
def list_runs_db(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    db=Depends(get_db),
    limit: int = 30,
):
    """Recent runs from application audit table."""
    require_admin(x_admin_token)
    r = db.execute(text("""
        SELECT run_id, dag_id, triggered_by, started_at, finished_at, status, notes
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT :lim
    """), {"lim": limit})
    rows = r.fetchall()

    def _iso(d):
        if d is None:
            return None
        s = d.isoformat()
        if getattr(d, "tzinfo", None) is None and "Z" not in s and "+" not in s:
            return s.replace(" ", "T", 1) + "Z" if " " in s else s + "Z"
        return s

    out = []
    for row in rows:
        out.append({
            "run_id": str(row[0]),
            "dag_id": str(row[1]) if row[1] else None,
            "triggered_by": str(row[2]) if row[2] else None,
            "started_at": _iso(row[3]),
            "finished_at": _iso(row[4]),
            "status": str(row[5]) if row[5] else None,
            "notes": str(row[6]) if row[6] else None,
        })
    return {"runs": out}
