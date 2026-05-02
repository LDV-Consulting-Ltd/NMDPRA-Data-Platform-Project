"""Governance health: last run status, failures, coverage drift."""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/health/ingestion", response_model=dict)
def ingestion_health(db=Depends(get_db)):
    """GET /v1/governance/health/ingestion - last run status, failures, ingested file counts (no orchestration UI details)."""
    r = db.execute(text("""
        SELECT run_id, status, started_at, finished_at, notes
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT 1
    """))
    row = r.fetchone()
    last_run_id = str(row[0]) if row and row[0] else None
    last_run_status = row[1] if row and len(row) > 1 else None
    last_run_finished_at = row[3].isoformat() if row and len(row) > 4 and row[3] else None
    failures = 0
    if last_run_id:
        r2 = db.execute(text("""
            SELECT COUNT(*) FROM bronze.dq_result
            WHERE run_id = :run_id AND passed = false
        """), {"run_id": last_run_id})
        failures = r2.scalar() or 0

    ingested_file_count = db.execute(text("""
        SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL
    """)).scalar() or 0

    has_successful_run = bool(
        db.execute(text(
            "SELECT EXISTS (SELECT 1 FROM bronze.ingest_run WHERE status = 'success' LIMIT 1)"
        )).scalar()
    )

    data_ready = has_successful_run and ingested_file_count > 0

    return {
        "data": {
            "last_run_id": last_run_id,
            "last_run_status": last_run_status,
            "last_run_finished_at": last_run_finished_at,
            "failures_count": failures,
            "coverage_drift": None,
            "ingested_file_count": int(ingested_file_count),
            "has_successful_run": has_successful_run,
            "data_ready": data_ready,
        },
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
