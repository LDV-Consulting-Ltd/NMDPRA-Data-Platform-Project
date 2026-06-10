"""
Transparent rule configuration for PetroGrid Patterns v0.1.
Patterns cluster co-occurring signals from PetroGrid Signals v0.1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_PATTERN_TYPES: tuple[str, ...] = (
    "recurring_pipeline_issue_pattern",
    "recurring_ingestion_health_pattern",
    "repeated_data_readiness_issue_pattern",
    "repeated_dq_failure_pattern",
    "recurring_coverage_gap_pattern",
    "recurring_api_availability_gap_pattern",
    "recurring_data_layer_availability_gap_pattern",
    "recurring_business_dataset_gap_pattern",
)

ALLOWED_STATUSES: tuple[str, ...] = (
    "new",
    "acknowledged",
    "under_review",
    "dismissed",
    "archived",
)

THRESHOLDS: dict[str, Any] = {
    "minimum_related_signals": 2,
    "minimum_signal_types_for_cluster": 2,
    "high_severity_signal_count_threshold": 2,
    "repeated_source_gap_threshold": 2,
    "dq_failure_signal_threshold": 2,
    "data_layer_gap_threshold": 2,
    "business_dataset_gap_threshold": 2,
    "pipeline_cluster_minimum": 2,
    "ingestion_cluster_minimum": 2,
}

HIGH_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})

AVAILABILITY_SIGNAL_TYPES: tuple[str, ...] = (
    "fuel_price_availability_signal",
    "refinery_status_availability_signal",
    "vessel_clearance_availability_signal",
    "archive_availability_signal",
)


@dataclass(frozen=True)
class PatternRuleDefinition:
    rule_id: str
    pattern_type: str
    pattern_name: str
    description: str
    evidence_summary_template: str
    confidence: float
    matching_signal_types: tuple[str, ...]
    threshold_key: str
    limitations: str
    cluster_rule: str


PATTERN_RULES: dict[str, PatternRuleDefinition] = {
    "recurring_pipeline_issue": PatternRuleDefinition(
        rule_id="recurring_pipeline_issue",
        pattern_type="recurring_pipeline_issue_pattern",
        pattern_name="Recurring pipeline issues",
        description=(
            "Pipeline, ingestion, or data-readiness signals cluster together, "
            "indicating sustained operational attention across pipeline evidence."
        ),
        evidence_summary_template=(
            "{count} pipeline-related signals across {type_count} signal types."
        ),
        confidence=0.86,
        matching_signal_types=(
            "pipeline_status_signal",
            "ingestion_health_signal",
            "data_readiness_signal",
        ),
        threshold_key="pipeline_cluster_minimum",
        limitations=(
            "v0.1 detects co-occurring signals at request time only; "
            "not historical recurrence across runs."
        ),
        cluster_rule="matching_signal_types",
    ),
    "recurring_ingestion_health": PatternRuleDefinition(
        rule_id="recurring_ingestion_health",
        pattern_type="recurring_ingestion_health_pattern",
        pattern_name="Recurring ingestion health issues",
        description=(
            "Ingestion health signals cluster with other operational signals, "
            "suggesting repeated ingest-run attention items."
        ),
        evidence_summary_template=(
            "Ingestion health signal clusters with {count} related signals."
        ),
        confidence=0.84,
        matching_signal_types=("ingestion_health_signal",),
        threshold_key="ingestion_cluster_minimum",
        limitations=(
            "Based on latest-run ingestion evidence surfaced as signals; "
            "not root-cause classification."
        ),
        cluster_rule="anchor_with_cluster",
    ),
    "repeated_data_readiness": PatternRuleDefinition(
        rule_id="repeated_data_readiness",
        pattern_type="repeated_data_readiness_issue_pattern",
        pattern_name="Repeated data readiness issues",
        description=(
            "Data readiness signals co-occur with coverage or pipeline signals, "
            "indicating a clustered readiness gap."
        ),
        evidence_summary_template=(
            "Data readiness signal clusters with {count} related signals "
            "across {type_count} types."
        ),
        confidence=0.88,
        matching_signal_types=("data_readiness_signal",),
        threshold_key="minimum_related_signals",
        limitations=(
            "Reflects bronze.ingest_run and file_registry readiness checks only."
        ),
        cluster_rule="anchor_with_cluster",
    ),
    "repeated_dq_failure": PatternRuleDefinition(
        rule_id="repeated_dq_failure",
        pattern_type="repeated_dq_failure_pattern",
        pattern_name="Repeated data quality failures",
        description=(
            "DQ failure signals cluster with additional governance or coverage signals."
        ),
        evidence_summary_template=(
            "DQ failure signal clusters with {count} related signals."
        ),
        confidence=0.83,
        matching_signal_types=("dq_failure_signal",),
        threshold_key="dq_failure_signal_threshold",
        limitations=(
            "Uses simplified DQ outcomes on latest run; not row-level validation history."
        ),
        cluster_rule="anchor_with_cluster",
    ),
    "recurring_coverage_gap": PatternRuleDefinition(
        rule_id="recurring_coverage_gap",
        pattern_type="recurring_coverage_gap_pattern",
        pattern_name="Recurring source coverage gaps",
        description=(
            "Source coverage and API coverage signals cluster, "
            "indicating repeated gaps across report registry evidence."
        ),
        evidence_summary_template=(
            "{count} coverage-related signals across source and API layers."
        ),
        confidence=0.85,
        matching_signal_types=(
            "source_coverage_signal",
            "api_coverage_signal",
        ),
        threshold_key="repeated_source_gap_threshold",
        limitations=(
            "Expected sources are fixed; partial coverage does not alone trigger this pattern."
        ),
        cluster_rule="matching_signal_types",
    ),
    "recurring_api_availability_gap": PatternRuleDefinition(
        rule_id="recurring_api_availability_gap",
        pattern_type="recurring_api_availability_gap_pattern",
        pattern_name="Recurring API availability gaps",
        description=(
            "API coverage degradation clusters with business dataset availability signals."
        ),
        evidence_summary_template=(
            "{count} API availability signals across {type_count} signal types."
        ),
        confidence=0.82,
        matching_signal_types=(
            "api_coverage_signal",
            *AVAILABILITY_SIGNAL_TYPES,
        ),
        threshold_key="minimum_related_signals",
        limitations=(
            "Heuristic across bronze backing tables; not market or compliance assessment."
        ),
        cluster_rule="matching_signal_types",
    ),
    "recurring_data_layer_availability_gap": PatternRuleDefinition(
        rule_id="recurring_data_layer_availability_gap",
        pattern_type="recurring_data_layer_availability_gap_pattern",
        pattern_name="Recurring data layer availability gaps",
        description=(
            "Gold layer availability signals cluster with pipeline or coverage signals."
        ),
        evidence_summary_template=(
            "Data layer gap clusters with {count} related signals."
        ),
        confidence=0.8,
        matching_signal_types=("data_layer_availability_signal",),
        threshold_key="data_layer_gap_threshold",
        limitations=(
            "Gold row counts use pg_class approximations; silver is not persisted."
        ),
        cluster_rule="anchor_with_cluster",
    ),
    "recurring_business_dataset_gap": PatternRuleDefinition(
        rule_id="recurring_business_dataset_gap",
        pattern_type="recurring_business_dataset_gap_pattern",
        pattern_name="Recurring business dataset gaps",
        description=(
            "Multiple business dataset availability signals cluster together."
        ),
        evidence_summary_template=(
            "{count} business dataset availability signals across {type_count} domains."
        ),
        confidence=0.87,
        matching_signal_types=AVAILABILITY_SIGNAL_TYPES,
        threshold_key="business_dataset_gap_threshold",
        limitations=(
            "Table emptiness only; not supply shortage or pricing anomaly detection."
        ),
        cluster_rule="matching_signal_types",
    ),
}
