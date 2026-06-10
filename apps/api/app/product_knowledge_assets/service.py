"""
PetroGrid Knowledge Assets v0.1 — read-only catalog of documentation and metadata artifacts.
No document ingestion, modification, vector DB, or AI summaries.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.product_knowledge_assets.rules import (
    ALLOWED_ASSET_TYPES,
    DIAGRAMS_TS_RELATIVE,
    DIAGRAM_ASSETS,
    ENDPOINT_ASSETS,
    FILE_ASSETS,
    FORBIDDEN_ASSET_MARKERS,
    GENERATED_DIAGRAM_GLOBS,
    PREVIEW_MAX_CHARS,
)

_REPO_ROOT: Optional[Path] = None


def _repo_root() -> Path:
    global _REPO_ROOT
    if _REPO_ROOT is None:
        _REPO_ROOT = Path(__file__).resolve().parents[4]
    return _REPO_ROOT


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _preview_text(content: str) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= PREVIEW_MAX_CHARS:
        return normalized
    return normalized[: PREVIEW_MAX_CHARS - 3] + "..."


def _build_asset(
    *,
    asset_id: str,
    asset_type: str,
    title: str,
    description: str,
    source_path: Optional[str],
    source_endpoint: Optional[str],
    content_available: bool,
    content_preview: str,
    related_data_products: list[str],
    related_entities: list[str],
    related_relationships: list[str],
    evidence: dict[str, Any],
    status: str,
    limitations: str,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "title": title,
        "description": description,
        "source_path": source_path,
        "source_endpoint": source_endpoint,
        "content_available": content_available,
        "content_preview": content_preview,
        "related_data_products": related_data_products,
        "related_entities": related_entities,
        "related_relationships": related_relationships,
        "evidence": evidence,
        "status": status,
        "limitations": limitations,
    }


def _read_file_preview(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, ""
    try:
        text_content = path.read_text(encoding="utf-8", errors="replace")
        return True, _preview_text(text_content)
    except OSError:
        return False, ""


def _parse_diagrams_ts() -> dict[str, str]:
    diagrams_path = _repo_root() / DIAGRAMS_TS_RELATIVE
    if not diagrams_path.is_file():
        return {}
    content = diagrams_path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"export const (\w+) = `([\s\S]*?)`;", content)
    return {name: body.strip() for name, body in matches}


def _build_file_assets() -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    root = _repo_root()

    for definition in FILE_ASSETS:
        file_path = root / definition.source_path
        available, preview = _read_file_preview(file_path)
        if not available:
            warnings.append(f"File asset skipped (not found): {definition.source_path}")
            continue
        items.append(
            _build_asset(
                asset_id=definition.asset_id,
                asset_type=definition.asset_type,
                title=definition.title,
                description=definition.description,
                source_path=str(definition.source_path),
                source_endpoint=None,
                content_available=True,
                content_preview=preview,
                related_data_products=list(definition.related_data_products),
                related_entities=list(definition.related_entities),
                related_relationships=list(definition.related_relationships),
                evidence={
                    "evidence_type": "repository_file",
                    "source_path": definition.source_path,
                    "absolute_path": str(file_path),
                    "file_size_bytes": file_path.stat().st_size,
                },
                status="available",
                limitations=definition.limitations,
            )
        )
    return items, warnings


def _probe_dictionary(db) -> tuple[bool, str, dict[str, Any]]:
    try:
        total = db.execute(text("SELECT COUNT(*) FROM meta.data_dictionary")).scalar() or 0
        preview = f"Governance dictionary endpoint; {int(total)} entries in meta.data_dictionary."
        return True, preview, {"row_count": int(total)}
    except (ProgrammingError, SQLAlchemyError):
        return False, "", {}


def _probe_lineage(db) -> tuple[bool, str, dict[str, Any]]:
    try:
        nodes = db.execute(text("SELECT COUNT(*) FROM meta.lineage_node")).scalar() or 0
        edges = db.execute(text("SELECT COUNT(*) FROM meta.lineage_edge")).scalar() or 0
        preview = (
            f"Lineage metadata endpoints; {int(nodes)} nodes and {int(edges)} edges recorded."
        )
        return True, preview, {"node_count": int(nodes), "edge_count": int(edges)}
    except (ProgrammingError, SQLAlchemyError):
        return False, "", {}


def _build_endpoint_assets(db) -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    warnings: list[str] = []

    for definition in ENDPOINT_ASSETS:
        preview = f"Available via GET {definition.source_endpoint}."
        evidence: dict[str, Any] = {
            "evidence_type": "api_endpoint",
            "source_endpoint": definition.source_endpoint,
        }
        available = True

        if definition.asset_id == "knowledge.governance.data_dictionary":
            ok, preview, stats = _probe_dictionary(db)
            available = ok
            evidence.update(stats)
            if ok and stats.get("row_count", 0) == 0:
                preview = "Endpoint available; meta.data_dictionary currently empty."

        elif definition.asset_id == "knowledge.governance.lineage":
            ok, preview, stats = _probe_lineage(db)
            available = ok
            evidence.update(stats)
            evidence["edges_endpoint"] = "/v1/governance/lineage/edges"
            if ok and stats.get("edge_count", 0) == 0:
                preview = "Lineage nodes may exist; lineage edges currently empty."

        elif definition.asset_id == "knowledge.openapi":
            evidence["runtime"] = True
            preview = "OpenAPI 3.x document served by FastAPI at runtime."

        elif definition.asset_id == "knowledge.data_layers.metadata":
            evidence["layers"] = ["bronze", "silver", "gold"]
            preview = "Table metadata via GET /v1/data-layers/tables?layer=bronze|silver|gold."

        if not available:
            warnings.append(f"Endpoint asset skipped (unavailable): {definition.source_endpoint}")
            continue

        items.append(
            _build_asset(
                asset_id=definition.asset_id,
                asset_type=definition.asset_type,
                title=definition.title,
                description=definition.description,
                source_path=definition.source_path,
                source_endpoint=definition.source_endpoint,
                content_available=True,
                content_preview=preview,
                related_data_products=list(definition.related_data_products),
                related_entities=list(definition.related_entities),
                related_relationships=list(definition.related_relationships),
                evidence=evidence,
                status="available",
                limitations=definition.limitations,
            )
        )

    return items, warnings


def _build_diagram_assets() -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    diagrams = _parse_diagrams_ts()
    diagrams_path = _repo_root() / DIAGRAMS_TS_RELATIVE

    if not diagrams_path.is_file():
        warnings.append(f"Diagram source skipped (not found): {DIAGRAMS_TS_RELATIVE}")
        return items, warnings

    for definition in DIAGRAM_ASSETS:
        body = diagrams.get(definition.export_name)
        if not body:
            warnings.append(f"Diagram export skipped (not found): {definition.export_name}")
            continue
        items.append(
            _build_asset(
                asset_id=definition.asset_id,
                asset_type=definition.asset_type,
                title=definition.title,
                description=definition.description,
                source_path=DIAGRAMS_TS_RELATIVE,
                source_endpoint=None,
                content_available=True,
                content_preview=_preview_text(body),
                related_data_products=list(definition.related_data_products),
                related_entities=list(definition.related_entities),
                related_relationships=list(definition.related_relationships),
                evidence={
                    "evidence_type": "mermaid_export",
                    "source_path": DIAGRAMS_TS_RELATIVE,
                    "export_name": definition.export_name,
                    "diagram_format": "mermaid",
                },
                status="available",
                limitations=definition.limitations,
            )
        )

    for pattern in GENERATED_DIAGRAM_GLOBS:
        if list(_repo_root().glob(pattern)):
            warnings.append(
                f"Generated diagram outputs exist ({pattern}) but PNG/SVG assets are not exposed in v0.1."
            )

    return items, warnings


def build_knowledge_assets(db) -> tuple[list[dict[str, Any]], list[str]]:
    """Assemble knowledge assets from files, endpoints, and diagram exports."""
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    file_items, file_warnings = _build_file_assets()
    endpoint_items, endpoint_warnings = _build_endpoint_assets(db)
    diagram_items, diagram_warnings = _build_diagram_assets()

    items.extend(file_items)
    items.extend(endpoint_items)
    items.extend(diagram_items)
    warnings.extend(file_warnings)
    warnings.extend(endpoint_warnings)
    warnings.extend(diagram_warnings)

    return items, warnings


def build_knowledge_assets_response(db) -> dict[str, Any]:
    """Build GET /v1/product/knowledge-assets payload."""
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    try:
        items, warnings = build_knowledge_assets(db)
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Knowledge asset build failed: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.knowledge_asset_service",
        "generated_at": _utc_now(),
        "notes": (
            "Knowledge assets catalog existing documentation, OpenAPI, Mermaid diagrams, "
            "and governance metadata endpoints. No AI summaries or vector search."
        ),
        "allowed_asset_types": list(ALLOWED_ASSET_TYPES),
        "asset_count": len(items),
        "forbidden_asset_markers": list(FORBIDDEN_ASSET_MARKERS),
        "preview_max_chars": PREVIEW_MAX_CHARS,
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "knowledge_assets",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
