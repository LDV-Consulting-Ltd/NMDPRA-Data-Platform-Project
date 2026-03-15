"""Data Quality: rules, execution, remediation (rejects), scorecards."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# Rule types and severities
RULE_TYPE_SCHEMA = "schema"
RULE_TYPE_TYPE = "type"
RULE_TYPE_RANGE = "range"
RULE_TYPE_UNIQUENESS = "uniqueness"
RULE_TYPE_REFERENTIAL = "referential"
RULE_TYPE_COMPLETENESS = "completeness"
RULE_TYPE_TIMELINESS = "timeliness"
SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_ERROR = "error"


def _rule(
    rule_name: str,
    layer: str,
    table_name: str,
    rule_type: str,
    rule_definition: dict,
    severity: str = SEVERITY_ERROR,
) -> dict:
    return {
        "rule_id": str(uuid4()),
        "rule_name": rule_name,
        "layer": layer,
        "table_name": table_name,
        "rule_type": rule_type,
        "rule_definition": rule_definition,
        "severity": severity,
        "is_active": True,
    }


def default_dq_rules() -> List[dict]:
    """Return default DQ rules for bronze/silver/gold."""
    rules = []

    # Bronze schema checks (required columns exist)
    for table, cols in [
        ("file_registry", ["file_id", "source_name", "pdf_url", "content_hash"]),
        ("performance_highlights", ["month", "metric_name", "source_file_id"]),
        ("refinery_status", ["month", "refinery_name", "source_file_id"]),
        ("fuel_prices_city", ["month", "city", "source_file_id"]),
        ("vessel_clearance_schedule", ["report_period", "source_file_id"]),
        ("truckout_by_depot_daily", ["report_date", "depot_name", "source_file_id"]),
        ("stock_days_sufficiency_summary", ["report_date", "product", "source_file_id"]),
    ]:
        rules.append(_rule(
            f"bronze_{table}_required_columns",
            "bronze",
            table,
            RULE_TYPE_SCHEMA,
            {"required_columns": cols},
            SEVERITY_ERROR,
        ))

    # Range checks
    rules.append(_rule(
        "utilization_0_100",
        "bronze",
        "refinery_status",
        RULE_TYPE_RANGE,
        {"column": "utilization_pct", "min": 0, "max": 100},
        SEVERITY_WARN,
    ))
    rules.append(_rule(
        "utilization_0_100_modular",
        "bronze",
        "modular_refinery_output",
        RULE_TYPE_RANGE,
        {"column": "capacity_utilization_pct", "min": 0, "max": 100},
        SEVERITY_WARN,
    ))
    rules.append(_rule(
        "prices_non_negative",
        "bronze",
        "fuel_prices_city",
        RULE_TYPE_RANGE,
        {"column": "avg_price", "min": 0},
        SEVERITY_WARN,
    ))
    rules.append(_rule(
        "volumes_non_negative",
        "bronze",
        "truckout_by_depot_daily",
        RULE_TYPE_RANGE,
        {"column": "volume_litres", "min": 0},
        SEVERITY_WARN,
    ))
    rules.append(_rule(
        "days_sufficiency_non_negative",
        "bronze",
        "stock_days_sufficiency_summary",
        RULE_TYPE_RANGE,
        {"column": "total_days_sufficiency", "min": 0},
        SEVERITY_WARN,
    ))

    # Completeness: key fields not null
    for table, key_cols in [
        ("performance_highlights", ["month", "metric_name"]),
        ("refinery_status", ["month", "refinery_name"]),
        ("fuel_prices_city", ["month", "city"]),
        ("vessel_clearance_schedule", ["report_period"]),
    ]:
        rules.append(_rule(
            f"bronze_{table}_completeness",
            "bronze",
            table,
            RULE_TYPE_COMPLETENESS,
            {"columns": key_cols},
            SEVERITY_WARN,
        ))

    return rules


def run_schema_check(rows: List[dict], required_columns: List[str]) -> Tuple[bool, int, List[dict]]:
    """Check that required columns exist in each row. Returns (passed, failed_count, sample_failures)."""
    failed = []
    for i, row in enumerate(rows):
        for col in required_columns:
            if col not in row or row[col] is None or (isinstance(row[col], str) and not row[col].strip()):
                failed.append({"row_index": i, "column": col, "value": row.get(col)})
                if len(failed) >= 10:
                    return False, len(rows) - i + len(failed), failed[:10]
    return len(failed) == 0, len(failed), failed[:10]


def run_range_check(
    rows: List[dict],
    column: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> Tuple[bool, int, List[dict]]:
    """Check numeric column is within [min_val, max_val]. Returns (passed, failed_count, sample_failures)."""
    failed = []
    for i, row in enumerate(rows):
        v = row.get(column)
        if v is None:
            continue
        try:
            n = float(v) if not isinstance(v, (int, float, Decimal)) else float(v)
        except (TypeError, ValueError):
            failed.append({"row_index": i, "column": column, "value": v})
            continue
        if min_val is not None and n < min_val:
            failed.append({"row_index": i, "column": column, "value": n, "min": min_val})
        if max_val is not None and n > max_val:
            failed.append({"row_index": i, "column": column, "value": n, "max": max_val})
        if len(failed) >= 10:
            break
    total_fail = len(failed)
    return total_fail == 0, total_fail, failed[:10]


def run_completeness_check(rows: List[dict], columns: List[str]) -> Tuple[bool, int, List[dict]]:
    """Check key columns are not null/empty. Returns (passed, failed_count, sample_failures)."""
    failed = []
    for i, row in enumerate(rows):
        for col in columns:
            v = row.get(col)
            if v is None or (isinstance(v, str) and not v.strip()):
                failed.append({"row_index": i, "column": col})
        if len(failed) >= 10:
            break
    return len(failed) == 0, len(failed), failed[:10]


def dq_result_record(
    run_id: str,
    layer: str,
    table_name: str,
    rule_id: str,
    passed: bool,
    failed_count: int,
    total_count: int,
    sample_failures: List[dict],
    file_id: Optional[str] = None,
) -> dict:
    return {
        "result_id": str(uuid4()),
        "run_id": run_id,
        "file_id": file_id,
        "layer": layer,
        "table_name": table_name,
        "rule_id": rule_id,
        "passed": passed,
        "failed_count": failed_count,
        "total_count": total_count,
        "sample_failures": sample_failures,
    }
