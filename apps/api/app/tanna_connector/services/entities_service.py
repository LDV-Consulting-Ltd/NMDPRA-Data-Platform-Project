"""Map GET /v1/product/entities to Tanna connector entities."""
from __future__ import annotations

from typing import Any

from app.product_entities.service import build_entities_response
from app.tanna_connector.schemas import external_id_entity
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_entities(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entity in payload.get("items") or []:
        entity_id = entity.get("entity_id", "unknown")
        items.append({**entity, "external_id": external_id_entity(entity_id)})
    return items


def build_tanna_entities(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_entities_response(db)
        items = _map_entities(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
        if not items:
            implementation_status = "partial"
            warnings.append("Entities product surface returned no items.")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Entities product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="entities",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.entities_service",
        notes="PetroGrid entities mapped from GET /v1/product/entities.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/entities"},
    )


def assess_entities_maturity(db) -> dict[str, Any]:
    payload = build_tanna_entities(db)
    return {
        "endpoint": "entities",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
