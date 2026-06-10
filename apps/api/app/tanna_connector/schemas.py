"""Tanna connector schemas and stable external_id helpers."""
from __future__ import annotations

import re

MODULE_ID = "petrogrid"
MODULE_NAME = "PetroGrid"

EXTERNAL_ID_STRATEGY = "petrogrid:{object_type}:{stable_identifier}"
DUPLICATE_HANDLING_NOTES = (
    "Stable identifiers are derived from PetroGrid product surface keys "
    "(product_id, entity_id, relationship_id, signal_id, etc.). "
    "Tanna should upsert by external_id; duplicates are rejected at sync time."
)

IMPLEMENTATION_STATUSES = ("implemented", "partial", "placeholder", "not_implemented")

ENVELOPE_METADATA_KEYS = (
    "source",
    "notes",
    "generated_at",
    "sync_ready",
    "sync_notes",
    "external_id_strategy",
    "duplicate_handling_notes",
)


def _sanitize(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned.lower() or "unknown"


def external_id(object_type: str, stable_identifier: str) -> str:
    return f"petrogrid:{object_type}:{_sanitize(stable_identifier)}"


def external_id_data_product(product_id: str) -> str:
    return external_id("data_product", product_id)


def external_id_entity(entity_id: str) -> str:
    if "." in entity_id:
        entity_type, instance = entity_id.split(".", 1)
        return f"petrogrid:entity:{_sanitize(entity_type)}:{_sanitize(instance)}"
    return external_id("entity", entity_id)


def external_id_relationship(relationship_id: str) -> str:
    return external_id("relationship", relationship_id)


def external_id_signal(signal_id: str) -> str:
    return external_id("signal", signal_id)


def external_id_pattern(pattern_id: str) -> str:
    return external_id("pattern", pattern_id)


def external_id_illumination(illumination_id: str) -> str:
    return external_id("illumination", illumination_id)


def external_id_decision_product(decision_product_id: str) -> str:
    return external_id("decision_product", decision_product_id)


def external_id_knowledge_asset(asset_id: str) -> str:
    return external_id("knowledge_asset", asset_id)


def external_id_capability(capability_id: str) -> str:
    return external_id("capability", capability_id)


def external_id_health_check(check_name: str) -> str:
    return external_id("health", check_name)
