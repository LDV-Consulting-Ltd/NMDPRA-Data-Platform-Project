"""
Knowledge asset definitions for PetroGrid Knowledge Assets v0.1.
Only documents and endpoints confirmed by the mapping report / repository layout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ALLOWED_ASSET_TYPES: tuple[str, ...] = (
    "technical_documentation",
    "business_article",
    "product_analysis",
    "case_study",
    "openapi_spec",
    "mermaid_diagram",
    "data_dictionary",
    "lineage_metadata",
    "data_layer_metadata",
    "architecture_reference",
)

FORBIDDEN_ASSET_MARKERS: tuple[str, ...] = (
    "vector_index",
    "ai_summary",
    "tanna_connector",
    "invented_document",
    "generated_png",
    "generated_svg",
)

PREVIEW_MAX_CHARS = 240
DIAGRAMS_TS_RELATIVE = "apps/web/lib/diagrams.ts"
MANIFEST_SOURCE = "apps/api/app/product_manifest.py"


@dataclass(frozen=True)
class FileAssetDefinition:
    asset_id: str
    asset_type: str
    title: str
    description: str
    source_path: str
    related_data_products: tuple[str, ...]
    related_entities: tuple[str, ...]
    related_relationships: tuple[str, ...]
    limitations: str = ""


@dataclass(frozen=True)
class EndpointAssetDefinition:
    asset_id: str
    asset_type: str
    title: str
    description: str
    source_endpoint: str
    source_path: Optional[str]
    related_data_products: tuple[str, ...]
    related_entities: tuple[str, ...]
    related_relationships: tuple[str, ...]
    limitations: str = ""


@dataclass(frozen=True)
class DiagramAssetDefinition:
    asset_id: str
    asset_type: str
    title: str
    description: str
    export_name: str
    related_data_products: tuple[str, ...]
    related_entities: tuple[str, ...]
    related_relationships: tuple[str, ...]
    limitations: str = ""


FILE_ASSETS: tuple[FileAssetDefinition, ...] = (
    FileAssetDefinition(
        asset_id="knowledge.readme",
        asset_type="technical_documentation",
        title="README.md",
        description="Platform setup, architecture overview, and API documentation index.",
        source_path="README.md",
        related_data_products=("petrogrid",),
        related_entities=("type.api_product",),
        related_relationships=("documented_by.knowledge.readme.product.petrogrid",),
    ),
    FileAssetDefinition(
        asset_id="knowledge.product_article_business",
        asset_type="business_article",
        title="PRODUCT_ARTICLE_BUSINESS.md",
        description="Business-facing product article for PetroGrid / PetroSight positioning.",
        source_path="PRODUCT_ARTICLE_BUSINESS.md",
        related_data_products=("petrogrid",),
        related_entities=("type.api_product",),
        related_relationships=(),
        limitations="Business narrative only; not operational telemetry.",
    ),
    FileAssetDefinition(
        asset_id="knowledge.product_analysis",
        asset_type="product_analysis",
        title="PRODUCT_ANALYSIS.md",
        description="Product analysis document for platform capabilities and gaps.",
        source_path="PRODUCT_ANALYSIS.md",
        related_data_products=("petrogrid",),
        related_entities=("type.api_product",),
        related_relationships=(),
    ),
    FileAssetDefinition(
        asset_id="knowledge.case_study_nmdpra",
        asset_type="case_study",
        title="CASE_STUDY_NMDPRA.md",
        description="NMDPRA downstream regulatory intelligence case study.",
        source_path="CASE_STUDY_NMDPRA.md",
        related_data_products=("petrogrid",),
        related_entities=("type.report", "type.source_file"),
        related_relationships=(),
    ),
)

ENDPOINT_ASSETS: tuple[EndpointAssetDefinition, ...] = (
    EndpointAssetDefinition(
        asset_id="knowledge.openapi",
        asset_type="openapi_spec",
        title="OpenAPI specification",
        description="Machine-readable API contract served at runtime by FastAPI.",
        source_endpoint="/openapi.json",
        source_path=None,
        related_data_products=("api.reports",),
        related_entities=("type.api_product",),
        related_relationships=("documented_by.knowledge.openapi.api.reports",),
        limitations="Served at request time; not a static repository file.",
    ),
    EndpointAssetDefinition(
        asset_id="knowledge.governance.data_dictionary",
        asset_type="data_dictionary",
        title="Governance data dictionary",
        description="Governance metadata dictionary entries from meta.data_dictionary.",
        source_endpoint="/v1/governance/metadata/dictionary",
        source_path=None,
        related_data_products=("api.coverage",),
        related_entities=("type.data_layer_table",),
        related_relationships=(),
        limitations="meta.data_dictionary may be empty until populated by pipeline publish step.",
    ),
    EndpointAssetDefinition(
        asset_id="knowledge.governance.lineage",
        asset_type="lineage_metadata",
        title="Governance lineage metadata",
        description="Lineage nodes and edges from meta.lineage_node and meta.lineage_edge.",
        source_endpoint="/v1/governance/lineage/nodes",
        source_path=None,
        related_data_products=("api.data_layers",),
        related_entities=("type.data_layer_table",),
        related_relationships=(),
        limitations="Lineage edges may be empty; nodes seeded minimally by pipeline publish step.",
    ),
    EndpointAssetDefinition(
        asset_id="knowledge.data_layers.metadata",
        asset_type="data_layer_metadata",
        title="Data layer table metadata",
        description="Bronze, silver, and gold table introspection with row counts.",
        source_endpoint="/v1/data-layers/tables",
        source_path=None,
        related_data_products=("api.data_layers",),
        related_entities=("type.data_layer_table",),
        related_relationships=(),
        limitations="Silver schema exists but is not persisted by pipeline.",
    ),
)

DIAGRAM_ASSETS: tuple[DiagramAssetDefinition, ...] = (
    DiagramAssetDefinition(
        asset_id="knowledge.diagram.data_architecture",
        asset_type="architecture_reference",
        title="Data architecture diagram",
        description="Mermaid data architecture flowchart used by the Metadata UI.",
        export_name="DATA_ARCHITECTURE_MMD",
        related_data_products=("petrogrid",),
        related_entities=("type.ingestion_run", "type.data_layer_table"),
        related_relationships=(),
    ),
    DiagramAssetDefinition(
        asset_id="knowledge.diagram.lineage",
        asset_type="mermaid_diagram",
        title="Lineage diagram",
        description="Mermaid lineage flowchart across bronze, silver, and gold layers.",
        export_name="LINEAGE_MMD",
        related_data_products=("api.data_layers",),
        related_entities=("type.data_layer_table",),
        related_relationships=(),
    ),
    DiagramAssetDefinition(
        asset_id="knowledge.diagram.data_model",
        asset_type="mermaid_diagram",
        title="Gold data model diagram",
        description="Mermaid ER diagram for gold dimensions and facts.",
        export_name="DATA_MODEL_MMD",
        related_data_products=("gold.dim_product", "gold.fact_fuel_prices"),
        related_entities=("type.product", "type.location", "type.facility"),
        related_relationships=(),
        limitations="Gold schema reference; silver not persisted.",
    ),
)

# Generated diagram outputs are not claimed unless present on disk.
GENERATED_DIAGRAM_GLOBS: tuple[str, ...] = (
    "docs/diagrams/*.png",
    "docs/diagrams/*.svg",
    "docs/diagrams/*.mmd",
)
