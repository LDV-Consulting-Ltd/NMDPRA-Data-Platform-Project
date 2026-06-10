"""Map GET /v1/product/manifest to Tanna connector manifest."""
from __future__ import annotations

from typing import Any, Optional

from app.product_manifest import build_product_manifest
from app.tanna_connector.schemas import external_id_capability
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_manifest_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for capability in payload.get("supported_capabilities") or []:
        cap_id = capability.get("id", "unknown")
        items.append(
            {
                "external_id": external_id_capability(cap_id),
                "capability_id": cap_id,
                "status": capability.get("status", "implemented"),
                "evidence": capability.get("evidence"),
                "sync_category": "supported",
            }
        )
    for capability in payload.get("unsupported_capabilities") or []:
        cap_id = capability.get("id", "unknown")
        items.append(
            {
                "external_id": external_id_capability(cap_id),
                "capability_id": cap_id,
                "status": capability.get("status", "not_implemented"),
                "reason": capability.get("reason"),
                "sync_category": "unsupported",
            }
        )
    return items


def build_tanna_manifest(*, api_title: str) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_product_manifest(api_title=api_title)
        items = _map_manifest_items(source_payload)
        implementation_status = "implemented" if items else "partial"
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Manifest product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="manifest",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.manifest_service",
        notes=(
            "PetroGrid capability manifest mapped from GET /v1/product/manifest. "
            "Tanna uses this to register PetroGrid module capabilities."
        ),
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={
            "product_surface": "/v1/product/manifest",
            "api_title": source_payload.get("api_title"),
            "registry_version": source_payload.get("generated_at"),
        },
    )


def assess_manifest_maturity(*, api_title: str) -> dict[str, Any]:
    payload = build_tanna_manifest(api_title=api_title)
    return {
        "endpoint": "manifest",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
