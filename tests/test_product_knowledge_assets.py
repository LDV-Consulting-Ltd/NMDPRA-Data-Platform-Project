"""Tests for PetroGrid Knowledge Assets v0.1 (GET /v1/product/knowledge-assets)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402
from app.product_knowledge_assets.rules import (  # noqa: E402
    ALLOWED_ASSET_TYPES,
    FILE_ASSETS,
    FORBIDDEN_ASSET_MARKERS,
)
from app.product_knowledge_assets.service import (  # noqa: E402
    build_knowledge_assets_response,
    build_knowledge_assets,
)

REQUIRED_FIELDS = {
    "asset_id",
    "asset_type",
    "title",
    "description",
    "source_path",
    "source_endpoint",
    "content_available",
    "content_preview",
    "related_data_products",
    "related_entities",
    "related_relationships",
    "evidence",
    "status",
    "limitations",
}


@pytest.fixture
def client():
    return TestClient(app)


def test_knowledge_assets_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/knowledge-assets")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["object_type"] == "knowledge_assets"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert data["metadata"]["source"] == "petrogrid.knowledge_asset_service"


def test_only_existing_files_and_endpoints_exposed(client):
    data = client.get("/v1/product/knowledge-assets").json()
    asset_ids = {item["asset_id"] for item in data["items"]}

    for definition in FILE_ASSETS:
        file_path = ROOT / definition.source_path
        if file_path.is_file():
            assert definition.asset_id in asset_ids
        else:
            assert definition.asset_id not in asset_ids

    for item in data["items"]:
        assert item["asset_type"] in ALLOWED_ASSET_TYPES
        for marker in FORBIDDEN_ASSET_MARKERS:
            assert marker not in item["asset_id"]
        if item["source_path"]:
            assert Path(item["source_path"]).name in item["source_path"] or item["source_path"].endswith(".ts")


def test_missing_generated_diagram_outputs_not_claimed(client):
    data = client.get("/v1/product/knowledge-assets").json()
    for item in data["items"]:
        assert item["asset_type"] not in ("generated_png", "generated_svg")
        assert "generated_png" not in item["asset_id"]
        assert "docs/diagrams" not in (item.get("source_path") or "")
    warnings = data.get("metadata", {}).get("warnings", [])
    assert not any("invented" in w.lower() for w in warnings)


def test_openapi_exposed_as_knowledge_asset(client):
    data = client.get("/v1/product/knowledge-assets").json()
    openapi_assets = [i for i in data["items"] if i["asset_id"] == "knowledge.openapi"]
    assert openapi_assets
    asset = openapi_assets[0]
    assert asset["asset_type"] == "openapi_spec"
    assert asset["source_endpoint"] == "/openapi.json"
    assert asset["content_available"] is True


def test_mermaid_diagrams_exposed_from_diagrams_ts(client):
    diagrams_path = ROOT / "apps" / "web" / "lib" / "diagrams.ts"
    data = client.get("/v1/product/knowledge-assets").json()
    diagram_items = [i for i in data["items"] if i["asset_type"] in ("mermaid_diagram", "architecture_reference")]
    if diagrams_path.is_file():
        assert len(diagram_items) >= 3
        export_names = {i["evidence"].get("export_name") for i in diagram_items}
        assert "DATA_ARCHITECTURE_MMD" in export_names
        assert "LINEAGE_MMD" in export_names
        assert "DATA_MODEL_MMD" in export_names
    else:
        assert diagram_items == []


def test_knowledge_assets_include_evidence(client):
    data = client.get("/v1/product/knowledge-assets").json()
    for item in data["items"]:
        assert REQUIRED_FIELDS.issubset(item.keys())
        assert item["evidence"]
        assert "evidence_type" in item["evidence"]


def test_no_documents_modified_during_build():
    readme = ROOT / "README.md"
    if not readme.is_file():
        pytest.skip("README.md not present")
    before_mtime = readme.stat().st_mtime
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(scalar=MagicMock(return_value=0))
    build_knowledge_assets_response(db)
    after_mtime = readme.stat().st_mtime
    assert before_mtime == after_mtime


def test_no_database_writes_occur():
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(scalar=MagicMock(return_value=0))
    build_knowledge_assets_response(db)
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_db_probe_failure_still_returns_file_and_diagram_assets():
    db = MagicMock()
    db.execute.side_effect = OperationalError("stmt", {}, Exception("db down"))
    items, warnings = build_knowledge_assets(db)
    assert warnings
    assert any(i["asset_id"] == "knowledge.readme" for i in items if (ROOT / "README.md").is_file())
    assert not any(i["asset_id"] == "knowledge.governance.data_dictionary" for i in items)


def test_manifest_lists_knowledge_asset_surface(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "knowledge_asset_surface" in supported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/knowledge-assets").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/v1/product/knowledge-assets" in paths
