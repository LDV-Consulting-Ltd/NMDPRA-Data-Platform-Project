"""Map GET /v1/product/illuminations to Tanna connector illuminations."""
from __future__ import annotations

from typing import Any

from app.product_illuminations.service import build_illuminations_response
from app.tanna_connector.schemas import external_id_illumination
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_illuminations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for illumination in payload.get("items") or []:
        illumination_id = illumination.get("illumination_id", "unknown")
        items.append({**illumination, "external_id": external_id_illumination(illumination_id)})
    return items


def build_tanna_illuminations(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_illuminations_response(db)
        items = _map_illuminations(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Illuminations product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="illuminations",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.illuminations_service",
        notes="PetroGrid illuminations mapped from GET /v1/product/illuminations.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/illuminations"},
    )


def assess_illuminations_maturity(db) -> dict[str, Any]:
    payload = build_tanna_illuminations(db)
    return {
        "endpoint": "illuminations",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
