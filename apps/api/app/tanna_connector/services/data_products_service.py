"""Map GET /v1/product/data-products to Tanna connector data products."""
from __future__ import annotations

from typing import Any

from app.data_product_registry import build_data_product_registry
from app.tanna_connector.schemas import external_id_data_product
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _flatten_products(registry: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group_name, products in (registry.get("groups") or {}).items():
        for product in products:
            product_id = product.get("product_id", "unknown")
            items.append(
                {
                    **product,
                    "external_id": external_id_data_product(product_id),
                    "registry_group": group_name,
                }
            )
    return items


def build_tanna_data_products() -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    registry: dict[str, Any] = {}

    try:
        registry = build_data_product_registry()
        items = _flatten_products(registry)
        if items:
            implementation_status = "implemented"
            partial_count = sum(1 for item in items if not item.get("tanna_sync_ready", True))
            if partial_count:
                implementation_status = "partial"
                warnings.append(
                    f"{partial_count} data products marked not tanna_sync_ready in registry."
                )
        else:
            implementation_status = "partial"
            warnings.append("Data product registry returned no products.")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Data products product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="data_products",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.data_products_service",
        notes="PetroGrid data product registry mapped from GET /v1/product/data-products.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={
            "product_surface": "/v1/product/data-products",
            "registry_version": registry.get("registry_version"),
            "excluded_layers": registry.get("excluded_layers"),
        },
    )


def assess_data_products_maturity() -> dict[str, Any]:
    payload = build_tanna_data_products()
    return {
        "endpoint": "data_products",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
