"""
PetroGrid Relationships v0.1 — read-only, evidence-backed relationship surface.
No persistence, no graph database, no invented links.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.data_product_registry import build_data_product_registry
from app.product_entities.service import build_entities
from app.product_relationships.rules import (
    ALLOWED_RELATIONSHIP_TYPES,
    BRONZE_INGEST_FILE_REFERENCES,
    BRONZE_SOURCED_FROM_FILE_REGISTRY,
    CONFIDENCE,
    CONFIDENCE_BANDS,
    ENTITIES_SOURCE,
    FORBIDDEN_RELATIONSHIP_TYPES,
    GOLD_DERIVED_FROM_BRONZE,
    GOLD_FACT_DIMENSION_FKS,
    KNOWLEDGE_ASSET_TO_DATA_PRODUCT,
    KNOWLEDGE_ASSET_TO_ENTITY,
    MIN_CONFIDENCE,
    MIGRATION_SOURCE,
    PIPELINE_SOURCE,
    REGISTRY_SOURCE,
    RELATIONSHIP_GROUPS,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _relationship(
    *,
    relationship_id: str,
    relationship_type: str,
    source_object_type: str,
    source_object_id: str,
    target_object_type: str,
    target_object_id: str,
    description: str,
    evidence: dict[str, Any],
    confidence: float,
    limitations: str,
    status: str = "active",
    group: str,
) -> Optional[dict[str, Any]]:
    if confidence < MIN_CONFIDENCE:
        return None
    payload = {
        "relationship_id": relationship_id,
        "relationship_type": relationship_type,
        "source_object_type": source_object_type,
        "source_object_id": source_object_id,
        "target_object_type": target_object_type,
        "target_object_id": target_object_id,
        "description": description,
        "evidence": {**evidence, "relationship_group": group},
        "confidence": round(confidence, 2),
        "status": status,
        "limitations": limitations,
    }
    return payload


def _append(items: list[dict[str, Any]], rel: Optional[dict[str, Any]]) -> None:
    if rel is not None:
        items.append(rel)


def _parse_backing_tables(backing_table: Optional[str]) -> list[str]:
    if not backing_table:
        return []
    return [part.strip() for part in backing_table.split(";") if part.strip()]


def _parse_api_routes(backing_api: Optional[str]) -> list[str]:
    if not backing_api:
        return []
    routes: list[str] = []
    for part in backing_api.split(";"):
        part = part.strip()
        if part.upper().startswith("GET "):
            route = part[4:].strip().split("?")[0]
            if route:
                routes.append(route)
    return routes


def _migration_fk_evidence(*, fk_column: str, fk_target: str) -> dict[str, Any]:
    return {
        "evidence_type": "foreign_key_definition",
        "migration_file": MIGRATION_SOURCE,
        "fk_column": fk_column,
        "fk_target": fk_target,
        "confidence_band": CONFIDENCE_BANDS["foreign_key"],
    }


def _build_gold_fact_dimension_relationships() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for rel in GOLD_FACT_DIMENSION_FKS:
        _append(
            items,
            _relationship(
                relationship_id=rel.relationship_id,
                relationship_type=rel.relationship_type,
                source_object_type=rel.source_object_type,
                source_object_id=rel.source_object_id,
                target_object_type=rel.target_object_type,
                target_object_id=rel.target_object_id,
                description=rel.description,
                evidence=_migration_fk_evidence(
                    fk_column=rel.fk_column,
                    fk_target=rel.fk_target,
                ),
                confidence=CONFIDENCE["foreign_key"],
                limitations="Gold fact-to-dimension FK from migration schema.",
                group="gold_fact_to_gold_dimension",
            ),
        )
    return items


def _build_bronze_sourced_from_relationships() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for table, fk_column in BRONZE_SOURCED_FROM_FILE_REGISTRY:
        rel_id = f"sourced_from.{table}.bronze.file_registry"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type="sourced_from",
                source_object_type="table",
                source_object_id=table,
                target_object_type="source_file",
                target_object_id="bronze.file_registry",
                description=f"{table} rows reference NMDPRA source files via {fk_column}.",
                evidence={
                    "evidence_type": "source_file_id_reference",
                    "migration_file": MIGRATION_SOURCE,
                    "fk_column": fk_column,
                    "fk_target": "bronze.file_registry.file_id",
                    "confidence_band": CONFIDENCE_BANDS["source_file_id"],
                },
                confidence=CONFIDENCE["source_file_id"],
                limitations="Row-level source_file_id linkage; instances not enumerated in v0.1.",
                group="source_file_to_bronze_table",
            ),
        )
    return items


def _build_bronze_ingest_references() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for table, fk_column, target in BRONZE_INGEST_FILE_REFERENCES:
        rel_id = f"references.{table}.{target}"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type="references",
                source_object_type="table",
                source_object_id=table,
                target_object_type="source_file",
                target_object_id=target,
                description=f"{table}.{fk_column} references report registry entries.",
                evidence={
                    "evidence_type": "foreign_key_definition",
                    "migration_file": MIGRATION_SOURCE,
                    "fk_column": fk_column,
                    "fk_target": f"{target}.file_id",
                    "confidence_band": CONFIDENCE_BANDS["foreign_key"],
                },
                confidence=CONFIDENCE["foreign_key"],
                limitations="Ingest and DQ tables reference file_registry rows.",
                group="report_to_source_file",
            ),
        )
    return items


def _build_gold_derived_from_bronze() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for gold_table, bronze_table in GOLD_DERIVED_FROM_BRONZE:
        rel_id = f"derived_from.{gold_table}.{bronze_table}"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type="derived_from",
                source_object_type="table",
                source_object_id=gold_table,
                target_object_type="table",
                target_object_id=bronze_table,
                description=f"{gold_table} is built from {bronze_table} in run_silver_gold.",
                evidence={
                    "evidence_type": "pipeline_derived_mapping",
                    "pipeline_function": PIPELINE_SOURCE,
                    "gold_table": gold_table,
                    "bronze_table": bronze_table,
                    "confidence_band": CONFIDENCE_BANDS["lineage_edge"],
                },
                confidence=CONFIDENCE["pipeline_derived"],
                limitations="Pipeline mapping evidence; not a database FK.",
                group="bronze_table_to_gold_table",
            ),
        )
    return items


def _build_data_product_relationships() -> list[dict[str, Any]]:
    registry = build_data_product_registry()
    items: list[dict[str, Any]] = []
    seen_endpoint_tables: set[tuple[str, str]] = set()

    for group_name, products in registry["groups"].items():
        for product in products:
            product_id = product["product_id"]
            backing_api = product.get("backing_api")
            tables = _parse_backing_tables(product.get("backing_table"))
            routes = _parse_api_routes(backing_api)

            for route in routes:
                rel_id = f"references.{product_id}.{route.strip('/').replace('/', '_')}"
                _append(
                    items,
                    _relationship(
                        relationship_id=rel_id,
                        relationship_type="references",
                        source_object_type="data_product",
                        source_object_id=product_id,
                        target_object_type="api_endpoint",
                        target_object_id=route,
                        description=f"Data product {product_id} is served by API endpoint {route}.",
                        evidence={
                            "evidence_type": "data_product_registry",
                            "registry_source": REGISTRY_SOURCE,
                            "registry_group": group_name,
                            "backing_api": backing_api,
                            "confidence_band": CONFIDENCE_BANDS["documentation"],
                        },
                        confidence=CONFIDENCE["documentation"],
                        limitations="Registry-defined API route; not a runtime contract test.",
                        group="data_product_to_api_endpoint",
                    ),
                )

            for route in routes:
                for table in tables:
                    pair = (route, table)
                    if pair in seen_endpoint_tables:
                        continue
                    seen_endpoint_tables.add(pair)
                    endpoint_id = route.strip("/").replace("/", "_")
                    table_id = table.replace(".", "_")
                    rel_id = f"references.{endpoint_id}.{table_id}"
                    _append(
                        items,
                        _relationship(
                            relationship_id=rel_id,
                            relationship_type="references",
                            source_object_type="api_endpoint",
                            source_object_id=route,
                            target_object_type="table",
                            target_object_id=table,
                            description=f"API endpoint {route} reads backing table {table}.",
                            evidence={
                                "evidence_type": "data_product_registry",
                                "registry_source": REGISTRY_SOURCE,
                                "backing_api": route,
                                "backing_table": table,
                                "confidence_band": CONFIDENCE_BANDS["documentation"],
                            },
                            confidence=CONFIDENCE["documentation"],
                            limitations="Business APIs read bronze tables per mapping report.",
                            group="api_endpoint_to_bronze_table",
                        ),
                    )

            for table in tables:
                rel_id = f"represented_by.{product_id}.{table}"
                _append(
                    items,
                    _relationship(
                        relationship_id=rel_id,
                        relationship_type="represented_by",
                        source_object_type="data_product",
                        source_object_id=product_id,
                        target_object_type="table",
                        target_object_id=table,
                        description=f"Data product {product_id} is represented by backing table {table}.",
                        evidence={
                            "evidence_type": "data_product_registry",
                            "registry_source": REGISTRY_SOURCE,
                            "registry_group": group_name,
                            "backing_table": table,
                            "backing_api": backing_api,
                            "confidence_band": CONFIDENCE_BANDS["documentation"],
                        },
                        confidence=CONFIDENCE["documentation"],
                        limitations="Catalog representation link from data product registry.",
                        group="api_endpoint_to_bronze_table",
                    ),
                )

            if product.get("backing_table") == "bronze.file_registry" or product_id in (
                "api.reports",
                "api.coverage",
            ):
                rel_id = f"contains.{product_id}.bronze.file_registry"
                _append(
                    items,
                    _relationship(
                        relationship_id=rel_id,
                        relationship_type="contains",
                        source_object_type="data_product",
                        source_object_id=product_id,
                        target_object_type="source_file",
                        target_object_id="bronze.file_registry",
                        description=f"Data product {product_id} catalogs NMDPRA source file registry entries.",
                        evidence={
                            "evidence_type": "data_product_registry",
                            "registry_source": REGISTRY_SOURCE,
                            "backing_table": "bronze.file_registry",
                            "backing_api": backing_api,
                            "confidence_band": CONFIDENCE_BANDS["documentation"],
                        },
                        confidence=CONFIDENCE["documentation"],
                        limitations="Catalog link; individual file instances exposed via entities endpoint.",
                        group="report_to_source_file",
                    ),
                )

    return items


def _build_knowledge_asset_relationships() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for asset_id, product_id in KNOWLEDGE_ASSET_TO_DATA_PRODUCT:
        rel_id = f"documented_by.{asset_id}.{product_id}"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type="documented_by",
                source_object_type="knowledge_asset",
                source_object_id=asset_id,
                target_object_type="data_product",
                target_object_id=product_id,
                description=f"Knowledge asset {asset_id} documents data product {product_id}.",
                evidence={
                    "evidence_type": "knowledge_asset_manifest",
                    "manifest_capability": "knowledge_assets",
                    "asset_id": asset_id,
                    "target_product_id": product_id,
                    "confidence_band": CONFIDENCE_BANDS["documentation"],
                },
                confidence=CONFIDENCE["documentation"],
                limitations="Manifest-documented knowledge asset link only.",
                group="knowledge_asset_to_data_product",
            ),
        )

    for asset_id, entity_type, entity_id in KNOWLEDGE_ASSET_TO_ENTITY:
        rel_id = f"documented_by.{asset_id}.{entity_type}.{entity_id}"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type="documented_by",
                source_object_type="knowledge_asset",
                source_object_id=asset_id,
                target_object_type=entity_type,
                target_object_id=entity_id,
                description=f"Knowledge asset {asset_id} documents {entity_type} {entity_id}.",
                evidence={
                    "evidence_type": "knowledge_asset_manifest",
                    "manifest_capability": "knowledge_assets",
                    "asset_id": asset_id,
                    "target_entity_type": entity_type,
                    "target_entity_id": entity_id,
                    "confidence_band": CONFIDENCE_BANDS["documentation"],
                },
                confidence=CONFIDENCE["documentation"],
                limitations="Manifest-documented knowledge asset link only.",
                group="knowledge_asset_to_data_product",
            ),
        )

    return items


def _build_report_source_file_relationship() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    _append(
        items,
        _relationship(
            relationship_id="contains.bronze.file_registry.report_entry",
            relationship_type="contains",
            source_object_type="table",
            source_object_id="bronze.file_registry",
            target_object_type="report",
            target_object_id="bronze.file_registry.file_id",
            description="file_registry rows are NMDPRA source report catalog entries.",
            evidence={
                "evidence_type": "migration_metadata",
                "migration_file": MIGRATION_SOURCE,
                "table": "bronze.file_registry",
                "primary_key": "file_id",
                "confidence_band": CONFIDENCE_BANDS["foreign_key"],
            },
            confidence=CONFIDENCE["foreign_key"],
            limitations="Schema-level report catalog; instance rows via entities endpoint.",
            group="report_to_source_file",
        ),
    )
    return items


def _build_entity_to_data_product_relationships(db) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        entities, _ = build_entities(db)
    except (ProgrammingError, SQLAlchemyError):
        return items

    registry = build_data_product_registry()
    product_by_table: dict[str, list[str]] = {}
    for group in registry["groups"].values():
        for product in group:
            for table in _parse_backing_tables(product.get("backing_table")):
                product_by_table.setdefault(table, []).append(product["product_id"])

    for entity in entities:
        if entity.get("status") == "summary":
            continue

        if entity["entity_id"].startswith("api_product."):
            product_id = entity["entity_id"].replace("api_product.", "", 1)
            rel_id = f"belongs_to.{entity['entity_id']}.{product_id}"
            _append(
                items,
                _relationship(
                    relationship_id=rel_id,
                    relationship_type="belongs_to",
                    source_object_type="entity",
                    source_object_id=entity["entity_id"],
                    target_object_type="data_product",
                    target_object_id=product_id,
                    description=f"API product entity maps to registry data product {product_id}.",
                    evidence={
                        "evidence_type": "entity_surface",
                        "entities_source": ENTITIES_SOURCE,
                        "entity_id": entity["entity_id"],
                        "confidence_band": CONFIDENCE_BANDS["documentation"],
                    },
                    confidence=CONFIDENCE["documentation"],
                    limitations="Entity catalog entry mirrors data product registry id.",
                    group="entity_to_data_product",
                ),
            )
            continue

        backing_table = entity.get("backing_table")
        if not backing_table:
            continue
        for table in _parse_backing_tables(backing_table):
            for product_id in product_by_table.get(table, []):
                rel_id = f"belongs_to.{entity['entity_id']}.{product_id}"
                _append(
                    items,
                    _relationship(
                        relationship_id=rel_id,
                        relationship_type="belongs_to",
                        source_object_type="entity",
                        source_object_id=entity["entity_id"],
                        target_object_type="data_product",
                        target_object_id=product_id,
                        description=(
                            f"Entity {entity['entity_id']} belongs to data product {product_id} "
                            f"via backing table {table}."
                        ),
                        evidence={
                            "evidence_type": "entity_surface",
                            "entities_source": ENTITIES_SOURCE,
                            "entity_id": entity["entity_id"],
                            "backing_table": table,
                            "target_product_id": product_id,
                            "confidence_band": CONFIDENCE_BANDS["source_file_id"],
                        },
                        confidence=CONFIDENCE["entity_registry"],
                        limitations="Derived from entities v0.1 and data product registry overlap.",
                        group="entity_to_data_product",
                    ),
                )

    return items


def _fetch_lineage_nodes(db) -> list[dict[str, Any]]:
    try:
        rows = db.execute(
            text(
                "SELECT node_id, layer, object_name, object_type "
                "FROM meta.lineage_node ORDER BY layer, object_name"
            )
        ).fetchall()
        return [
            {
                "node_id": str(row[0]),
                "layer": row[1],
                "object_name": row[2],
                "object_type": row[3],
            }
            for row in rows
        ]
    except (ProgrammingError, SQLAlchemyError):
        return []


def _fetch_lineage_edges(db) -> list[dict[str, Any]]:
    try:
        rows = db.execute(
            text("""
                SELECT e.id, e.from_node_id, e.to_node_id, e.transform_name, e.transform_version,
                       n_from.layer AS from_layer, n_from.object_name AS from_name,
                       n_to.layer AS to_layer, n_to.object_name AS to_name
                FROM meta.lineage_edge e
                JOIN meta.lineage_node n_from ON n_from.node_id = e.from_node_id
                JOIN meta.lineage_node n_to ON n_to.node_id = e.to_node_id
                ORDER BY e.created_at DESC
            """)
        ).fetchall()
        return [
            {
                "edge_id": str(row[0]),
                "from_node_id": str(row[1]),
                "to_node_id": str(row[2]),
                "transform_name": row[3],
                "transform_version": row[4],
                "from_layer": row[5],
                "from_name": row[6],
                "to_layer": row[7],
                "to_name": row[8],
            }
            for row in rows
        ]
    except (ProgrammingError, SQLAlchemyError):
        return []


def _lineage_edge_relationship_type(transform_name: Optional[str]) -> str:
    if transform_name and "load" in transform_name.lower():
        return "loaded_into"
    if transform_name and "produce" in transform_name.lower():
        return "produces"
    return "derived_from"


def _build_lineage_edge_relationships(db) -> list[dict[str, Any]]:
    edges = _fetch_lineage_edges(db)
    items: list[dict[str, Any]] = []
    for edge in edges:
        rel_type = _lineage_edge_relationship_type(edge.get("transform_name"))
        rel_id = f"{rel_type}.lineage.{edge['edge_id']}"
        _append(
            items,
            _relationship(
                relationship_id=rel_id,
                relationship_type=rel_type,
                source_object_type="lineage_node",
                source_object_id=edge["from_node_id"],
                target_object_type="lineage_node",
                target_object_id=edge["to_node_id"],
                description=(
                    f"Lineage edge from {edge['from_layer']}.{edge['from_name']} "
                    f"to {edge['to_layer']}.{edge['to_name']}."
                ),
                evidence={
                    "evidence_type": "lineage_edge_record",
                    "edge_id": edge["edge_id"],
                    "from_node_id": edge["from_node_id"],
                    "to_node_id": edge["to_node_id"],
                    "transform_name": edge.get("transform_name"),
                    "transform_version": edge.get("transform_version"),
                    "source_endpoint": "/v1/governance/lineage/edges",
                    "confidence_band": CONFIDENCE_BANDS["lineage_edge"],
                },
                confidence=CONFIDENCE["lineage_edge"],
                limitations="Governance lineage edge record from meta.lineage_edge.",
                group="lineage_node_to_lineage_node",
            ),
        )
    return items


def _group_relationships(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {key: [] for key in RELATIONSHIP_GROUPS}
    for item in items:
        group = item.get("evidence", {}).get("relationship_group")
        if group in groups:
            groups[group].append(item)
    return groups


def build_static_relationships(db=None) -> list[dict[str, Any]]:
    """Relationships from migration, registry, pipeline, entities, and knowledge assets."""
    items: list[dict[str, Any]] = []
    items.extend(_build_gold_fact_dimension_relationships())
    items.extend(_build_bronze_sourced_from_relationships())
    items.extend(_build_bronze_ingest_references())
    items.extend(_build_gold_derived_from_bronze())
    items.extend(_build_data_product_relationships())
    items.extend(_build_knowledge_asset_relationships())
    items.extend(_build_report_source_file_relationship())
    if db is not None:
        items.extend(_build_entity_to_data_product_relationships(db))
    return items


def build_relationships(db) -> list[dict[str, Any]]:
    """Merge static and DB-backed lineage relationships."""
    items = build_static_relationships(db)
    items.extend(_build_lineage_edge_relationships(db))
    return items


def build_relationships_response(db) -> dict[str, Any]:
    """Build GET /v1/product/relationships payload."""
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    lineage_node_count = 0
    lineage_edge_count = 0

    try:
        items = build_relationships(db)
        lineage_node_count = len(_fetch_lineage_nodes(db))
        lineage_edges = _fetch_lineage_edges(db)
        lineage_edge_count = len(lineage_edges)
        if lineage_node_count and lineage_edge_count == 0:
            warnings.append(
                "Lineage nodes exist but lineage edges are empty; lineage_node_to_lineage_node group is empty."
            )
    except SQLAlchemyError as exc:
        warnings.append(f"Relationship build failed: {exc}")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Unexpected relationship service error: {exc}")

    groups = _group_relationships(items)
    lineage_limitation = (
        "No lineage edge records in meta.lineage_edge; lineage_node_to_lineage_node relationships "
        "are not emitted. Pipeline publish step seeds nodes only."
        if lineage_edge_count == 0
        else ""
    )

    metadata: dict[str, Any] = {
        "source": "petrogrid.relationship_service",
        "generated_at": _utc_now(),
        "notes": (
            "Relationships are evidence-backed links from migration metadata, data product registry, "
            "entities surface, pipeline mappings, and governance lineage records. "
            "Not signals, patterns, illuminations, or decision products. No graph database."
        ),
        "allowed_relationship_types": list(ALLOWED_RELATIONSHIP_TYPES),
        "forbidden_relationship_types": list(FORBIDDEN_RELATIONSHIP_TYPES),
        "relationship_count": len(items),
        "lineage_node_count": lineage_node_count,
        "lineage_edge_count": lineage_edge_count,
        "confidence_bands": dict(CONFIDENCE_BANDS),
        "min_confidence": MIN_CONFIDENCE,
        "entities_source": ENTITIES_SOURCE,
    }
    if warnings:
        metadata["warnings"] = warnings
    if lineage_limitation:
        metadata["lineage_edges_limitation"] = lineage_limitation

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "relationships",
        "implementation_status": "implemented",
        "items": items,
        "groups": groups,
        "metadata": metadata,
    }
