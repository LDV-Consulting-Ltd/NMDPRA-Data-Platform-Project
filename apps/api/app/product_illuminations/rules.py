"""
Transparent rule configuration for PetroGrid Illuminations v0.1.
Illuminations interpret clustered signals and patterns in operational context.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_ILLUMINATION_TYPES: tuple[str, ...] = (
    "data_readiness_illumination",
    "ingestion_health_illumination",
    "dq_reliability_illumination",
    "coverage_gap_illumination",
    "api_availability_illumination",
    "data_layer_availability_illumination",
    "business_dataset_gap_illumination",
)

ALLOWED_STATUSES: tuple[str, ...] = (
    "new",
    "acknowledged",
    "under_review",
    "dismissed",
    "archived",
)

CONSERVATIVE_PHRASES: tuple[str, ...] = (
    "may indicate",
    "may be affected",
    "suggest",
    "suggests",
    "could affect",
    "requires review",
    "appears to",
    "appear to",
)

FORBIDDEN_PHRASES: tuple[str, ...] = (
    "proves",
    "confirms",
    "will cause",
    "guarantees",
    "definitely",
    "certainly",
    "must act",
)

THRESHOLDS: dict[str, Any] = {
    "minimum_signals_without_pattern": 1,
    "minimum_patterns_without_signals": 1,
    "pattern_confidence_boost": 0.05,
    "signal_only_confidence_penalty": 0.08,
}

AVAILABILITY_SIGNAL_TYPES: tuple[str, ...] = (
    "fuel_price_availability_signal",
    "refinery_status_availability_signal",
    "vessel_clearance_availability_signal",
    "archive_availability_signal",
)


@dataclass(frozen=True)
class IlluminationRuleDefinition:
    rule_id: str
    illumination_type: str
    illumination_name: str
    summary: str
    interpretation: str
    business_implication: str
    recommended_attention: str
    base_confidence: float
    source_pattern_types: tuple[str, ...]
    source_signal_types: tuple[str, ...]
    limitations: str
    threshold_key: str


ILLUMINATION_RULES: dict[str, IlluminationRuleDefinition] = {
    "data_readiness_illumination": IlluminationRuleDefinition(
        rule_id="data_readiness_illumination",
        illumination_type="data_readiness_illumination",
        illumination_name="Data readiness context",
        summary=(
            "Data readiness signals and patterns suggest the platform may not yet "
            "have sufficient ingested source files for downstream use."
        ),
        interpretation=(
            "Co-occurring data readiness attention items appear to indicate that "
            "bronze ingest evidence may be incomplete for business API consumption."
        ),
        business_implication=(
            "Stakeholder visibility on dashboards and APIs that depend on ingested "
            "NMDPRA reports may be affected until readiness is restored."
        ),
        recommended_attention=(
            "Requires review of latest pipeline status, ingest runs, and file registry "
            "coverage before relying on business endpoints."
        ),
        base_confidence=0.84,
        source_pattern_types=("repeated_data_readiness_issue_pattern",),
        source_signal_types=("data_readiness_signal",),
        limitations=(
            "Operational readiness only; not a market, supply, or regulatory conclusion."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "ingestion_health_illumination": IlluminationRuleDefinition(
        rule_id="ingestion_health_illumination",
        illumination_type="ingestion_health_illumination",
        illumination_name="Ingestion health context",
        summary=(
            "Ingestion and pipeline signals suggest recurring ingest-run attention "
            "items may indicate operational friction in source refresh."
        ),
        interpretation=(
            "Clustered pipeline and ingestion health evidence appears to indicate "
            "that ingest execution may require operational follow-up."
        ),
        business_implication=(
            "Freshness of downstream regulatory intelligence surfaces may be affected "
            "when ingestion is delayed or unsuccessful."
        ),
        recommended_attention=(
            "Requires review of ingest run history, governance ingestion health, "
            "and pipeline status before scheduling dependent workflows."
        ),
        base_confidence=0.82,
        source_pattern_types=(
            "recurring_ingestion_health_pattern",
            "recurring_pipeline_issue_pattern",
        ),
        source_signal_types=(
            "ingestion_health_signal",
            "pipeline_status_signal",
        ),
        limitations=(
            "Reflects ingest-run and pipeline evidence only; not root-cause diagnosis."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "dq_reliability_illumination": IlluminationRuleDefinition(
        rule_id="dq_reliability_illumination",
        illumination_type="dq_reliability_illumination",
        illumination_name="Data quality reliability context",
        summary=(
            "DQ failure signals suggest data quality checks on the latest run "
            "may indicate reliability concerns for governed datasets."
        ),
        interpretation=(
            "DQ attention items clustered with governance evidence appear to indicate "
            "that published bronze data may require quality review."
        ),
        business_implication=(
            "Confidence in operational metrics from affected reports and APIs may be "
            "affected until DQ outcomes are reviewed."
        ),
        recommended_attention=(
            "Requires review of DQ results for the latest ingest run and affected "
            "bronze tables before downstream consumption."
        ),
        base_confidence=0.8,
        source_pattern_types=("repeated_dq_failure_pattern",),
        source_signal_types=("dq_failure_signal",),
        limitations=(
            "Based on simplified DQ rule outcomes; not full row-level validation history."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "coverage_gap_illumination": IlluminationRuleDefinition(
        rule_id="coverage_gap_illumination",
        illumination_type="coverage_gap_illumination",
        illumination_name="Source coverage gap context",
        summary=(
            "Coverage signals suggest expected NMDPRA source feeds may not yet "
            "have downloaded registry entries."
        ),
        interpretation=(
            "Source and API coverage attention items appear to indicate gaps "
            "across expected report sources in the file registry."
        ),
        business_implication=(
            "Completeness of governance coverage views and dependent business APIs may "
            "be affected while source coverage remains incomplete."
        ),
        recommended_attention=(
            "Requires review of /v1/coverage and /v1/reports before assuming "
            "full source feed availability."
        ),
        base_confidence=0.83,
        source_pattern_types=("recurring_coverage_gap_pattern",),
        source_signal_types=(
            "source_coverage_signal",
            "api_coverage_signal",
        ),
        limitations=(
            "Expected sources are fixed; partial coverage is not fully characterized here."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "api_availability_illumination": IlluminationRuleDefinition(
        rule_id="api_availability_illumination",
        illumination_type="api_availability_illumination",
        illumination_name="API availability context",
        summary=(
            "API coverage and availability signals suggest multiple business API "
            "backing tables may be empty or degraded."
        ),
        interpretation=(
            "Clustered API availability attention items appear to indicate "
            "that several public business endpoints may return limited data."
        ),
        business_implication=(
            "Analytical workflows that rely on prices, refineries, vessels, and related "
            "APIs may be affected until backing bronze tables are populated."
        ),
        recommended_attention=(
            "Requires review of affected business API routes and bronze backing "
            "tables before publishing operational summaries."
        ),
        base_confidence=0.81,
        source_pattern_types=("recurring_api_availability_gap_pattern",),
        source_signal_types=("api_coverage_signal", *AVAILABILITY_SIGNAL_TYPES),
        limitations=(
            "Table emptiness heuristic only; not pricing anomaly or market intelligence."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "data_layer_availability_illumination": IlluminationRuleDefinition(
        rule_id="data_layer_availability_illumination",
        illumination_type="data_layer_availability_illumination",
        illumination_name="Data layer availability context",
        summary=(
            "Data layer availability signals suggest the gold warehouse layer "
            "may not yet contain populated marts."
        ),
        interpretation=(
            "Gold layer attention items clustered with pipeline or coverage signals "
            "appear to indicate warehouse introspection may show empty marts."
        ),
        business_implication=(
            "Warehouse reporting that depends on gold-layer analytics may be affected "
            "until marts are populated by the pipeline."
        ),
        recommended_attention=(
            "Requires review of /v1/data-layers/tables?layer=gold and pipeline "
            "status before assuming warehouse readiness."
        ),
        base_confidence=0.79,
        source_pattern_types=("recurring_data_layer_availability_gap_pattern",),
        source_signal_types=("data_layer_availability_signal",),
        limitations=(
            "Uses pg_class row approximations; silver is not persisted by pipeline."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
    "business_dataset_gap_illumination": IlluminationRuleDefinition(
        rule_id="business_dataset_gap_illumination",
        illumination_type="business_dataset_gap_illumination",
        illumination_name="Business dataset gap context",
        summary=(
            "Business dataset availability signals suggest multiple domain bronze "
            "tables may be empty across fuel, refinery, vessel, or archive feeds."
        ),
        interpretation=(
            "Clustered business dataset availability attention items appear to indicate "
            "sustained gaps across operational domain extracts."
        ),
        business_implication=(
            "Stakeholder situational awareness from domain-specific dashboards and APIs "
            "may be affected until datasets are loaded."
        ),
        recommended_attention=(
            "Requires review of domain API endpoints and bronze backing tables "
            "for fuel prices, refineries, vessels, and archive feeds."
        ),
        base_confidence=0.85,
        source_pattern_types=("recurring_business_dataset_gap_pattern",),
        source_signal_types=AVAILABILITY_SIGNAL_TYPES,
        limitations=(
            "Dataset emptiness only; not supply shortage, depot risk, or compliance conclusions."
        ),
        threshold_key="minimum_signals_without_pattern",
    ),
}
