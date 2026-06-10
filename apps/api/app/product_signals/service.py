"""
PetroGrid Signals v0.1 — read-only, rule-based signal generation from existing evidence.
No persistence, no ingestion/backfill calls, no database writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.product_signals.rules import SIGNAL_RULES, SignalRuleDefinition, THRESHOLDS
from app.routers.reports import COVERAGE_EXPECTED_SOURCES

BUSINESS_BACKING_TABLES: tuple[tuple[str, str], ...] = (
    ("bronze.fuel_prices_city", "api.fuel_prices"),
    ("bronze.refinery_status", "api.refineries"),
    ("bronze.vessel_clearance_schedule", "api.vessels"),
    ("bronze.performance_highlights", "api.highlights"),
    ("bronze.chart_series_values", "api.charts"),
)

ARCHIVE_TABLES: tuple[str, ...] = (
    "bronze.truckout_by_depot_daily",
    "bronze.truckout_by_state_daily",
    "bronze.stock_days_sufficiency_summary",
    "bronze.stock_ledger_by_product",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_scalar(db, sql: str, params: Optional[dict] = None, default: Any = 0) -> Any:
    result = db.execute(text(sql), params or {})
    return result.scalar() if result is not None else default


def _probe(
    *,
    source: str,
    endpoint: str,
    collector: Callable[[Any], dict[str, Any]],
    db: Any,
) -> dict[str, Any]:
    try:
        return {
            "source": source,
            "endpoint": endpoint,
            "available": True,
            "data": collector(db),
            "error": None,
        }
    except SQLAlchemyError as exc:
        return {
            "source": source,
            "endpoint": endpoint,
            "available": False,
            "data": None,
            "error": str(exc),
        }
    except Exception as exc:  # pragma: no cover - defensive for unexpected probe errors
        return {
            "source": source,
            "endpoint": endpoint,
            "available": False,
            "data": None,
            "error": str(exc),
        }


def _collect_pipeline_status(db) -> dict[str, Any]:
    row = db.execute(text("""
        SELECT run_id, status, started_at, finished_at
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()

    ingested = int(_safe_scalar(
        db,
        "SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL",
        default=0,
    ))
    has_success = bool(_safe_scalar(
        db,
        "SELECT EXISTS (SELECT 1 FROM bronze.ingest_run WHERE status = 'success' LIMIT 1)",
        default=False,
    ))
    data_ready = bool(has_success and ingested > 0)

    ui_status = "unknown"
    if row and row[1]:
        if row[1] == "fail":
            ui_status = "failed"
        elif row[1] == "partial":
            ui_status = "running"
        elif row[1] == "success":
            ui_status = "success"

    return {
        "latest_run_id": str(row[0]) if row and row[0] else None,
        "status": ui_status,
        "db_status": row[1] if row else None,
        "data_ready": data_ready,
        "ingested_file_count": ingested,
    }


def _collect_ingestion_health(db) -> dict[str, Any]:
    row = db.execute(text("""
        SELECT run_id, status
        FROM bronze.ingest_run
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()
    last_run_id = str(row[0]) if row and row[0] else None
    last_run_status = row[1] if row else None

    dq_failures = 0
    if last_run_id:
        dq_failures = int(_safe_scalar(
            db,
            """
            SELECT COUNT(*) FROM bronze.dq_result
            WHERE run_id = :run_id AND passed = false
            """,
            {"run_id": last_run_id},
            default=0,
        ))

    ingestion_failures = int(_safe_scalar(
        db,
        "SELECT COUNT(*) FROM bronze.ingest_run WHERE status = 'fail'",
        default=0,
    ))

    return {
        "last_run_id": last_run_id,
        "last_run_status": last_run_status,
        "dq_failures_count": dq_failures,
        "ingestion_failures_count": ingestion_failures,
    }


def _collect_coverage(db) -> dict[str, Any]:
    rows = db.execute(text("""
        SELECT DISTINCT source_name
        FROM bronze.file_registry
        WHERE downloaded_at IS NOT NULL
    """)).fetchall()
    sources_with_data = {row[0] for row in rows}
    missing_sources = [src for src in COVERAGE_EXPECTED_SOURCES if src not in sources_with_data]
    return {
        "sources_with_data_count": len(sources_with_data),
        "sources_with_data": sorted(sources_with_data),
        "expected_sources": list(COVERAGE_EXPECTED_SOURCES),
        "missing_sources": missing_sources,
    }


def _collect_reports(db) -> dict[str, Any]:
    reports_total = int(_safe_scalar(db, "SELECT COUNT(*) FROM bronze.file_registry", default=0))
    downloaded_total = int(_safe_scalar(
        db,
        "SELECT COUNT(*) FROM bronze.file_registry WHERE downloaded_at IS NOT NULL",
        default=0,
    ))
    return {
        "reports_total": reports_total,
        "downloaded_reports_total": downloaded_total,
    }


def _collect_gold_layer(db) -> dict[str, Any]:
    rows = db.execute(text("""
        SELECT COALESCE(SUM(c.reltuples::bigint), 0)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'gold' AND c.relkind = 'r'
    """)).fetchone()
    gold_total = int(rows[0] if rows and rows[0] is not None else 0)
    return {"gold_total_rows": gold_total}


def _table_count(db, table: str) -> int:
    return int(_safe_scalar(db, f"SELECT COUNT(*) FROM {table}", default=0))


def _collect_business_tables(db) -> dict[str, Any]:
    counts = {table: _table_count(db, table) for table, _ in BUSINESS_BACKING_TABLES}
    empty_tables = [table for table, count in counts.items() if count == 0]
    return {
        "business_table_counts": counts,
        "empty_business_table_count": len(empty_tables),
        "empty_business_tables": empty_tables,
    }


def _collect_archive(db) -> dict[str, Any]:
    total = sum(_table_count(db, table) for table in ARCHIVE_TABLES)
    return {"archive_total_rows": total}


def gather_evidence(db) -> tuple[dict[str, Any], list[str]]:
    """Run read-only probes; return merged evidence and source warnings."""
    probes = {
        "pipeline_status": _probe(
            source="pipeline_status",
            endpoint="/v1/pipeline/status",
            collector=_collect_pipeline_status,
            db=db,
        ),
        "ingestion_health": _probe(
            source="ingestion_health",
            endpoint="/v1/governance/health/ingestion",
            collector=_collect_ingestion_health,
            db=db,
        ),
        "coverage": _probe(
            source="coverage",
            endpoint="/v1/coverage",
            collector=_collect_coverage,
            db=db,
        ),
        "reports": _probe(
            source="reports",
            endpoint="/v1/reports",
            collector=_collect_reports,
            db=db,
        ),
        "gold_layer": _probe(
            source="gold_layer",
            endpoint="/v1/data-layers/tables",
            collector=_collect_gold_layer,
            db=db,
        ),
        "business_tables": _probe(
            source="business_tables",
            endpoint="/v1/prices/fuel",
            collector=_collect_business_tables,
            db=db,
        ),
        "archive": _probe(
            source="archive",
            endpoint="/v1/archive/truckout/depot",
            collector=_collect_archive,
            db=db,
        ),
    }

    warnings: list[str] = []
    evidence: dict[str, Any] = {}
    for name, probe in probes.items():
        if not probe["available"]:
            warnings.append(
                f"Source unavailable: {probe['endpoint']} ({probe['error']})"
            )
            continue
        evidence[name] = probe["data"]

    if evidence.get("business_tables"):
        bt = evidence["business_tables"]
        evidence["fuel_prices"] = {
            "fuel_prices_total": bt["business_table_counts"].get("bronze.fuel_prices_city", 0),
        }
        evidence["refinery_status"] = {
            "refinery_status_total": bt["business_table_counts"].get("bronze.refinery_status", 0),
        }
        evidence["vessel_clearance"] = {
            "vessel_clearance_total": bt["business_table_counts"].get(
                "bronze.vessel_clearance_schedule", 0
            ),
        }

    return evidence, warnings


def _build_signal(
    rule: SignalRuleDefinition,
    *,
    observed_value: Any,
    related_entities: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "signal_id": f"{rule.signal_type}.{rule.rule_id}",
        "signal_name": rule.signal_name,
        "signal_type": rule.signal_type,
        "description": rule.description,
        "severity": rule.severity,
        "confidence": rule.confidence,
        "detected_at": _utc_now(),
        "source_endpoint": rule.source_endpoint,
        "source_table": rule.source_table,
        "related_data_products": list(rule.related_data_products),
        "related_entities": related_entities or [],
        "evidence": {
            "source": rule.source_endpoint,
            "field": rule.evidence_field,
            "observed_value": observed_value,
            "rule": rule.rule_id,
            "threshold": rule.threshold,
        },
        "status": "new",
        "limitations": rule.limitations,
    }


def _rule_triggered(rule_id: str, evidence: dict[str, Any]) -> Optional[dict[str, Any]]:
    rule = SIGNAL_RULES[rule_id]

    if rule_id == "data_ready_false":
        ps = evidence.get("pipeline_status")
        if not ps:
            return None
        observed = ps.get("data_ready")
        if observed is False:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "pipeline_status_failed":
        ps = evidence.get("pipeline_status")
        if not ps:
            return None
        observed = ps.get("status")
        if observed == rule.threshold:
            return _build_signal(
                rule,
                observed_value=observed,
                related_entities=[ps.get("latest_run_id")] if ps.get("latest_run_id") else [],
            )
        return None

    if rule_id == "ingestion_failures_count_gt_0":
        ih = evidence.get("ingestion_health")
        if not ih:
            return None
        observed = ih.get("ingestion_failures_count", 0)
        if observed > rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "dq_failures_count_gt_0":
        ih = evidence.get("ingestion_health")
        if not ih:
            return None
        observed = ih.get("dq_failures_count", 0)
        if observed > rule.threshold:
            return _build_signal(
                rule,
                observed_value=observed,
                related_entities=[ih.get("last_run_id")] if ih.get("last_run_id") else [],
            )
        return None

    if rule_id == "coverage_empty":
        cov = evidence.get("coverage")
        if not cov:
            return None
        observed = cov.get("sources_with_data_count", 0)
        if observed == rule.threshold:
            return _build_signal(
                rule,
                observed_value=observed,
                related_entities=cov.get("missing_sources", []),
            )
        return None

    if rule_id == "reports_empty":
        rep = evidence.get("reports")
        if not rep:
            return None
        observed = rep.get("reports_total", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "gold_layer_empty":
        gold = evidence.get("gold_layer")
        if not gold:
            return None
        observed = gold.get("gold_total_rows", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "fuel_prices_empty":
        fp = evidence.get("fuel_prices")
        if not fp:
            return None
        observed = fp.get("fuel_prices_total", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "refinery_status_empty":
        rs = evidence.get("refinery_status")
        if not rs:
            return None
        observed = rs.get("refinery_status_total", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "vessel_clearance_empty":
        vc = evidence.get("vessel_clearance")
        if not vc:
            return None
        observed = vc.get("vessel_clearance_total", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "archive_empty":
        arch = evidence.get("archive")
        if not arch:
            return None
        observed = arch.get("archive_total_rows", 0)
        if observed == rule.threshold:
            return _build_signal(rule, observed_value=observed)
        return None

    if rule_id == "api_coverage_degraded":
        bt = evidence.get("business_tables")
        if not bt:
            return None
        observed = bt.get("empty_business_table_count", 0)
        if observed >= rule.threshold:
            return _build_signal(
                rule,
                observed_value=observed,
                related_entities=bt.get("empty_business_tables", []),
            )
        return None

    return None


def evaluate_signals(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply configured rules; only emit signals with supporting evidence."""
    items: list[dict[str, Any]] = []
    for rule_id in SIGNAL_RULES:
        signal = _rule_triggered(rule_id, evidence)
        if signal is not None:
            items.append(signal)
    return items


def build_signals_response(db) -> dict[str, Any]:
    """Build GET /v1/product/signals payload."""
    evidence: dict[str, Any] = {}
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    try:
        evidence, warnings = gather_evidence(db)
        items = evaluate_signals(evidence)
    except SQLAlchemyError as exc:
        warnings.append(f"Signal evidence collection failed: {exc}")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Unexpected signal service error: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.signal_service",
        "generated_at": _utc_now(),
        "notes": (
            "Signals are rule-based and derived from existing PetroGrid operational, "
            "governance, and API evidence."
        ),
        "rule_count": len(SIGNAL_RULES),
        "thresholds": dict(THRESHOLDS),
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "signals",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
