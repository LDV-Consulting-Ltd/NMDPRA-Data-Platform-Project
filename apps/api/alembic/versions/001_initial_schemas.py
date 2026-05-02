"""Initial bronze, silver, gold, meta schemas and tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    op.execute("CREATE SCHEMA IF NOT EXISTS silver")
    op.execute("CREATE SCHEMA IF NOT EXISTS gold")
    op.execute("CREATE SCHEMA IF NOT EXISTS meta")

    # --- BRONZE: enums ---
    op.execute("""
        CREATE TYPE bronze.source_name_enum AS ENUM (
            'oilgasdata', 'vesselschedule', 'dailytruckout', 'stockreport'
        )
    """)
    op.execute("CREATE TYPE bronze.file_status_enum AS ENUM ('active', 'archived', 'paused')")
    op.execute("CREATE TYPE bronze.triggered_by_enum AS ENUM ('schedule', 'manual', 'backfill')")
    op.execute("CREATE TYPE bronze.run_status_enum AS ENUM ('success', 'fail', 'partial')")
    op.execute("CREATE TYPE bronze.period_type_enum AS ENUM ('daily', 'monthly')")
    op.execute("""
        CREATE TYPE bronze.dq_rule_type_enum AS ENUM (
            'schema', 'type', 'range', 'uniqueness', 'referential', 'completeness', 'timeliness'
        )
    """)
    op.execute("CREATE TYPE bronze.dq_severity_enum AS ENUM ('info', 'warn', 'error')")

    # --- bronze.file_registry ---
    op.create_table(
        "file_registry",
        sa.Column("file_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", postgresql.ENUM("oilgasdata", "vesselschedule", "dailytruckout", "stockreport", name="source_name_enum", schema="bronze", create_type=False), nullable=False),
        sa.Column("source_page_url", sa.Text(), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=False),
        sa.Column("report_title", sa.Text(), nullable=True),
        sa.Column("report_period", sa.Date(), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM("active", "archived", "paused", name="file_status_enum", schema="bronze", create_type=False), nullable=False, server_default="active"),
        sa.Column("discovered_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("downloaded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        schema="bronze",
    )
    op.create_index("ix_bronze_file_registry_source_name", "file_registry", ["source_name"], schema="bronze")
    op.create_index("ix_bronze_file_registry_content_hash", "file_registry", ["content_hash"], schema="bronze")

    # --- bronze.ingest_run ---
    op.create_table(
        "ingest_run",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dag_id", sa.Text(), nullable=False),
        sa.Column("triggered_by", postgresql.ENUM("schedule", "manual", "backfill", name="triggered_by_enum", schema="bronze", create_type=False), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", postgresql.ENUM("success", "fail", "partial", name="run_status_enum", schema="bronze", create_type=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        schema="bronze",
    )

    # --- bronze.ingest_run_file ---
    op.create_table(
        "ingest_run_file",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.ingest_run.run_id"), primary_key=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), primary_key=True),
        sa.Column("parsed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("parser_version", sa.Text(), nullable=True),
        sa.Column("extraction_summary", postgresql.JSONB(), nullable=True),
        sa.Column("dq_summary", postgresql.JSONB(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("row_counts", postgresql.JSONB(), nullable=True),
        schema="bronze",
    )

    # --- bronze.rejects ---
    op.create_table(
        "rejects",
        sa.Column("reject_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("table_name", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="bronze",
    )

    # --- bronze.dq_rule ---
    op.create_table(
        "dq_rule",
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_name", sa.Text(), nullable=False),
        sa.Column("layer", sa.Text(), nullable=False),
        sa.Column("table_name", sa.Text(), nullable=False),
        sa.Column("rule_type", postgresql.ENUM("schema", "type", "range", "uniqueness", "referential", "completeness", "timeliness", name="dq_rule_type_enum", schema="bronze", create_type=False), nullable=False),
        sa.Column("rule_definition", postgresql.JSONB(), nullable=True),
        sa.Column("severity", postgresql.ENUM("info", "warn", "error", name="dq_severity_enum", schema="bronze", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        schema="bronze",
    )

    # --- bronze.dq_result ---
    op.create_table(
        "dq_result",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.ingest_run.run_id"), nullable=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("layer", sa.Text(), nullable=False),
        sa.Column("table_name", sa.Text(), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.dq_rule.rule_id"), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sample_failures", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="bronze",
    )

    # --- Bronze Oil & Gas tables ---
    op.create_table(
        "performance_highlights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("metric_name", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "refinery_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("refinery_name", sa.Text(), nullable=False),
        sa.Column("refinery_type", sa.Text(), nullable=True),
        sa.Column("capacity_bpsd", sa.Numeric(20, 4), nullable=True),
        sa.Column("utilization_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("product", sa.Text(), nullable=True),
        sa.Column("avg_supply_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_supply_unit", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "modular_refinery_output",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("refinery_name", sa.Text(), nullable=False),
        sa.Column("capacity_utilization_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("avg_ago_supply_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_ago_supply_unit", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "consumption_benchmark",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("benchmark_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "actual_consumption_truckout_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("volume_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "fuel_prices_city",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("indicative_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("min_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("max_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True, server_default="NGN/L"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "gas_infra",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("item_name", sa.Text(), nullable=True),
        sa.Column("metric_name", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "chart_series_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=False),
        sa.Column("chart_name", sa.Text(), nullable=False),
        sa.Column("series_name", sa.Text(), nullable=False),
        sa.Column("period_type", postgresql.ENUM("daily", "monthly", name="period_type_enum", schema="bronze", create_type=False), nullable=False),
        sa.Column("period_date", sa.Date(), nullable=True),
        sa.Column("period_month", sa.Date(), nullable=True),
        sa.Column("value", sa.Numeric(20, 4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )

    # --- Bronze Vessel Schedule ---
    op.create_table(
        "vessel_clearance_schedule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_period", sa.Date(), nullable=False),
        sa.Column("clearance_no", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("vessel_name", sa.Text(), nullable=True),
        sa.Column("initial_submission_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("final_submission_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("clearance_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("processing_days", sa.Numeric(10, 2), nullable=True),
        sa.Column("processing_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )

    # --- Bronze Daily Truckout (archived) ---
    op.create_table(
        "truckout_by_depot_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=True, server_default="PMS"),
        sa.Column("depot_name", sa.Text(), nullable=False),
        sa.Column("truck_count", sa.Integer(), nullable=True),
        sa.Column("volume_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "truckout_by_state_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=True, server_default="PMS"),
        sa.Column("state_name", sa.Text(), nullable=False),
        sa.Column("truck_count", sa.Integer(), nullable=True),
        sa.Column("volume_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "truckout_daily_totals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("total_trucks", sa.Integer(), nullable=True),
        sa.Column("total_volume_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )

    # --- Bronze Stock Report (archived) ---
    op.create_table(
        "stock_days_sufficiency_summary",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("land_stock_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("marine_stock_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("total_stock_less_dead_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("dead_stock_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("total_stock_incl_dead_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("land_days_sufficiency", sa.Numeric(10, 4), nullable=True),
        sa.Column("marine_days_sufficiency", sa.Numeric(10, 4), nullable=True),
        sa.Column("total_days_sufficiency", sa.Numeric(10, 4), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )
    op.create_table(
        "stock_ledger_by_product",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("product", sa.Text(), nullable=False),
        sa.Column("opening_stock_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("receipts_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("evacuation_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("book_closing_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("actual_closing_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("dead_stock_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("closing_operational_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("nat_avg_daily_consumption_litres", sa.Numeric(20, 4), nullable=True),
        sa.Column("days_sufficiency", sa.Numeric(10, 4), nullable=True),
        sa.Column("prev_days_sufficiency", sa.Numeric(10, 4), nullable=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bronze.file_registry.file_id"), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        schema="bronze",
    )

    # --- SILVER: dims and facts ---
    op.create_table(
        "dim_date",
        sa.Column("date_key", sa.Date(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=True),
        sa.Column("quarter", sa.Integer(), nullable=True),
        schema="silver",
    )
    op.create_table(
        "dim_product",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_code", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("unit_default", sa.Text(), nullable=True),
        schema="silver",
    )
    op.create_table(
        "dim_location",
        sa.Column("location_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_name", sa.Text(), nullable=False),
        sa.Column("location_type", sa.Text(), nullable=False),
        sa.Column("parent_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="silver",
    )
    op.create_table(
        "dim_facility",
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("facility_name", sa.Text(), nullable=False),
        sa.Column("facility_type", sa.Text(), nullable=False),
        schema="silver",
    )

    op.create_table(
        "fact_prices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date_month", sa.Date(), nullable=False),
        sa.Column("city_location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_location.location_id"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_product.product_id"), nullable=True),
        sa.Column("indicative", sa.Numeric(20, 4), nullable=True),
        sa.Column("min_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("max_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_price", sa.Numeric(20, 4), nullable=True),
        schema="silver",
    )
    op.create_table(
        "fact_stock",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_product.product_id"), nullable=True),
        sa.Column("land_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("marine_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("total_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("dead_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("days_sufficiency", sa.Numeric(10, 4), nullable=True),
        schema="silver",
    )
    op.create_table(
        "fact_truckout",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_location.location_id"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_product.product_id"), nullable=True),
        sa.Column("trucks", sa.Integer(), nullable=True),
        sa.Column("volume_litres", sa.Numeric(20, 4), nullable=True),
        schema="silver",
    )
    op.create_table(
        "fact_refinery_output",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("silver.dim_facility.facility_id"), nullable=True),
        sa.Column("utilization_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("output_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("output_unit", sa.Text(), nullable=True),
        schema="silver",
    )
    op.create_table(
        "fact_vessel_clearance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("clearance_no", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("vessel", sa.Text(), nullable=True),
        sa.Column("processing_days", sa.Numeric(10, 2), nullable=True),
        sa.Column("processing_hours", sa.Numeric(10, 2), nullable=True),
        schema="silver",
    )
    op.create_table(
        "fact_chart_series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chart_key", sa.Text(), nullable=False),
        sa.Column("period_date", sa.Date(), nullable=True),
        sa.Column("period_month", sa.Date(), nullable=True),
        sa.Column("series_name", sa.Text(), nullable=False),
        sa.Column("value", sa.Numeric(20, 4), nullable=False),
        schema="silver",
    )

    # --- GOLD: star schema ---
    op.create_table(
        "dim_date",
        sa.Column("date_key", sa.Date(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=True),
        sa.Column("quarter", sa.Integer(), nullable=True),
        schema="gold",
    )
    op.create_table(
        "dim_product",
        sa.Column("product_key", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_code", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("unit_default", sa.Text(), nullable=True),
        schema="gold",
    )
    op.create_table(
        "dim_location",
        sa.Column("location_key", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("location_name", sa.Text(), nullable=False),
        sa.Column("location_type", sa.Text(), nullable=False),
        schema="gold",
    )
    op.create_table(
        "dim_facility",
        sa.Column("facility_key", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("facility_name", sa.Text(), nullable=False),
        sa.Column("facility_type", sa.Text(), nullable=False),
        schema="gold",
    )
    op.create_table(
        "dim_report",
        sa.Column("report_key", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("report_title", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        schema="gold",
    )

    op.create_table(
        "fact_fuel_prices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date_month_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=False),
        sa.Column("location_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_location.location_key"), nullable=True),
        sa.Column("product_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_product.product_key"), nullable=True),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("indicative", sa.Numeric(20, 4), nullable=True),
        sa.Column("min_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("max_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_price", sa.Numeric(20, 4), nullable=True),
        schema="gold",
    )
    op.create_table(
        "fact_stock_sufficiency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=False),
        sa.Column("product_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_product.product_key"), nullable=True),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("land_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("marine_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("total_stock", sa.Numeric(20, 4), nullable=True),
        sa.Column("days_sufficiency", sa.Numeric(10, 4), nullable=True),
        schema="gold",
    )
    op.create_table(
        "fact_truckout",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=False),
        sa.Column("location_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_location.location_key"), nullable=True),
        sa.Column("product_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_product.product_key"), nullable=True),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("trucks", sa.Integer(), nullable=True),
        sa.Column("volume_litres", sa.Numeric(20, 4), nullable=True),
        schema="gold",
    )
    op.create_table(
        "fact_refinery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=False),
        sa.Column("facility_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_facility.facility_key"), nullable=True),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("utilization_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("output_value", sa.Numeric(20, 4), nullable=True),
        schema="gold",
    )
    op.create_table(
        "fact_vessel_clearance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("month_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=False),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("vessel", sa.Text(), nullable=True),
        sa.Column("processing_days", sa.Numeric(10, 2), nullable=True),
        sa.Column("processing_hours", sa.Numeric(10, 2), nullable=True),
        schema="gold",
    )
    op.create_table(
        "fact_series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=True),
        sa.Column("month_key", sa.Date(), sa.ForeignKey("gold.dim_date.date_key"), nullable=True),
        sa.Column("report_key", postgresql.UUID(as_uuid=True), sa.ForeignKey("gold.dim_report.report_key"), nullable=True),
        sa.Column("series_name", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("chart_name", sa.Text(), nullable=True),
        schema="gold",
    )

    # --- META ---
    op.create_table(
        "data_dictionary",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_type", sa.Text(), nullable=False),
        sa.Column("object_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data_type", sa.Text(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="meta",
    )
    op.create_table(
        "lineage_node",
        sa.Column("node_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("layer", sa.Text(), nullable=False),
        sa.Column("object_name", sa.Text(), nullable=False),
        sa.Column("object_type", sa.Text(), nullable=False),
        schema="meta",
    )
    op.create_table(
        "lineage_edge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meta.lineage_node.node_id"), nullable=False),
        sa.Column("to_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meta.lineage_node.node_id"), nullable=False),
        sa.Column("transform_name", sa.Text(), nullable=True),
        sa.Column("transform_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="meta",
    )
    op.create_table(
        "api_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("query_params", postgresql.JSONB(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="meta",
    )


def downgrade() -> None:
    op.drop_table("api_audit_log", schema="meta")
    op.drop_table("lineage_edge", schema="meta")
    op.drop_table("lineage_node", schema="meta")
    op.drop_table("data_dictionary", schema="meta")

    op.drop_table("fact_series", schema="gold")
    op.drop_table("fact_vessel_clearance", schema="gold")
    op.drop_table("fact_refinery", schema="gold")
    op.drop_table("fact_truckout", schema="gold")
    op.drop_table("fact_stock_sufficiency", schema="gold")
    op.drop_table("fact_fuel_prices", schema="gold")
    op.drop_table("dim_report", schema="gold")
    op.drop_table("dim_facility", schema="gold")
    op.drop_table("dim_location", schema="gold")
    op.drop_table("dim_product", schema="gold")
    op.drop_table("dim_date", schema="gold")

    op.drop_table("fact_chart_series", schema="silver")
    op.drop_table("fact_vessel_clearance", schema="silver")
    op.drop_table("fact_refinery_output", schema="silver")
    op.drop_table("fact_truckout", schema="silver")
    op.drop_table("fact_stock", schema="silver")
    op.drop_table("fact_prices", schema="silver")
    op.drop_table("dim_facility", schema="silver")
    op.drop_table("dim_location", schema="silver")
    op.drop_table("dim_product", schema="silver")
    op.drop_table("dim_date", schema="silver")

    op.drop_table("stock_ledger_by_product", schema="bronze")
    op.drop_table("stock_days_sufficiency_summary", schema="bronze")
    op.drop_table("truckout_daily_totals", schema="bronze")
    op.drop_table("truckout_by_state_daily", schema="bronze")
    op.drop_table("truckout_by_depot_daily", schema="bronze")
    op.drop_table("vessel_clearance_schedule", schema="bronze")
    op.drop_table("chart_series_values", schema="bronze")
    op.drop_table("gas_infra", schema="bronze")
    op.drop_table("fuel_prices_city", schema="bronze")
    op.drop_table("actual_consumption_truckout_daily", schema="bronze")
    op.drop_table("consumption_benchmark", schema="bronze")
    op.drop_table("modular_refinery_output", schema="bronze")
    op.drop_table("refinery_status", schema="bronze")
    op.drop_table("performance_highlights", schema="bronze")

    op.drop_table("dq_result", schema="bronze")
    op.drop_table("dq_rule", schema="bronze")
    op.drop_table("rejects", schema="bronze")
    op.drop_table("ingest_run_file", schema="bronze")
    op.drop_table("ingest_run", schema="bronze")
    op.drop_index("ix_bronze_file_registry_content_hash", "file_registry", schema="bronze")
    op.drop_index("ix_bronze_file_registry_source_name", "file_registry", schema="bronze")
    op.drop_table("file_registry", schema="bronze")

    op.execute("DROP TYPE IF EXISTS bronze.dq_severity_enum")
    op.execute("DROP TYPE IF EXISTS bronze.dq_rule_type_enum")
    op.execute("DROP TYPE IF EXISTS bronze.period_type_enum")
    op.execute("DROP TYPE IF EXISTS bronze.run_status_enum")
    op.execute("DROP TYPE IF EXISTS bronze.triggered_by_enum")
    op.execute("DROP TYPE IF EXISTS bronze.file_status_enum")
    op.execute("DROP TYPE IF EXISTS bronze.source_name_enum")

    op.execute("DROP SCHEMA IF EXISTS meta")
    op.execute("DROP SCHEMA IF EXISTS gold")
    op.execute("DROP SCHEMA IF EXISTS silver")
    op.execute("DROP SCHEMA IF EXISTS bronze")
