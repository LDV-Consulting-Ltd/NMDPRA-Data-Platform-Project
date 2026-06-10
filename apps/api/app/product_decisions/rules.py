"""
Transparent rule configuration for PetroGrid Decision Products v0.1.
Decision products connect evidence, context, and human review areas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_DECISION_TYPES: tuple[str, ...] = (
    "data_readiness_review",
    "ingestion_health_review",
    "dq_remediation_review",
    "coverage_gap_review",
    "api_availability_review",
    "data_layer_readiness_review",
    "business_dataset_readiness_review",
)

DECISION_STATUS_V01: str = "draft"

REVIEW_PHRASES: tuple[str, ...] = (
    "supports review of",
    "helps assess",
    "provides evidence for",
    "may inform",
    "requires human review",
)

FORBIDDEN_DECISION_PHRASES: tuple[str, ...] = (
    "should approve",
    "should reject",
    "must enforce",
    "guarantees",
    "confirms",
    "automated decision",
    "auto-approve",
)

THRESHOLDS: dict[str, Any] = {
    "minimum_signals_for_shell": 1,
    "minimum_patterns_for_shell": 1,
}

AVAILABILITY_SIGNAL_TYPES: tuple[str, ...] = (
    "fuel_price_availability_signal",
    "refinery_status_availability_signal",
    "vessel_clearance_availability_signal",
    "archive_availability_signal",
)


@dataclass(frozen=True)
class DecisionProductRuleDefinition:
    rule_id: str
    decision_type: str
    decision_product_name: str
    description: str
    supported_decision: str
    business_context: str
    decision_owner_role: str
    decision_area: str
    source_illumination_types: tuple[str, ...]
    source_pattern_types: tuple[str, ...]
    source_signal_types: tuple[str, ...]
    related_data_products: tuple[str, ...]
    limitations: str
    shell_limitations: str


DECISION_RULES: dict[str, DecisionProductRuleDefinition] = {
    "data_readiness_review": DecisionProductRuleDefinition(
        rule_id="data_readiness_review",
        decision_type="data_readiness_review",
        decision_product_name="Data readiness review",
        description=(
            "Provides evidence for whether PetroGrid source ingestion and file registry "
            "state supports review of platform data readiness."
        ),
        supported_decision=(
            "Supports review of whether business APIs and dashboards may be used "
            "given current bronze ingest evidence."
        ),
        business_context=(
            "Helps assess operational readiness before downstream regulatory "
            "intelligence consumption."
        ),
        decision_owner_role="Data Platform Operator",
        decision_area="data readiness review",
        source_illumination_types=("data_readiness_illumination",),
        source_pattern_types=("repeated_data_readiness_issue_pattern",),
        source_signal_types=("data_readiness_signal",),
        related_data_products=("api.reports", "api.coverage"),
        limitations=(
            "Requires human review; not an automated readiness approval."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "ingestion_health_review": DecisionProductRuleDefinition(
        rule_id="ingestion_health_review",
        decision_type="ingestion_health_review",
        decision_product_name="Ingestion health review",
        description=(
            "Provides evidence for pipeline and ingest-run health to support review "
            "of source refresh operations."
        ),
        supported_decision=(
            "Supports review of whether ingestion operations require follow-up "
            "or scheduling changes."
        ),
        business_context=(
            "May inform operational planning for NMDPRA source report refresh cycles."
        ),
        decision_owner_role="Pipeline Operations Lead",
        decision_area="ingestion health review",
        source_illumination_types=("ingestion_health_illumination",),
        source_pattern_types=(
            "recurring_ingestion_health_pattern",
            "recurring_pipeline_issue_pattern",
        ),
        source_signal_types=(
            "ingestion_health_signal",
            "pipeline_status_signal",
        ),
        related_data_products=("api.reports",),
        limitations=(
            "Requires human review; not automated pipeline remediation."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "dq_remediation_review": DecisionProductRuleDefinition(
        rule_id="dq_remediation_review",
        decision_type="dq_remediation_review",
        decision_product_name="DQ remediation review",
        description=(
            "Provides evidence for data quality outcomes on the latest ingest run "
            "to support review of remediation priorities."
        ),
        supported_decision=(
            "Supports review of whether affected bronze tables require DQ "
            "remediation before consumption."
        ),
        business_context=(
            "Helps assess governed dataset reliability for governance and business APIs."
        ),
        decision_owner_role="Data Governance Lead",
        decision_area="dq remediation review",
        source_illumination_types=("dq_reliability_illumination",),
        source_pattern_types=("repeated_dq_failure_pattern",),
        source_signal_types=("dq_failure_signal",),
        related_data_products=("api.coverage",),
        limitations=(
            "Requires human review; not automated DQ enforcement or row-level fixes."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "coverage_gap_review": DecisionProductRuleDefinition(
        rule_id="coverage_gap_review",
        decision_type="coverage_gap_review",
        decision_product_name="Coverage gap review",
        description=(
            "Provides evidence for source report registry coverage gaps across "
            "expected NMDPRA feeds."
        ),
        supported_decision=(
            "Supports review of whether source discovery or download workflows "
            "require attention."
        ),
        business_context=(
            "May inform completeness of governance coverage and report catalog views."
        ),
        decision_owner_role="Source Coverage Analyst",
        decision_area="coverage gap review",
        source_illumination_types=("coverage_gap_illumination",),
        source_pattern_types=("recurring_coverage_gap_pattern",),
        source_signal_types=(
            "source_coverage_signal",
            "api_coverage_signal",
        ),
        related_data_products=("api.coverage", "api.reports"),
        limitations=(
            "Requires human review; not regulatory enforcement or compliance conclusions."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "api_availability_review": DecisionProductRuleDefinition(
        rule_id="api_availability_review",
        decision_type="api_availability_review",
        decision_product_name="API availability review",
        description=(
            "Provides evidence for business API backing table availability "
            "across operational endpoints."
        ),
        supported_decision=(
            "Supports review of whether public business APIs are fit for "
            "operational use given bronze backing state."
        ),
        business_context=(
            "Helps assess API reliability for prices, refineries, vessels, and related domains."
        ),
        decision_owner_role="API Operations Lead",
        decision_area="api availability review",
        source_illumination_types=("api_availability_illumination",),
        source_pattern_types=("recurring_api_availability_gap_pattern",),
        source_signal_types=("api_coverage_signal", *AVAILABILITY_SIGNAL_TYPES),
        related_data_products=(
            "api.fuel_prices",
            "api.refineries",
            "api.vessels",
            "api.highlights",
        ),
        limitations=(
            "Requires human review; not pricing or market intervention decisions."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "data_layer_readiness_review": DecisionProductRuleDefinition(
        rule_id="data_layer_readiness_review",
        decision_type="data_layer_readiness_review",
        decision_product_name="Data layer readiness review",
        description=(
            "Provides evidence for gold warehouse layer population to support "
            "review of mart readiness."
        ),
        supported_decision=(
            "Supports review of whether gold marts are ready for warehouse "
            "introspection and dependent analytics."
        ),
        business_context=(
            "May inform warehouse layer planning; silver is not persisted by pipeline."
        ),
        decision_owner_role="Warehouse Steward",
        decision_area="data layer readiness review",
        source_illumination_types=("data_layer_availability_illumination",),
        source_pattern_types=("recurring_data_layer_availability_gap_pattern",),
        source_signal_types=("data_layer_availability_signal",),
        related_data_products=("api.data_layers",),
        limitations=(
            "Requires human review; uses approximate gold row counts only."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
    "business_dataset_readiness_review": DecisionProductRuleDefinition(
        rule_id="business_dataset_readiness_review",
        decision_type="business_dataset_readiness_review",
        decision_product_name="Business dataset readiness review",
        description=(
            "Provides evidence for domain bronze dataset availability across fuel, "
            "refinery, vessel, and archive feeds."
        ),
        supported_decision=(
            "Supports review of whether domain datasets require backfill or "
            "parser attention before business use."
        ),
        business_context=(
            "Helps assess domain extract readiness; not supply allocation or investment decisions."
        ),
        decision_owner_role="Domain Data Steward",
        decision_area="business dataset readiness review",
        source_illumination_types=("business_dataset_gap_illumination",),
        source_pattern_types=("recurring_business_dataset_gap_pattern",),
        source_signal_types=AVAILABILITY_SIGNAL_TYPES,
        related_data_products=(
            "api.fuel_prices",
            "api.refineries",
            "api.vessels",
            "api.archive",
        ),
        limitations=(
            "Requires human review; not supply shortage or depot risk conclusions."
        ),
        shell_limitations=(
            "Requires human review. Placeholder shell from signals/patterns only; illumination unavailable."
        ),
    ),
}
