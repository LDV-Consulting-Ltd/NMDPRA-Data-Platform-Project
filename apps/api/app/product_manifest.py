"""
PetroGrid product manifest v0.1 — capability surface for internal services and future Tanna connector.
Derived from repository facts; does not assert unimplemented features.
"""
from __future__ import annotations

from datetime import datetime, timezone


def build_product_manifest(*, api_title: str) -> dict:
    """Return the PetroGrid manifest payload (v0.1)."""
    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "legacy_branding": "PetroSight / NMDPRA Data Platform",
        "product_category": "Downstream Petroleum Intelligence",
        "owner": "LDV",
        "api_title": api_title,
        "available_api_groups": [
            {
                "id": "health",
                "label": "Health",
                "base_path": "/health",
                "auth": "public",
            },
            {
                "id": "product",
                "label": "Product manifest",
                "base_path": "/v1/product",
                "auth": "public",
            },
            {
                "id": "reports_coverage",
                "label": "Reports & coverage",
                "base_path": "/v1/reports",
                "auth": "public",
            },
            {
                "id": "oil_gas",
                "label": "Oil & gas business APIs",
                "base_path": "/v1",
                "auth": "public",
                "endpoints": [
                    "/v1/highlights",
                    "/v1/refineries/status",
                    "/v1/refineries/modular",
                    "/v1/consumption/benchmarks",
                    "/v1/consumption/truckout",
                    "/v1/prices/fuel",
                    "/v1/gas/infra",
                    "/v1/charts/series",
                ],
            },
            {
                "id": "vessels",
                "label": "Vessel clearance",
                "base_path": "/v1/vessels",
                "auth": "public",
            },
            {
                "id": "archive",
                "label": "Archived feeds",
                "base_path": "/v1/archive",
                "auth": "public",
            },
            {
                "id": "governance",
                "label": "Governance",
                "base_path": "/v1/governance",
                "auth": "public",
                "endpoints": [
                    "/v1/governance/dq/rules",
                    "/v1/governance/dq/results",
                    "/v1/governance/metadata/dictionary",
                    "/v1/governance/lineage/nodes",
                    "/v1/governance/lineage/edges",
                    "/v1/governance/audit/api",
                    "/v1/governance/health/ingestion",
                ],
            },
            {
                "id": "pipeline",
                "label": "Pipeline status (sanitized)",
                "base_path": "/v1/pipeline",
                "auth": "public",
            },
            {
                "id": "data_layers",
                "label": "Data layer introspection",
                "base_path": "/v1/data-layers",
                "auth": "public",
            },
            {
                "id": "admin",
                "label": "Admin pipeline operations",
                "base_path": "/v1/admin",
                "auth": "X-Admin-Token",
            },
        ],
        "available_data_layers": [
            {
                "layer": "bronze",
                "status": "implemented",
                "description": "Source-shaped ingestion tables; primary read surface for business APIs.",
            },
            {
                "layer": "silver",
                "status": "not_implemented",
                "description": "Schema defined in migrations; pipeline builds silver in-memory only (not persisted).",
            },
            {
                "layer": "gold",
                "status": "partial",
                "description": "Star-schema marts populated by pipeline; introspection via /v1/data-layers (no dedicated gold read APIs).",
            },
            {
                "layer": "meta",
                "status": "partial",
                "description": "Governance catalog tables (data_dictionary, lineage_node, lineage_edge, api_audit_log).",
            },
        ],
        "supported_domains": [
            "source_reports_and_coverage",
            "performance_highlights",
            "fuel_prices_by_city",
            "refinery_status_and_modular_output",
            "consumption_benchmarks_and_truckout",
            "gas_and_infrastructure_metrics",
            "chart_series",
            "vessel_clearance_schedule",
            "archived_truckout_and_stock",
            "data_quality_rules_and_results",
            "metadata_dictionary",
            "lineage_nodes_and_edges",
            "api_audit_log",
            "ingestion_and_pipeline_health",
            "warehouse_layer_introspection",
        ],
        "supported_capabilities": [
            {
                "id": "api_liveness",
                "status": "implemented",
                "evidence": "GET /health",
            },
            {
                "id": "pipeline_status",
                "status": "implemented",
                "evidence": "GET /v1/pipeline/status, GET /v1/pipeline/history",
            },
            {
                "id": "governance_health",
                "status": "implemented",
                "evidence": "GET /v1/governance/health/ingestion",
            },
            {
                "id": "business_apis",
                "status": "implemented",
                "evidence": "GET /v1/reports, /v1/coverage, /v1/highlights, /v1/refineries/*, /v1/prices/*, /v1/gas/*, /v1/charts/*, /v1/vessels/*, /v1/archive/*",
            },
            {
                "id": "bronze_data_products",
                "status": "implemented",
                "evidence": "Business routers query bronze.* tables per apps/api/app/routers/",
            },
            {
                "id": "gold_data_layer_introspection",
                "status": "partial",
                "evidence": "GET /v1/data-layers/tables?layer=gold",
            },
            {
                "id": "data_dictionary_endpoint",
                "status": "partial",
                "evidence": "GET /v1/governance/metadata/dictionary (meta.data_dictionary may be empty until populated)",
            },
            {
                "id": "lineage_nodes_edges_endpoint",
                "status": "partial",
                "evidence": "GET /v1/governance/lineage/nodes, GET /v1/governance/lineage/edges (edges may be empty in DB)",
            },
            {
                "id": "audit_log_endpoint",
                "status": "implemented",
                "evidence": "GET /v1/governance/audit/api",
            },
            {
                "id": "ingestion_health_endpoint",
                "status": "implemented",
                "evidence": "GET /v1/governance/health/ingestion",
            },
            {
                "id": "knowledge_assets",
                "status": "partial",
                "evidence": "OpenAPI at /openapi.json; README.md, PRODUCT_ARTICLE_BUSINESS.md, PRODUCT_ANALYSIS.md, CASE_STUDY_NMDPRA.md; Mermaid in apps/web/lib/diagrams.ts",
            },
            {
                "id": "admin_pipeline_health",
                "status": "implemented",
                "evidence": "GET /v1/admin/pipeline/health (requires X-Admin-Token)",
            },
            {
                "id": "rule_based_signals",
                "status": "implemented",
                "evidence": "GET /v1/product/signals (read-only rule evaluation from pipeline, governance, coverage, and bronze table evidence)",
            },
            {
                "id": "rule_based_patterns",
                "status": "implemented",
                "evidence": "GET /v1/product/patterns (read-only clustering of PetroGrid Signals v0.1)",
            },
            {
                "id": "rule_based_illuminations",
                "status": "implemented",
                "evidence": "GET /v1/product/illuminations (read-only contextual interpretation from Signals and Patterns v0.1)",
            },
            {
                "id": "rule_based_decision_products",
                "status": "implemented",
                "evidence": "GET /v1/product/decision-products (read-only decision-support objects from Signals, Patterns, and Illuminations v0.1)",
            },
            {
                "id": "relationship_model",
                "status": "implemented",
                "evidence": "GET /v1/product/relationships (migration FKs, data product registry, pipeline mappings, lineage edges)",
            },
            {
                "id": "relationship_surface",
                "status": "implemented",
                "evidence": "GET /v1/product/relationships (evidence-backed relationship groups: data products, APIs, tables, entities, lineage)",
            },
            {
                "id": "entity_surface",
                "status": "implemented",
                "evidence": "GET /v1/product/entities (migration schema, data product registry, Pydantic schemas, safe read-only instance queries)",
            },
            {
                "id": "knowledge_asset_surface",
                "status": "implemented",
                "evidence": "GET /v1/product/knowledge-assets (README, product docs, OpenAPI, Mermaid diagrams, governance metadata endpoints)",
            },
        ],
        "unsupported_capabilities": [
            {
                "id": "signal_persistence_and_advanced_signal_engine",
                "status": "not_implemented",
                "reason": "v0.1 exposes computed rule-based signals only; no signal tables, ML, market intelligence, or AI-generated signals.",
            },
            {
                "id": "pattern_persistence_and_advanced_pattern_engine",
                "status": "not_implemented",
                "reason": "v0.1 exposes computed rule-based patterns from signals only; no pattern tables, ML, market movement, or AI-generated patterns.",
            },
            {
                "id": "illumination_persistence_and_advanced_illumination_engine",
                "status": "not_implemented",
                "reason": "v0.1 exposes computed rule-based illuminations from signals/patterns only; no illumination tables, AI narratives, or forecasting.",
            },
            {
                "id": "decision_product_workflow_and_automation",
                "status": "not_implemented",
                "reason": "v0.1 exposes computed rule-based decision-support objects only; no approval workflows, task management, AI recommendations, or forecasting.",
            },
            {
                "id": "tanna_connector",
                "status": "not_implemented",
                "reason": "No Tanna connector module or sync endpoints in this repository.",
            },
        ],
        "current_limitations": [
            "Signals v0.1 are computed at request time with status 'new' only; no acknowledgement workflow or persistence.",
            "Patterns v0.1 cluster co-occurring signals at request time; not historical recurrence across time windows.",
            "Knowledge asset surface v0.1 catalogs existing docs and metadata endpoints only; no vector search or AI summaries.",
            "Entity surface v0.1 returns type summaries plus capped instance queries; no invented business objects.",
            "Relationship model v0.1 emits evidence-backed static and lineage links only; no graph analytics or inferred causality.",
            "Decision products v0.1 are draft decision-support objects requiring human review; not automated approvals.",
            "Illuminations v0.1 provide conservative operational context from signals/patterns; not automated decisions.",
            "Patterns are clustered signal structures only — not decision products.",
            "Signals are attention indicators only — not decision products.",
            "Business APIs read bronze tables; gold marts are built but not exposed as primary read APIs.",
            "Silver layer schema exists but is not persisted by the ingestion pipeline.",
            "Pipeline metadata publish step seeds minimal lineage nodes; lineage edges and data_dictionary rows are often empty.",
            "DQ pipeline records rule outcomes in simplified form; not full row-level validation.",
            "Oil & gas parse step inserts a subset of parser outputs (e.g. highlights and chart series); not all parsed bronze entities are loaded.",
            "Admin pipeline routes require ADMIN_RUN_TOKEN (X-Admin-Token header).",
            "Product manifest describes PetroGrid; UI may still show PetroSight / NMDPRA legacy branding.",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
