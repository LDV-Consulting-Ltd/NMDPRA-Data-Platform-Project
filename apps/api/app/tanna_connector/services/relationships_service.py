"""Map GET /v1/product/relationships to Tanna connector relationships."""
from __future__ import annotations

from typing import Any

from app.product_relationships.service import build_relationships_response
from app.tanna_connector.schemas import external_id_relationship
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_relationships(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for relationship in payload.get("items") or []:
        relationship_id = relationship.get("relationship_id", "unknown")
        items.append({**relationship, "external_id": external_id_relationship(relationship_id)})
    return items


def build_tanna_relationships(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_relationships_response(db)
        items = _map_relationships(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
        lineage_limitation = source_payload.get("metadata", {}).get("lineage_edges_limitation")
        if lineage_limitation:
            warnings.append(lineage_limitation)
        if not items:
            implementation_status = "partial"
            warnings.append("Relationships product surface returned no items.")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Relationships product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="relationships",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.relationships_service",
        notes="PetroGrid relationships mapped from GET /v1/product/relationships.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={
            "product_surface": "/v1/product/relationships",
            "relationship_groups": source_payload.get("groups"),
        },
    )


def assess_relationships_maturity(db) -> dict[str, Any]:
    payload = build_tanna_relationships(db)
    return {
        "endpoint": "relationships",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
