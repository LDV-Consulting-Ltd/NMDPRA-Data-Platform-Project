"""
PetroGrid Entities v0.1 — read-only entity catalog and safe instance enumeration.
No persistence, no invented entities, no database writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.data_product_registry import build_data_product_registry
from app.product_entities.rules import (
    ALLOWED_ENTITY_GROUPS,
    CONFIDENCE,
    ENTITY_TYPE_DEFINITIONS,
    EntityTypeDefinition,
    MIGRATION_SOURCE,
    MIGRATION_TABLES,
    REGISTRY_SOURCE,
    SCHEMAS_SOURCE,
    THRESHOLDS,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (int, float, bool, str)):
        return value
    return str(value)


def _build_entity(
    *,
    entity_id: str,
    definition: EntityTypeDefinition,
    entity_name: str,
    description: str,
    attributes: dict[str, Any],
    evidence: dict[str, Any],
    confidence: float,
    status: str,
    limitations: str,
    backing_table: Optional[str] = None,
    backing_api: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "entity_type": definition.entity_group,
        "entity_name": entity_name,
        "description": description,
        "source_layer": definition.source_layer,
        "backing_table": backing_table if backing_table is not None else definition.backing_table,
        "backing_api": backing_api if backing_api is not None else definition.backing_api,
        "attributes": attributes,
        "evidence": evidence,
        "confidence": round(confidence, 2),
        "status": status,
        "limitations": limitations,
    }


def _type_summary_entity(definition: EntityTypeDefinition) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "evidence_type": "entity_type_summary",
        "entity_type": definition.entity_type,
        "migration_file": MIGRATION_SOURCE,
    }
    if definition.pydantic_schema:
        evidence["pydantic_schema"] = definition.pydantic_schema
        evidence["schemas_source"] = SCHEMAS_SOURCE
    if definition.backing_table:
        evidence["backing_table"] = definition.backing_table

    return _build_entity(
        entity_id=f"type.{definition.entity_type}",
        definition=definition,
        entity_name=definition.display_name,
        description=definition.description,
        attributes={
            "entity_group": definition.entity_group,
            "attributes_schema": list(definition.attributes_schema),
        },
        evidence=evidence,
        confidence=CONFIDENCE["type_summary"],
        status="summary",
        limitations=definition.limitations,
    )


def _instance_entity(
    definition: EntityTypeDefinition,
    *,
    instance_id: str,
    entity_name: str,
    attributes: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return _build_entity(
        entity_id=f"{definition.entity_type}.{instance_id}",
        definition=definition,
        entity_name=entity_name or instance_id,
        description=definition.description,
        attributes=attributes,
        evidence=evidence,
        confidence=CONFIDENCE["db_instance"],
        status="active",
        limitations=definition.limitations,
    )


def _query_instances(db, definition: EntityTypeDefinition) -> list[dict[str, Any]]:
    if not definition.instance_query or not definition.instance_id_field:
        return []

    rows = db.execute(
        text(definition.instance_query),
        {"lim": THRESHOLDS["instance_query_limit"]},
    ).fetchall()
    if not rows:
        return []

    colnames = list(rows[0]._mapping.keys()) if hasattr(rows[0], "_mapping") else []
    items: list[dict[str, Any]] = []
    for row in rows:
        if hasattr(row, "_mapping"):
            record = dict(row._mapping)
        else:
            record = {colnames[i]: row[i] for i in range(len(colnames))}

        instance_id = record.get(definition.instance_id_field)
        if instance_id is None:
            continue
        if definition.entity_type == "gas_infrastructure":
            category = record.get("category") or "unknown"
            instance_id_str = f"{category}:{instance_id}"
        else:
            instance_id_str = str(instance_id)
        name_field = definition.instance_name_field or definition.instance_id_field
        entity_name = str(record.get(name_field) or instance_id_str)

        attributes = {
            key: _serialize_value(record.get(key))
            for key in definition.attributes_schema
            if key in record
        }

        evidence = {
            "evidence_type": "database_instance",
            "backing_table": definition.backing_table,
            "instance_id_field": definition.instance_id_field,
            "instance_id": instance_id_str,
            "query_limit": THRESHOLDS["instance_query_limit"],
        }
        if definition.pydantic_schema:
            evidence["pydantic_schema"] = definition.pydantic_schema
            evidence["schemas_source"] = SCHEMAS_SOURCE

        items.append(
            _instance_entity(
                definition,
                instance_id=instance_id_str,
                entity_name=entity_name,
                attributes=attributes,
                evidence=evidence,
            )
        )
    return items


def _api_product_entities() -> list[dict[str, Any]]:
    registry = build_data_product_registry()
    definition = ENTITY_TYPE_DEFINITIONS["api_product"]
    items: list[dict[str, Any]] = []

    for group_name, products in registry["groups"].items():
        if group_name != "api_data_products":
            continue
        for product in products:
            product_id = product["product_id"]
            items.append(
                _build_entity(
                    entity_id=f"api_product.{product_id}",
                    definition=definition,
                    entity_name=product["product_name"],
                    description=product["description"],
                    attributes={
                        "product_id": product_id,
                        "domain": product.get("domain"),
                        "backing_api": product.get("backing_api"),
                        "backing_table": product.get("backing_table"),
                        "source_layer": product.get("source_layer"),
                    },
                    evidence={
                        "evidence_type": "data_product_registry",
                        "registry_source": REGISTRY_SOURCE,
                        "registry_group": group_name,
                        "product_id": product_id,
                    },
                    confidence=CONFIDENCE["registry_defined"],
                    status="active",
                    limitations=product.get("limitations") or definition.limitations,
                    backing_table=product.get("backing_table"),
                    backing_api=product.get("backing_api"),
                )
            )
    return items


def _data_layer_table_entities() -> list[dict[str, Any]]:
    definition = ENTITY_TYPE_DEFINITIONS["data_layer_table"]
    items: list[dict[str, Any]] = []
    for schema, table_name in MIGRATION_TABLES:
        table_id = f"{schema}.{table_name}"
        items.append(
            _build_entity(
                entity_id=f"data_layer_table.{table_id}",
                definition=definition,
                entity_name=table_id,
                description=f"Warehouse table {table_id} defined in migration schema.",
                attributes={
                    "schema": schema,
                    "table_name": table_name,
                    "layer": schema,
                },
                evidence={
                    "evidence_type": "migration_metadata",
                    "migration_file": MIGRATION_SOURCE,
                    "schema": schema,
                    "table_name": table_name,
                },
                confidence=CONFIDENCE["migration_defined"],
                status="active",
                limitations=definition.limitations,
                backing_table=table_id,
            )
        )
    return items


def build_entities(db) -> tuple[list[dict[str, Any]], list[str]]:
    """Build entity list with type summaries and safe instance queries."""
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for entity_type in ALLOWED_ENTITY_GROUPS:
        definition = ENTITY_TYPE_DEFINITIONS[entity_type]
        summary = _type_summary_entity(definition)
        items.append(summary)
        seen_ids.add(summary["entity_id"])

    items.extend(_api_product_entities())
    items.extend(_data_layer_table_entities())
    for entity in items:
        seen_ids.add(entity["entity_id"])

    for entity_type in ALLOWED_ENTITY_GROUPS:
        if entity_type in ("data_layer_table", "api_product"):
            continue
        definition = ENTITY_TYPE_DEFINITIONS[entity_type]
        try:
            instances = _query_instances(db, definition)
            for instance in instances:
                if instance["entity_id"] not in seen_ids:
                    items.append(instance)
                    seen_ids.add(instance["entity_id"])
        except (ProgrammingError, SQLAlchemyError) as exc:
            warnings.append(
                f"Instance query skipped for {entity_type}: {exc}"
            )

    return items, warnings


def build_entities_response(db) -> dict[str, Any]:
    """Build GET /v1/product/entities payload."""
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    try:
        items, warnings = build_entities(db)
    except SQLAlchemyError as exc:
        warnings.append(f"Entity build failed: {exc}")
        for entity_type in ALLOWED_ENTITY_GROUPS:
            definition = ENTITY_TYPE_DEFINITIONS[entity_type]
            items.append(_type_summary_entity(definition))
        items.extend(_api_product_entities())
        items.extend(_data_layer_table_entities())
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Unexpected entity service error: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.entity_service",
        "generated_at": _utc_now(),
        "notes": (
            "Entities are evidence-backed business objects from migration schema, "
            "data product registry, Pydantic schemas, and safe read-only queries."
        ),
        "entity_group_count": len(ALLOWED_ENTITY_GROUPS),
        "entity_count": len(items),
        "thresholds": dict(THRESHOLDS),
        "allowed_entity_groups": list(ALLOWED_ENTITY_GROUPS),
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "entities",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
