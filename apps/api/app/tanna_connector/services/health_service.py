"""Aggregate PetroGrid health signals for Tanna connector."""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.tanna_connector.schemas import external_id_health_check
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status

AIRFLOW_BASE = os.getenv("AIRFLOW_API_BASE", "http://localhost:8080/api/v1").rstrip("/")
AIRFLOW_USER = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASSWORD", "admin")
ADMIN_RUN_TOKEN = os.getenv("ADMIN_RUN_TOKEN", "").strip()
DAG_ID = "nmdpra_end_to_end_dag"


def _airflow_ready() -> bool:
    try:
        root = AIRFLOW_BASE.replace("/api/v1", "")
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{root}/health")
            return response.status_code < 300
    except Exception:
        return False


def _pipeline_status(db) -> dict[str, Any]:
    try:
        row = db.execute(
            text("""
                SELECT run_id, status, started_at, finished_at
                FROM bronze.ingest_run
                ORDER BY started_at DESC
                LIMIT 1
            """)
        ).fetchone()
        ingested = db.execute(
            text("SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL")
        ).scalar() or 0
        has_success = bool(
            db.execute(
                text("SELECT EXISTS (SELECT 1 FROM bronze.ingest_run WHERE status = 'success' LIMIT 1)")
            ).scalar()
        )
        return {
            "status": row[1] if row else "idle",
            "latest_run_id": str(row[0]) if row and row[0] else None,
            "data_ready": bool(has_success and ingested > 0),
            "ingested_file_count": int(ingested),
        }
    except SQLAlchemyError as exc:
        return {"status": "unavailable", "error": str(exc), "data_ready": False}


def _ingestion_health(db) -> dict[str, Any]:
    try:
        row = db.execute(
            text("""
                SELECT run_id, status, finished_at
                FROM bronze.ingest_run
                ORDER BY started_at DESC
                LIMIT 1
            """)
        ).fetchone()
        ingested = db.execute(
            text("SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL")
        ).scalar() or 0
        failures = 0
        if row and row[0]:
            failures = (
                db.execute(
                    text(
                        "SELECT COUNT(*) FROM bronze.dq_result "
                        "WHERE run_id = :run_id AND passed = false"
                    ),
                    {"run_id": str(row[0])},
                ).scalar()
                or 0
            )
        return {
            "last_run_status": row[1] if row else None,
            "failures_count": int(failures),
            "ingested_file_count": int(ingested),
        }
    except SQLAlchemyError as exc:
        return {"status": "unavailable", "error": str(exc)}


def _admin_pipeline_health(db) -> Optional[dict[str, Any]]:
    if not ADMIN_RUN_TOKEN:
        return None
    db_ready = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ready = False
    last_success_time = None
    try:
        row = db.execute(
            text("""
                SELECT finished_at FROM bronze.ingest_run
                WHERE status = 'success'
                ORDER BY finished_at DESC NULLS LAST
                LIMIT 1
            """)
        ).fetchone()
        if row and row[0]:
            last_success_time = row[0].isoformat()
    except SQLAlchemyError:
        pass
    return {
        "api_ready": True,
        "db_ready": db_ready,
        "airflow_ready": _airflow_ready(),
        "last_successful_run_finished_at": last_success_time,
        "admin_token_configured": True,
    }


def build_tanna_health(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    items.append(
        {
            "external_id": external_id_health_check("api_liveness"),
            "check": "api_liveness",
            "status": "ok",
            "detail": {"source": "GET /health"},
        }
    )

    pipeline = _pipeline_status(db)
    items.append(
        {
            "external_id": external_id_health_check("pipeline_status"),
            "check": "pipeline_status",
            "status": "ok" if pipeline.get("data_ready") else "degraded",
            "detail": {**pipeline, "source": "GET /v1/pipeline/status"},
        }
    )
    if pipeline.get("error"):
        warnings.append(f"Pipeline status degraded: {pipeline['error']}")

    ingestion = _ingestion_health(db)
    items.append(
        {
            "external_id": external_id_health_check("ingestion_health"),
            "check": "ingestion_health",
            "status": "ok" if ingestion.get("last_run_status") == "success" else "degraded",
            "detail": {**ingestion, "source": "GET /v1/governance/health/ingestion"},
        }
    )
    if ingestion.get("error"):
        warnings.append(f"Ingestion health degraded: {ingestion['error']}")

    admin_health = _admin_pipeline_health(db)
    if admin_health is not None:
        items.append(
            {
                "external_id": external_id_health_check("admin_pipeline_health"),
                "check": "admin_pipeline_health",
                "status": "ok" if admin_health.get("db_ready") else "degraded",
                "detail": {**admin_health, "source": "GET /v1/admin/pipeline/health"},
            }
        )
    else:
        warnings.append(
            "Admin pipeline health skipped: ADMIN_RUN_TOKEN not configured on server."
        )

    degraded = any(item["status"] == "degraded" for item in items)
    implementation_status = "partial" if degraded or admin_health is None else "implemented"
    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)

    return build_envelope(
        object_type="health",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.health_service",
        notes=(
            "Aggregated PetroGrid health from API liveness, pipeline status, ingestion health, "
            "and optional admin pipeline health. Read-only; no ingestion triggers."
        ),
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surfaces": ["/health", "/v1/pipeline/status", "/v1/governance/health/ingestion"]},
    )


def assess_health_maturity(db) -> dict[str, Any]:
    payload = build_tanna_health(db)
    return {
        "endpoint": "health",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
