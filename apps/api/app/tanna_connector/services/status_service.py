"""Tanna connector status and maturity matrix."""
from __future__ import annotations

from typing import Any

from app.tanna_connector.config import get_tanna_config
from app.tanna_connector.schemas import MODULE_ID, MODULE_NAME
from app.tanna_connector.services.data_products_service import assess_data_products_maturity
from app.tanna_connector.services.decision_products_service import assess_decision_products_maturity
from app.tanna_connector.services.entities_service import assess_entities_maturity
from app.tanna_connector.services.envelope import utc_now
from app.tanna_connector.services.health_service import assess_health_maturity
from app.tanna_connector.services.illuminations_service import assess_illuminations_maturity
from app.tanna_connector.services.knowledge_assets_service import assess_knowledge_assets_maturity
from app.tanna_connector.services.manifest_service import assess_manifest_maturity
from app.tanna_connector.services.patterns_service import assess_patterns_maturity
from app.tanna_connector.services.relationships_service import assess_relationships_maturity
from app.tanna_connector.services.signals_service import assess_signals_maturity


def _classify_objects(assessments: list[dict[str, Any]]) -> dict[str, list[str]]:
    implemented: list[str] = []
    partial: list[str] = []
    placeholder: list[str] = []
    not_implemented: list[str] = []
    sync_ready: list[str] = []
    sync_blocked: list[str] = []

    for assessment in assessments:
        endpoint_status = assessment["implementation_status"]
        endpoint_sync_ready = bool(assessment.get("sync_ready"))
        for item in assessment.get("items") or []:
            external_id = item.get("external_id")
            if not external_id:
                continue

            is_placeholder = bool(
                item.get("placeholder") or item.get("sync_category") == "placeholder"
            )
            is_unsupported = item.get("sync_category") == "unsupported"

            if is_placeholder:
                placeholder.append(external_id)
                sync_blocked.append(external_id)
                continue
            if is_unsupported or endpoint_status == "not_implemented":
                not_implemented.append(external_id)
                sync_blocked.append(external_id)
                continue
            if endpoint_status == "implemented":
                implemented.append(external_id)
            else:
                partial.append(external_id)

            item_ready = endpoint_sync_ready and bool(external_id)
            if endpoint_status == "partial":
                item_ready = item_ready and bool(item.get("limitations") or item.get("reason"))
            if item_ready:
                sync_ready.append(external_id)
            else:
                sync_blocked.append(external_id)

    return {
        "implemented_objects": sorted(set(implemented)),
        "partial_objects": sorted(set(partial)),
        "placeholder_objects": sorted(set(placeholder)),
        "not_implemented_objects": sorted(set(not_implemented)),
        "sync_ready_objects": sorted(set(sync_ready)),
        "sync_blocked_objects": sorted(set(sync_blocked)),
    }


def _overall_status(matrix: dict[str, dict[str, Any]]) -> str:
    statuses = {entry["implementation_status"] for entry in matrix.values()}
    if statuses == {"implemented"}:
        return "ready"
    if "not_implemented" in statuses:
        return "degraded"
    return "partial"


def build_tanna_status(db, *, api_title: str) -> dict[str, Any]:
    config = get_tanna_config()
    assessments = [
        assess_manifest_maturity(api_title=api_title),
        assess_health_maturity(db),
        assess_data_products_maturity(),
        assess_entities_maturity(db),
        assess_relationships_maturity(db),
        assess_signals_maturity(db),
        assess_patterns_maturity(db),
        assess_illuminations_maturity(db),
        assess_decision_products_maturity(db),
        assess_knowledge_assets_maturity(db),
    ]

    endpoint_maturity_matrix = {
        assessment["endpoint"]: {
            "implementation_status": assessment["implementation_status"],
            "sync_ready": assessment["sync_ready"],
            "object_count": assessment["object_count"],
        }
        for assessment in assessments
    }
    classified = _classify_objects(assessments)

    return {
        "connector_version": config.connector_version,
        "module_id": MODULE_ID,
        "module_name": MODULE_NAME,
        "overall_status": _overall_status(endpoint_maturity_matrix),
        "endpoint_maturity_matrix": endpoint_maturity_matrix,
        **classified,
        "last_generated_at": utc_now(),
    }
