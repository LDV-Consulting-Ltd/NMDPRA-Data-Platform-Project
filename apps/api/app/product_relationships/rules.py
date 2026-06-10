"""
Transparent relationship definitions for PetroGrid Relationship Model v0.1.
Derived from migration 001_initial_schemas.py, data product registry, and pipeline mappings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_RELATIONSHIP_TYPES: tuple[str, ...] = (
    "contains",
    "references",
    "sourced_from",
    "derived_from",
    "loaded_into",
    "produces",
    "consumed_by",
    "documented_by",
    "represented_by",
    "belongs_to",
)

FORBIDDEN_RELATIONSHIP_TYPES: tuple[str, ...] = (
    "influences",
    "causes",
    "predicts",
    "recommends",
    "optimizes",
)

# Confidence bands (nothing below MIN_CONFIDENCE is emitted).
MIN_CONFIDENCE = 0.6
CONFIDENCE: dict[str, float] = {
    "foreign_key": 0.95,
    "lineage_edge": 0.85,
    "source_file_id": 0.75,
    "pipeline_derived": 0.88,
    "documentation": 0.65,
    "entity_registry": 0.7,
}

CONFIDENCE_BANDS: dict[str, str] = {
    "foreign_key": "0.9-1.0",
    "lineage_edge": "0.8-0.9",
    "source_file_id": "0.7-0.8",
    "documentation": "0.6-0.7",
}

RELATIONSHIP_GROUPS: tuple[str, ...] = (
    "data_product_to_api_endpoint",
    "api_endpoint_to_bronze_table",
    "gold_fact_to_gold_dimension",
    "source_file_to_bronze_table",
    "bronze_table_to_gold_table",
    "report_to_source_file",
    "knowledge_asset_to_data_product",
    "entity_to_data_product",
    "lineage_node_to_lineage_node",
)

ENTITIES_SOURCE = "/v1/product/entities"

MIGRATION_SOURCE = "alembic/versions/001_initial_schemas.py"
REGISTRY_SOURCE = "apps/api/app/data_product_registry.py"
PIPELINE_SOURCE = "core/run_pipeline.py:run_silver_gold"


@dataclass(frozen=True)
class ForeignKeyRelationship:
    relationship_id: str
    relationship_type: str
    source_object_type: str
    source_object_id: str
    target_object_type: str
    target_object_id: str
    description: str
    fk_column: str
    fk_target: str


# Gold fact → dimension foreign keys (migration-defined).
GOLD_FACT_DIMENSION_FKS: tuple[ForeignKeyRelationship, ...] = (
    ForeignKeyRelationship(
        "references.gold.fact_fuel_prices.gold.dim_date",
        "references",
        "table",
        "gold.fact_fuel_prices",
        "table",
        "gold.dim_date",
        "fact_fuel_prices.date_month_key references dim_date.date_key",
        "date_month_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_fuel_prices.gold.dim_location",
        "references",
        "table",
        "gold.fact_fuel_prices",
        "table",
        "gold.dim_location",
        "fact_fuel_prices.location_key references dim_location.location_key",
        "location_key",
        "gold.dim_location.location_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_fuel_prices.gold.dim_product",
        "references",
        "table",
        "gold.fact_fuel_prices",
        "table",
        "gold.dim_product",
        "fact_fuel_prices.product_key references dim_product.product_key",
        "product_key",
        "gold.dim_product.product_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_fuel_prices.gold.dim_report",
        "references",
        "table",
        "gold.fact_fuel_prices",
        "table",
        "gold.dim_report",
        "fact_fuel_prices.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_stock_sufficiency.gold.dim_date",
        "references",
        "table",
        "gold.fact_stock_sufficiency",
        "table",
        "gold.dim_date",
        "fact_stock_sufficiency.date_key references dim_date.date_key",
        "date_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_stock_sufficiency.gold.dim_product",
        "references",
        "table",
        "gold.fact_stock_sufficiency",
        "table",
        "gold.dim_product",
        "fact_stock_sufficiency.product_key references dim_product.product_key",
        "product_key",
        "gold.dim_product.product_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_stock_sufficiency.gold.dim_report",
        "references",
        "table",
        "gold.fact_stock_sufficiency",
        "table",
        "gold.dim_report",
        "fact_stock_sufficiency.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_truckout.gold.dim_date",
        "references",
        "table",
        "gold.fact_truckout",
        "table",
        "gold.dim_date",
        "fact_truckout.date_key references dim_date.date_key",
        "date_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_truckout.gold.dim_location",
        "references",
        "table",
        "gold.fact_truckout",
        "table",
        "gold.dim_location",
        "fact_truckout.location_key references dim_location.location_key",
        "location_key",
        "gold.dim_location.location_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_truckout.gold.dim_product",
        "references",
        "table",
        "gold.fact_truckout",
        "table",
        "gold.dim_product",
        "fact_truckout.product_key references dim_product.product_key",
        "product_key",
        "gold.dim_product.product_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_truckout.gold.dim_report",
        "references",
        "table",
        "gold.fact_truckout",
        "table",
        "gold.dim_report",
        "fact_truckout.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_refinery.gold.dim_date",
        "references",
        "table",
        "gold.fact_refinery",
        "table",
        "gold.dim_date",
        "fact_refinery.month_key references dim_date.date_key",
        "month_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_refinery.gold.dim_facility",
        "references",
        "table",
        "gold.fact_refinery",
        "table",
        "gold.dim_facility",
        "fact_refinery.facility_key references dim_facility.facility_key",
        "facility_key",
        "gold.dim_facility.facility_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_refinery.gold.dim_report",
        "references",
        "table",
        "gold.fact_refinery",
        "table",
        "gold.dim_report",
        "fact_refinery.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_vessel_clearance.gold.dim_date",
        "references",
        "table",
        "gold.fact_vessel_clearance",
        "table",
        "gold.dim_date",
        "fact_vessel_clearance.month_key references dim_date.date_key",
        "month_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_vessel_clearance.gold.dim_report",
        "references",
        "table",
        "gold.fact_vessel_clearance",
        "table",
        "gold.dim_report",
        "fact_vessel_clearance.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_series.gold.dim_date",
        "references",
        "table",
        "gold.fact_series",
        "table",
        "gold.dim_date",
        "fact_series.date_key references dim_date.date_key",
        "date_key",
        "gold.dim_date.date_key",
    ),
    ForeignKeyRelationship(
        "references.gold.fact_series.gold.dim_report",
        "references",
        "table",
        "gold.fact_series",
        "table",
        "gold.dim_report",
        "fact_series.report_key references dim_report.report_key",
        "report_key",
        "gold.dim_report.report_key",
    ),
)

# Bronze tables with source_file_id → bronze.file_registry (migration-defined).
BRONZE_SOURCED_FROM_FILE_REGISTRY: tuple[tuple[str, str], ...] = (
    ("bronze.performance_highlights", "source_file_id"),
    ("bronze.refinery_status", "source_file_id"),
    ("bronze.modular_refinery_output", "source_file_id"),
    ("bronze.consumption_benchmark", "source_file_id"),
    ("bronze.actual_consumption_truckout_daily", "source_file_id"),
    ("bronze.fuel_prices_city", "source_file_id"),
    ("bronze.gas_infra", "source_file_id"),
    ("bronze.chart_series_values", "file_id"),
    ("bronze.vessel_clearance_schedule", "source_file_id"),
    ("bronze.truckout_by_depot_daily", "source_file_id"),
    ("bronze.truckout_by_state_daily", "source_file_id"),
    ("bronze.truckout_daily_totals", "source_file_id"),
    ("bronze.stock_days_sufficiency_summary", "source_file_id"),
    ("bronze.stock_ledger_by_product", "source_file_id"),
)

# Bronze ingest/report linkage (migration-defined).
BRONZE_INGEST_FILE_REFERENCES: tuple[tuple[str, str, str], ...] = (
    ("bronze.ingest_run_file", "file_id", "bronze.file_registry"),
    ("bronze.rejects", "file_id", "bronze.file_registry"),
    ("bronze.dq_result", "file_id", "bronze.file_registry"),
)

# Gold mart derived from bronze tables (pipeline run_silver_gold mapping).
GOLD_DERIVED_FROM_BRONZE: tuple[tuple[str, str], ...] = (
    ("gold.fact_fuel_prices", "bronze.fuel_prices_city"),
    ("gold.fact_stock_sufficiency", "bronze.stock_days_sufficiency_summary"),
    ("gold.fact_truckout", "bronze.truckout_by_depot_daily"),
    ("gold.fact_truckout", "bronze.truckout_by_state_daily"),
    ("gold.fact_refinery", "bronze.refinery_status"),
    ("gold.fact_refinery", "bronze.modular_refinery_output"),
    ("gold.fact_vessel_clearance", "bronze.vessel_clearance_schedule"),
    ("gold.fact_series", "bronze.chart_series_values"),
)

# Knowledge assets documented in product manifest knowledge_assets capability.
KNOWLEDGE_ASSETS: tuple[dict[str, str], ...] = (
    {"id": "knowledge.openapi", "name": "OpenAPI specification", "location": "/openapi.json"},
    {"id": "knowledge.readme", "name": "README.md", "location": "README.md"},
    {"id": "knowledge.product_manifest", "name": "Product manifest API", "location": "/v1/product/manifest"},
    {"id": "knowledge.data_product_registry", "name": "Data product registry API", "location": "/v1/product/data-products"},
)

KNOWLEDGE_ASSET_TO_DATA_PRODUCT: tuple[tuple[str, str], ...] = (
    ("knowledge.openapi", "api.reports"),
    ("knowledge.readme", "petrogrid"),
    ("knowledge.product_manifest", "petrogrid"),
    ("knowledge.data_product_registry", "petrogrid"),
)

KNOWLEDGE_ASSET_TO_ENTITY: tuple[tuple[str, str, str], ...] = (
    ("knowledge.readme", "product", "petrogrid"),
    ("knowledge.product_manifest", "product", "petrogrid"),
)
