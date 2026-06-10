"""Map GET /v1/product/patterns to Tanna connector patterns."""
from __future__ import annotations

from typing import Any

from app.product_patterns.service import build_patterns_response
from app.tanna_connector.schemas import external_id_pattern
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_patterns(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for pattern in payload.get("items") or []:
        pattern_id = pattern.get("pattern_id", "unknown")
        items.append({**pattern, "external_id": external_id_pattern(pattern_id)})
    return items


def build_tanna_patterns(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_patterns_response(db)
        items = _map_patterns(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Patterns product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="patterns",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.patterns_service",
        notes="PetroGrid patterns mapped from GET /v1/product/patterns.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/patterns"},
    )


def assess_patterns_maturity(db) -> dict[str, Any]:
    payload = build_tanna_patterns(db)
    return {
        "endpoint": "patterns",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
