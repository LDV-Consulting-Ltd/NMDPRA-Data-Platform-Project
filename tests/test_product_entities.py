"""Tests for PetroGrid Entities v0.1 (GET /v1/product/entities)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, ProgrammingError

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402
from app.product_entities.rules import (  # noqa: E402
    ALLOWED_ENTITY_GROUPS,
    ENTITY_TYPE_DEFINITIONS,
    FORBIDDEN_ENTITY_MARKERS,
)
from app.product_entities.service import build_entities_response  # noqa: E402

REQUIRED_FIELDS = {
    "entity_id",
    "entity_type",
    "entity_name",
    "description",
    "source_layer",
    "backing_table",
    "backing_api",
    "attributes",
    "evidence",
    "confidence",
    "status",
    "limitations",
}

FAKE_ENTITY_TYPES = (
    "Market Entity",
    "Regulatory Enforcement",
    "Supply Shortage",
    "AI Entity",
)


@pytest.fixture
def client():
    return TestClient(app)


def test_entities_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/entities")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["object_type"] == "entities"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert data["metadata"]["source"] == "petrogrid.entity_service"


def test_entities_are_evidence_backed(client):
    data = client.get("/v1/product/entities").json()
    for item in data["items"]:
        assert REQUIRED_FIELDS.issubset(item.keys())
        assert item["evidence"]
        assert "evidence_type" in item["evidence"]
        assert 0.0 <= item["confidence"] <= 1.0


def test_no_invented_entities(client):
    data = client.get("/v1/product/entities").json()
    type_summaries = {item["entity_id"] for item in data["items"] if item["status"] == "summary"}
    for entity_type in ALLOWED_ENTITY_GROUPS:
        assert f"type.{entity_type}" in type_summaries

    for item in data["items"]:
        assert item["entity_type"] not in FAKE_ENTITY_TYPES
        for marker in FORBIDDEN_ENTITY_MARKERS:
            assert marker not in item["entity_id"]
        entity_key = item["entity_id"].split(".", 1)[0]
        if item["status"] == "summary":
            assert item["entity_id"].startswith("type.")
        elif item["entity_id"].startswith("api_product."):
            assert entity_key == "api_product"
        elif item["entity_id"].startswith("data_layer_table."):
            assert entity_key == "data_layer_table"
        else:
            assert entity_key in ALLOWED_ENTITY_GROUPS


def test_all_allowed_entity_groups_have_type_definitions():
    assert set(ENTITY_TYPE_DEFINITIONS.keys()) == set(ALLOWED_ENTITY_GROUPS)


def test_db_failure_still_returns_type_summaries_and_static_entities():
    db = MagicMock()
    db.execute.side_effect = OperationalError("stmt", {}, Exception("db down"))
    payload = build_entities_response(db)
    assert payload["implementation_status"] == "implemented"
    summary_ids = {i["entity_id"] for i in payload["items"] if i["status"] == "summary"}
    for entity_type in ALLOWED_ENTITY_GROUPS:
        assert f"type.{entity_type}" in summary_ids
    assert any(i["entity_id"].startswith("api_product.") for i in payload["items"])
    assert any(i["entity_id"].startswith("data_layer_table.") for i in payload["items"])


def test_no_database_writes_occur(client):
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(
        fetchall=MagicMock(return_value=[]),
        fetchone=MagicMock(return_value=None),
    )
    build_entities_response(db)
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_manifest_lists_entity_surface(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "entity_surface" in supported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/entities").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/v1/product/entities" in paths
