"""Standard Tanna connector response envelope."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.tanna_connector.schemas import (
    DUPLICATE_HANDLING_NOTES,
    EXTERNAL_ID_STRATEGY,
    MODULE_ID,
    MODULE_NAME,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_envelope(
    *,
    object_type: str,
    implementation_status: str,
    items: list[dict[str, Any]],
    source: str,
    notes: str,
    sync_ready: bool,
    sync_notes: str,
    warnings: Optional[list[str]] = None,
    extra_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source": source,
        "notes": notes,
        "generated_at": utc_now(),
        "sync_ready": sync_ready,
        "sync_notes": sync_notes,
        "external_id_strategy": EXTERNAL_ID_STRATEGY,
        "duplicate_handling_notes": DUPLICATE_HANDLING_NOTES,
    }
    if warnings:
        metadata["warnings"] = warnings
    if extra_metadata:
        metadata.update(extra_metadata)

    return {
        "module_id": MODULE_ID,
        "module_name": MODULE_NAME,
        "object_type": object_type,
        "implementation_status": implementation_status,
        "items": items,
        "metadata": metadata,
    }


def sync_ready_for_status(implementation_status: str, items: list[dict[str, Any]]) -> tuple[bool, str]:
    if implementation_status == "implemented":
        return True, "Backing product surface is implemented with stable external_ids."
    if implementation_status == "partial":
        if items and all(item.get("external_id") for item in items):
            return True, "Partial coverage; objects include stable external_ids and documented limitations."
        return False, "Partial coverage without stable external_ids on all objects."
    if implementation_status == "placeholder":
        return False, "Placeholder objects are not ready for Tanna sync."
    return False, "Endpoint is not implemented."
