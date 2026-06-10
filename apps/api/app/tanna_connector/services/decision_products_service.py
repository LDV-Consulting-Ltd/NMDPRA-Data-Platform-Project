"""Map GET /v1/product/decision-products to Tanna connector decision products."""
from __future__ import annotations

from typing import Any

from app.product_decisions.service import build_decision_products_response
from app.tanna_connector.schemas import external_id_decision_product
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_decision_products(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    items: list[dict[str, Any]] = []
    has_placeholder = False
    for decision in payload.get("items") or []:
        decision_id = decision.get("decision_product_id", "unknown")
        item = {**decision, "external_id": external_id_decision_product(decision_id)}
        if decision.get("placeholder"):
            has_placeholder = True
            item["sync_category"] = "placeholder"
        items.append(item)
    status = payload.get("implementation_status", "implemented")
    if has_placeholder and status == "implemented":
        status = "partial"
    return items, status


def build_tanna_decision_products(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_decision_products_response(db)
        items, implementation_status = _map_decision_products(source_payload)
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
        placeholder_count = sum(1 for item in items if item.get("placeholder"))
        if placeholder_count:
            warnings.append(f"{placeholder_count} decision products are placeholders.")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Decision products product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="decision_products",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.decision_products_service",
        notes="PetroGrid decision products mapped from GET /v1/product/decision-products.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/decision-products"},
    )


def assess_decision_products_maturity(db) -> dict[str, Any]:
    payload = build_tanna_decision_products(db)
    return {
        "endpoint": "decision_products",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
