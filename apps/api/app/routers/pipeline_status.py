"""Sanitized pipeline status from DB for dashboards (no orchestration product vocabulary)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/pipeline")


def _iso(d):
    if d is None:
        return None
    s = d.isoformat()
    if s.endswith("+00:00"):
        return s
    if getattr(d, "tzinfo", None) is None and "Z" not in s and "+" not in s:
        return s + "Z" if "T" in s else s.replace(" ", "T", 1) + "Z" if " " in s else s + "T00:00:00Z"
    return s


def _map_ui_status(db_status: str | None) -> str:
    """User-facing coarse status for banners."""
    if db_status is None:
        return "unknown"
    if db_status == "partial":
        return "running"
    if db_status == "success":
        return "success"
    if db_status == "fail":
        return "failed"
    return "unknown"


@router.get("/status")
def pipeline_status_public(db=Depends(get_db)):
    """
    GET /v1/pipeline/status — latest pipeline outcome for dashboard banners (public).
    """
    r = db.execute(text("""
        SELECT run_id, status, triggered_by, started_at, finished_at, notes
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT 1
    """))
    row = r.fetchone()

    ingested = db.execute(text(
        "SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL"
    )).scalar() or 0
    has_success = bool(db.execute(text(
        "SELECT EXISTS (SELECT 1 FROM bronze.ingest_run WHERE status = 'success' LIMIT 1)"
    )).scalar())

    data_ready = bool(has_success and ingested > 0)

    if not row or not row[0]:
        return {
            "latest_run_id": None,
            "status": "idle",
            "started_at": None,
            "finished_at": None,
            "triggered_by": None,
            "current_task": None,
            "message": None,
            "data_ready": data_ready,
        }

    db_status = row[1]
    ui_status = _map_ui_status(db_status)

    msg = None
    if ui_status == "running":
        msg = "Data refresh in progress."
    elif ui_status == "failed":
        msg = "Latest refresh did not complete successfully."
    elif not data_ready:
        msg = "Data is being prepared in the background."

    return {
        "latest_run_id": str(row[0]),
        "status": ui_status,
        "started_at": _iso(row[3]),
        "finished_at": _iso(row[4]),
        "triggered_by": str(row[2]) if row[2] is not None else None,
        "current_task": None,
        "message": msg,
        "data_ready": data_ready,
    }


@router.get("/history")
def pipeline_history(db=Depends(get_db), limit: int = Query(50, ge=1, le=200)):
    """Historical runs — prefer admin pages; kept for compatibility."""
    r = db.execute(text("""
        SELECT run_id, dag_id, triggered_by, started_at, finished_at, status, notes
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT :lim
    """), {"lim": limit})
    rows = r.fetchall()
    out = []
    for row in rows:
        out.append({
            "run_id": str(row[0]),
            "dag_id": str(row[1]) if row[1] is not None else None,
            "triggered_by": str(row[2]) if row[2] is not None else None,
            "started_at": _iso(row[3]),
            "finished_at": _iso(row[4]),
            "status": str(row[5]) if row[5] is not None else None,
            "notes": str(row[6]) if row[6] is not None else None,
        })
    return {"runs": out}
