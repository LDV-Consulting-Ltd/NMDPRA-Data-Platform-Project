"""Map GET /v1/product/signals to Tanna connector signals."""
from __future__ import annotations

from typing import Any

from app.product_signals.service import build_signals_response
from app.tanna_connector.schemas import external_id_signal
from app.tanna_connector.services.envelope import build_envelope, sync_ready_for_status


def _map_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for signal in payload.get("items") or []:
        signal_id = signal.get("signal_id", "unknown")
        items.append({**signal, "external_id": external_id_signal(signal_id)})
    return items


def build_tanna_signals(db) -> dict[str, Any]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    implementation_status = "not_implemented"
    source_payload: dict[str, Any] = {}

    try:
        source_payload = build_signals_response(db)
        items = _map_signals(source_payload)
        implementation_status = source_payload.get("implementation_status", "implemented")
        surface_warnings = source_payload.get("metadata", {}).get("warnings")
        if surface_warnings:
            warnings.extend(surface_warnings)
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Signals product surface failed: {exc}")
        implementation_status = "partial"

    sync_ready, sync_notes = sync_ready_for_status(implementation_status, items)
    return build_envelope(
        object_type="signals",
        implementation_status=implementation_status,
        items=items,
        source="petrogrid.tanna_connector.signals_service",
        notes="PetroGrid signals mapped from GET /v1/product/signals.",
        sync_ready=sync_ready,
        sync_notes=sync_notes,
        warnings=warnings or None,
        extra_metadata={"product_surface": "/v1/product/signals"},
    )


def assess_signals_maturity(db) -> dict[str, Any]:
    payload = build_tanna_signals(db)
    return {
        "endpoint": "signals",
        "implementation_status": payload["implementation_status"],
        "sync_ready": payload["metadata"]["sync_ready"],
        "object_count": len(payload["items"]),
        "items": payload["items"],
    }
