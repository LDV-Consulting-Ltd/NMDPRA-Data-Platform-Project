"""Map GET /v1/product/knowledge-assets to Tanna connector knowledge assets."""
from __future__ import annotations

from typing import Any

from app.product_knowledge_assets.service import build_knowledge_assets_response
from app.tanna_connector.schemas import external_id_knowledge_asset
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_knowledge_assets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for asset in payload.get("items") or []:
        asset_id = asset.get("asset_id", "unknown")
        items.append({**asset, "external_id": external_id_knowledge_asset(asset_id)})
    return items


def build_tanna_knowledge_assets(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_knowledge_assets_response(db)
        items = _map_knowledge_assets(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
        if not items:
            implementation_status = "partial"
            warnings.append("Knowledge assets product surface returned no items.")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Knowledge assets product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="knowledge_assets",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.knowledge_assets_service",
        notes="PetroGrid knowledge assets mapped from GET /v1/product/knowledge-assets.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/knowledge-assets"},
    )


def assess_knowledge_assets_maturity(db) -> dict[str, Any]:
    payload = build_tanna_knowledge_assets(db)
    return {
        "endpoint": "knowledge_assets",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
