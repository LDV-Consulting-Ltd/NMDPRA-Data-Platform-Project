"""
Transparent rule configuration for PetroGrid Signals v0.1.
Rules map observable evidence from existing endpoints/tables to attention signals.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

ALLOWED_SIGNAL_TYPES: tuple[str, ...] = (
    "pipeline_status_signal",
    "ingestion_health_signal",
    "data_readiness_signal",
    "dq_failure_signal",
    "source_coverage_signal",
    "api_coverage_signal",
    "data_layer_availability_signal",
    "fuel_price_availability_signal",
    "refinery_status_availability_signal",
    "vessel_clearance_availability_signal",
    "archive_availability_signal",
)

ALLOWED_SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")
ALLOWED_STATUSES: tuple[str, ...] = (
    "new",
    "acknowledged",
    "under_review",
    "dismissed",
    "archived",
)


@dataclass(frozen=True)
class SignalRuleDefinition:
    rule_id: str
    signal_type: str
    signal_name: str
    description: str
    severity: str
    confidence: float
    source_endpoint: str
    source_table: Optional[str]
    related_data_products: tuple[str, ...]
    limitations: str
    evidence_field: str
    threshold: Any


THRESHOLDS: dict[str, Any] = {
    "ingestion_failures_count_gt": 0,
    "dq_failures_count_gt": 0,
    "reports_total_eq": 0,
    "downloaded_reports_total_eq": 0,
    "gold_total_rows_eq": 0,
    "fuel_prices_total_eq": 0,
    "refinery_status_total_eq": 0,
    "vessel_clearance_total_eq": 0,
    "archive_total_rows_eq": 0,
    "api_empty_backing_tables_min": 3,
    "pipeline_failed_status": "failed",
    "data_ready_expected": True,
}

SIGNAL_RULES: dict[str, SignalRuleDefinition] = {
    "data_ready_false": SignalRuleDefinition(
        rule_id="data_ready_false",
        signal_type="data_readiness_signal",
        signal_name="Data not ready",
        description="Pipeline has not produced ingested source files required for business APIs.",
        severity="high",
        confidence=0.92,
        source_endpoint="/v1/pipeline/status",
        source_table="bronze.ingest_run",
        related_data_products=("api.reports", "api.coverage"),
        limitations="Reflects bronze.ingest_run and bronze.file_registry only; does not assess gold mart freshness.",
        evidence_field="data_ready",
        threshold=THRESHOLDS["data_ready_expected"],
    ),
    "pipeline_status_failed": SignalRuleDefinition(
        rule_id="pipeline_status_failed",
        signal_type="pipeline_status_signal",
        signal_name="Latest pipeline run failed",
        description="The most recent ingest run did not complete successfully.",
        severity="critical",
        confidence=0.95,
        source_endpoint="/v1/pipeline/status",
        source_table="bronze.ingest_run",
        related_data_products=("api.reports",),
        limitations="Based on latest bronze.ingest_run row only; does not inspect orchestrator task logs.",
        evidence_field="status",
        threshold=THRESHOLDS["pipeline_failed_status"],
    ),
    "ingestion_failures_count_gt_0": SignalRuleDefinition(
        rule_id="ingestion_failures_count_gt_0",
        signal_type="ingestion_health_signal",
        signal_name="Ingestion failures recorded",
        description="One or more ingest runs have a failed status in pipeline history.",
        severity="high",
        confidence=0.88,
        source_endpoint="/v1/governance/health/ingestion",
        source_table="bronze.ingest_run",
        related_data_products=("api.reports", "api.coverage"),
        limitations="Counts failed ingest_run rows; does not classify root cause of failure.",
        evidence_field="ingestion_failures_count",
        threshold=THRESHOLDS["ingestion_failures_count_gt"],
    ),
    "dq_failures_count_gt_0": SignalRuleDefinition(
        rule_id="dq_failures_count_gt_0",
        signal_type="dq_failure_signal",
        signal_name="Data quality failures on latest run",
        description="DQ results for the latest ingest run include one or more failed checks.",
        severity="medium",
        confidence=0.9,
        source_endpoint="/v1/governance/dq/results",
        source_table="bronze.dq_result",
        related_data_products=("api.coverage",),
        limitations="Uses simplified DQ outcomes on latest run_id; not full row-level validation.",
        evidence_field="dq_failures_count",
        threshold=THRESHOLDS["dq_failures_count_gt"],
    ),
    "coverage_empty": SignalRuleDefinition(
        rule_id="coverage_empty",
        signal_type="source_coverage_signal",
        signal_name="No source report coverage",
        description="No expected NMDPRA source feeds have downloaded files in the registry.",
        severity="medium",
        confidence=0.9,
        source_endpoint="/v1/coverage",
        source_table="bronze.file_registry",
        related_data_products=("api.coverage", "api.reports"),
        limitations="Expected sources are fixed in reports router; partial coverage does not trigger this rule.",
        evidence_field="sources_with_data_count",
        threshold=0,
    ),
    "reports_empty": SignalRuleDefinition(
        rule_id="reports_empty",
        signal_type="api_coverage_signal",
        signal_name="Report registry empty",
        description="No files are registered in the source report catalog.",
        severity="medium",
        confidence=0.93,
        source_endpoint="/v1/reports",
        source_table="bronze.file_registry",
        related_data_products=("api.reports",),
        limitations="Counts all file_registry rows, not only downloaded files.",
        evidence_field="reports_total",
        threshold=THRESHOLDS["reports_total_eq"],
    ),
    "gold_layer_empty": SignalRuleDefinition(
        rule_id="gold_layer_empty",
        signal_type="data_layer_availability_signal",
        signal_name="Gold warehouse layer empty",
        description="Gold schema tables exist but contain no rows.",
        severity="medium",
        confidence=0.85,
        source_endpoint="/v1/data-layers/tables",
        source_table="gold.*",
        related_data_products=("api.data_layers",),
        limitations="Uses pg_class reltuples approximations; exact counts may differ slightly.",
        evidence_field="gold_total_rows",
        threshold=THRESHOLDS["gold_total_rows_eq"],
    ),
    "fuel_prices_empty": SignalRuleDefinition(
        rule_id="fuel_prices_empty",
        signal_type="fuel_price_availability_signal",
        signal_name="Fuel price data unavailable",
        description="Fuel price bronze table has no rows for the business API.",
        severity="medium",
        confidence=0.94,
        source_endpoint="/v1/prices/fuel",
        source_table="bronze.fuel_prices_city",
        related_data_products=("api.fuel_prices",),
        limitations="Table emptiness only; does not assess price anomaly or market intelligence.",
        evidence_field="fuel_prices_total",
        threshold=THRESHOLDS["fuel_prices_total_eq"],
    ),
    "refinery_status_empty": SignalRuleDefinition(
        rule_id="refinery_status_empty",
        signal_type="refinery_status_availability_signal",
        signal_name="Refinery status data unavailable",
        description="Refinery status bronze table has no rows for the business API.",
        severity="medium",
        confidence=0.94,
        source_endpoint="/v1/refineries/status",
        source_table="bronze.refinery_status",
        related_data_products=("api.refineries",),
        limitations="Table emptiness only; does not assess supply risk or operational decisions.",
        evidence_field="refinery_status_total",
        threshold=THRESHOLDS["refinery_status_total_eq"],
    ),
    "vessel_clearance_empty": SignalRuleDefinition(
        rule_id="vessel_clearance_empty",
        signal_type="vessel_clearance_availability_signal",
        signal_name="Vessel clearance data unavailable",
        description="Vessel clearance schedule bronze table has no rows.",
        severity="low",
        confidence=0.94,
        source_endpoint="/v1/vessels/clearance",
        source_table="bronze.vessel_clearance_schedule",
        related_data_products=("api.vessels",),
        limitations="Table emptiness only; not a maritime risk or compliance assessment.",
        evidence_field="vessel_clearance_total",
        threshold=THRESHOLDS["vessel_clearance_total_eq"],
    ),
    "archive_empty": SignalRuleDefinition(
        rule_id="archive_empty",
        signal_type="archive_availability_signal",
        signal_name="Archive feeds empty",
        description="Archived truckout and stock bronze tables contain no rows.",
        severity="low",
        confidence=0.9,
        source_endpoint="/v1/archive/truckout/depot",
        source_table="bronze.truckout_by_depot_daily",
        related_data_products=("api.archive",),
        limitations="Sums archived truckout and stock tables only; legacy 2023 feeds may legitimately be empty before backfill.",
        evidence_field="archive_total_rows",
        threshold=THRESHOLDS["archive_total_rows_eq"],
    ),
    "api_coverage_degraded": SignalRuleDefinition(
        rule_id="api_coverage_degraded",
        signal_type="api_coverage_signal",
        signal_name="Multiple business API backing tables empty",
        description="Several business API bronze backing tables are empty while data readiness may be partial.",
        severity="medium",
        confidence=0.82,
        source_endpoint="/v1/coverage",
        source_table="bronze.*",
        related_data_products=(
            "api.fuel_prices",
            "api.refineries",
            "api.vessels",
            "api.highlights",
        ),
        limitations="Heuristic across a fixed set of business tables; not a market or compliance signal.",
        evidence_field="empty_business_table_count",
        threshold=THRESHOLDS["api_empty_backing_tables_min"],
    ),
}
