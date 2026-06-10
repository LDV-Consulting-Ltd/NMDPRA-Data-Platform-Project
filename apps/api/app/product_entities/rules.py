"""
Entity type definitions for PetroGrid Entities v0.1.
Derived from migration 001, data product registry, and Pydantic schemas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

ALLOWED_ENTITY_GROUPS: tuple[str, ...] = (
    "product",
    "location",
    "facility",
    "report",
    "source_file",
    "ingestion_run",
    "data_layer_table",
    "api_product",
    "refinery",
    "vessel",
    "gas_infrastructure",
    "fuel_price_location",
)

FORBIDDEN_ENTITY_MARKERS: tuple[str, ...] = (
    "market_entity",
    "regulatory_enforcement",
    "supply_shortage",
    "pricing_anomaly",
    "decision_entity",
    "ai_entity",
    "invented",
)

MIGRATION_SOURCE = "alembic/versions/001_initial_schemas.py"
SCHEMAS_SOURCE = "apps/api/app/schemas.py"
REGISTRY_SOURCE = "apps/api/app/data_product_registry.py"

CONFIDENCE: dict[str, float] = {
    "type_summary": 0.92,
    "migration_defined": 0.98,
    "registry_defined": 0.95,
    "pydantic_schema": 0.93,
    "db_instance": 0.9,
}

INSTANCE_QUERY_LIMIT = 50


@dataclass(frozen=True)
class EntityTypeDefinition:
    entity_type: str
    entity_group: str
    display_name: str
    description: str
    source_layer: str
    backing_table: Optional[str]
    backing_api: Optional[str]
    pydantic_schema: Optional[str]
    instance_query: Optional[str]
    instance_id_field: Optional[str]
    instance_name_field: Optional[str]
    attributes_schema: tuple[str, ...]
    limitations: str


ENTITY_TYPE_DEFINITIONS: dict[str, EntityTypeDefinition] = {
    "product": EntityTypeDefinition(
        entity_type="product",
        entity_group="Product",
        display_name="Product",
        description="Petroleum product conformed in gold.dim_product and referenced across bronze facts.",
        source_layer="gold",
        backing_table="gold.dim_product",
        backing_api="GET /v1/data-layers/tables?layer=gold",
        pydantic_schema=None,
        instance_query="SELECT product_key, product_code, product_name, unit_default FROM gold.dim_product LIMIT :lim",
        instance_id_field="product_key",
        instance_name_field="product_name",
        attributes_schema=("product_code", "product_name", "unit_default"),
        limitations="Gold mart dimension; populated when pipeline gold build runs.",
    ),
    "location": EntityTypeDefinition(
        entity_type="location",
        entity_group="Location",
        display_name="Location",
        description="Geographic or depot location conformed in gold.dim_location.",
        source_layer="gold",
        backing_table="gold.dim_location",
        backing_api="GET /v1/data-layers/tables?layer=gold",
        pydantic_schema=None,
        instance_query="SELECT location_key, location_name, location_type FROM gold.dim_location LIMIT :lim",
        instance_id_field="location_key",
        instance_name_field="location_name",
        attributes_schema=("location_name", "location_type"),
        limitations="Gold mart dimension; cities/depots/states derived from bronze during gold build.",
    ),
    "facility": EntityTypeDefinition(
        entity_type="facility",
        entity_group="Facility",
        display_name="Facility",
        description="Refinery or facility conformed in gold.dim_facility.",
        source_layer="gold",
        backing_table="gold.dim_facility",
        backing_api="GET /v1/data-layers/tables?layer=gold",
        pydantic_schema=None,
        instance_query="SELECT facility_key, facility_name, facility_type FROM gold.dim_facility LIMIT :lim",
        instance_id_field="facility_key",
        instance_name_field="facility_name",
        attributes_schema=("facility_name", "facility_type"),
        limitations="Gold mart dimension; sourced from bronze.refinery_status during gold build.",
    ),
    "report": EntityTypeDefinition(
        entity_type="report",
        entity_group="Report",
        display_name="Report",
        description="NMDPRA source report dimension in gold.dim_report and bronze.file_registry catalog.",
        source_layer="gold",
        backing_table="gold.dim_report",
        backing_api="GET /v1/reports",
        pydantic_schema="ReportSummary",
        instance_query="SELECT report_key, source_name, report_title, status FROM gold.dim_report LIMIT :lim",
        instance_id_field="report_key",
        instance_name_field="report_title",
        attributes_schema=("source_name", "report_title", "status"),
        limitations="Gold dim_report seeded from known source names; file_registry holds instance PDFs.",
    ),
    "source_file": EntityTypeDefinition(
        entity_type="source_file",
        entity_group="Source File",
        display_name="Source File",
        description="Discovered or downloaded NMDPRA PDF source file in bronze.file_registry.",
        source_layer="bronze",
        backing_table="bronze.file_registry",
        backing_api="GET /v1/reports",
        pydantic_schema="ReportDetail",
        instance_query="""
            SELECT file_id, source_name, report_title, status, discovered_at, downloaded_at
            FROM bronze.file_registry
            ORDER BY discovered_at DESC
            LIMIT :lim
        """,
        instance_id_field="file_id",
        instance_name_field="report_title",
        attributes_schema=("source_name", "status", "discovered_at", "downloaded_at"),
        limitations="Instances capped per request; requires discover/download pipeline.",
    ),
    "ingestion_run": EntityTypeDefinition(
        entity_type="ingestion_run",
        entity_group="Ingestion Run",
        display_name="Ingestion Run",
        description="Pipeline ingest run recorded in bronze.ingest_run.",
        source_layer="bronze",
        backing_table="bronze.ingest_run",
        backing_api="GET /v1/pipeline/history",
        pydantic_schema="IngestionHealth",
        instance_query="""
            SELECT run_id, dag_id, triggered_by, started_at, finished_at, status
            FROM bronze.ingest_run
            ORDER BY started_at DESC
            LIMIT :lim
        """,
        instance_id_field="run_id",
        instance_name_field="run_id",
        attributes_schema=("dag_id", "triggered_by", "status", "started_at", "finished_at"),
        limitations="Latest runs only; capped per request.",
    ),
    "data_layer_table": EntityTypeDefinition(
        entity_type="data_layer_table",
        entity_group="Data Layer Table",
        display_name="Data Layer Table",
        description="Bronze or gold warehouse table defined in migration schema.",
        source_layer="meta",
        backing_table=None,
        backing_api="GET /v1/data-layers/tables",
        pydantic_schema=None,
        instance_query=None,
        instance_id_field=None,
        instance_name_field=None,
        attributes_schema=("schema", "table_name", "layer"),
        limitations="Table catalog from migration; row counts via data-layers API separately.",
    ),
    "api_product": EntityTypeDefinition(
        entity_type="api_product",
        entity_group="API Product",
        display_name="API Product",
        description="PetroGrid API-backed data product from the data product registry.",
        source_layer="api",
        backing_table=None,
        backing_api="GET /v1/product/data-products",
        pydantic_schema=None,
        instance_query=None,
        instance_id_field=None,
        instance_name_field=None,
        attributes_schema=("product_id", "backing_api", "backing_table", "domain"),
        limitations="Defined in data product registry; not a database row entity.",
    ),
    "refinery": EntityTypeDefinition(
        entity_type="refinery",
        entity_group="Refinery",
        display_name="Refinery",
        description="Refinery named in bronze.refinery_status and exposed via refineries API.",
        source_layer="bronze",
        backing_table="bronze.refinery_status",
        backing_api="GET /v1/refineries/status",
        pydantic_schema="RefineryStatus",
        instance_query="""
            SELECT DISTINCT refinery_name, refinery_type
            FROM bronze.refinery_status
            WHERE refinery_name IS NOT NULL
            ORDER BY refinery_name
            LIMIT :lim
        """,
        instance_id_field="refinery_name",
        instance_name_field="refinery_name",
        attributes_schema=("refinery_name", "refinery_type"),
        limitations="Distinct refinery names from bronze; may be empty before parse/load.",
    ),
    "vessel": EntityTypeDefinition(
        entity_type="vessel",
        entity_group="Vessel",
        display_name="Vessel",
        description="Vessel named in bronze.vessel_clearance_schedule clearance records.",
        source_layer="bronze",
        backing_table="bronze.vessel_clearance_schedule",
        backing_api="GET /v1/vessels/clearance",
        pydantic_schema="VesselClearance",
        instance_query="""
            SELECT DISTINCT vessel_name, company
            FROM bronze.vessel_clearance_schedule
            WHERE vessel_name IS NOT NULL
            ORDER BY vessel_name
            LIMIT :lim
        """,
        instance_id_field="vessel_name",
        instance_name_field="vessel_name",
        attributes_schema=("vessel_name", "company"),
        limitations="Distinct vessel names from bronze; may be empty before vessel schedule ingest.",
    ),
    "gas_infrastructure": EntityTypeDefinition(
        entity_type="gas_infrastructure",
        entity_group="Gas Infrastructure",
        display_name="Gas Infrastructure",
        description="Gas infrastructure item from bronze.gas_infra fact sheet extracts.",
        source_layer="bronze",
        backing_table="bronze.gas_infra",
        backing_api="GET /v1/gas/infra",
        pydantic_schema=None,
        instance_query="""
            SELECT DISTINCT category, item_name, metric_name
            FROM bronze.gas_infra
            WHERE item_name IS NOT NULL
            ORDER BY category, item_name
            LIMIT :lim
        """,
        instance_id_field="item_name",
        instance_name_field="item_name",
        attributes_schema=("category", "item_name", "metric_name"),
        limitations="Distinct gas infra items; table may be empty if parser inserts are limited.",
    ),
    "fuel_price_location": EntityTypeDefinition(
        entity_type="fuel_price_location",
        entity_group="Fuel Price Location",
        display_name="Fuel Price Location",
        description="City location with fuel price observations in bronze.fuel_prices_city.",
        source_layer="bronze",
        backing_table="bronze.fuel_prices_city",
        backing_api="GET /v1/prices/fuel",
        pydantic_schema="FuelPriceCity",
        instance_query="""
            SELECT DISTINCT city
            FROM bronze.fuel_prices_city
            WHERE city IS NOT NULL
            ORDER BY city
            LIMIT :lim
        """,
        instance_id_field="city",
        instance_name_field="city",
        attributes_schema=("city",),
        limitations="Distinct cities from bronze fuel prices; may be empty before parse/load.",
    ),
}

# Migration-defined bronze and gold tables for data_layer_table instances.
MIGRATION_TABLES: tuple[tuple[str, str], ...] = (
    ("bronze", "file_registry"),
    ("bronze", "ingest_run"),
    ("bronze", "ingest_run_file"),
    ("bronze", "fuel_prices_city"),
    ("bronze", "refinery_status"),
    ("bronze", "vessel_clearance_schedule"),
    ("bronze", "gas_infra"),
    ("bronze", "performance_highlights"),
    ("gold", "dim_product"),
    ("gold", "dim_location"),
    ("gold", "dim_facility"),
    ("gold", "dim_report"),
    ("gold", "dim_date"),
    ("gold", "fact_fuel_prices"),
    ("gold", "fact_refinery"),
    ("gold", "fact_vessel_clearance"),
)

THRESHOLDS: dict[str, Any] = {
    "instance_query_limit": INSTANCE_QUERY_LIMIT,
}
