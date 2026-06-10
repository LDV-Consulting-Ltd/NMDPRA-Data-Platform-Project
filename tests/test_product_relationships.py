"""Tests for PetroGrid Relationships v0.1 (GET /v1/product/relationships)."""
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
from app.product_relationships.rules import (  # noqa: E402
    ALLOWED_RELATIONSHIP_TYPES,
    FORBIDDEN_RELATIONSHIP_TYPES,
    GOLD_FACT_DIMENSION_FKS,
    MIN_CONFIDENCE,
    RELATIONSHIP_GROUPS,
)
from app.product_relationships.service import (  # noqa: E402
    build_relationships_response,
    build_static_relationships,
)

REQUIRED_FIELDS = {
    "relationship_id",
    "relationship_type",
    "source_object_type",
    "source_object_id",
    "target_object_type",
    "target_object_id",
    "description",
    "evidence",
    "confidence",
    "status",
    "limitations",
}

FAKE_RELATIONSHIP_MARKERS = (
    "influences.",
    "causes.",
    "predicts.",
    "recommends.",
    "optimizes.",
    "fake_relationship",
    "neo4j",
    "market_intelligence_link",
)


@pytest.fixture
def client():
    return TestClient(app)


def test_relationships_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/relationships")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["object_type"] == "relationships"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert isinstance(data["groups"], dict)
    assert data["metadata"]["source"] == "petrogrid.relationship_service"
    assert data["metadata"]["min_confidence"] == MIN_CONFIDENCE


def test_relationships_contain_evidence(client):
    data = client.get("/v1/product/relationships").json()
    for item in data["items"]:
        assert REQUIRED_FIELDS.issubset(item.keys())
        assert item["evidence"]
        assert "evidence_type" in item["evidence"] or "migration_file" in item["evidence"]
        assert MIN_CONFIDENCE <= item["confidence"] <= 1.0
        assert item["limitations"]


def test_no_invented_relationship_types(client):
    data = client.get("/v1/product/relationships").json()
    ids = set()
    for item in data["items"]:
        assert item["relationship_type"] in ALLOWED_RELATIONSHIP_TYPES
        assert item["relationship_type"] not in FORBIDDEN_RELATIONSHIP_TYPES
        for marker in FAKE_RELATIONSHIP_MARKERS:
            assert marker not in item["relationship_id"]
        assert item["relationship_id"] not in ids
        ids.add(item["relationship_id"])


def test_relationship_groups_cover_required_categories(client):
    data = client.get("/v1/product/relationships").json()
    groups = data["groups"]
    for group_key in RELATIONSHIP_GROUPS:
        assert group_key in groups
        assert isinstance(groups[group_key], list)

    assert len(groups["data_product_to_api_endpoint"]) > 0
    assert len(groups["gold_fact_to_gold_dimension"]) > 0
    assert len(groups["source_file_to_bronze_table"]) > 0
    assert len(groups["bronze_table_to_gold_table"]) > 0
    assert len(groups["api_endpoint_to_bronze_table"]) > 0


def test_static_relationships_include_gold_fact_dimension_fks():
    static = build_static_relationships()
    static_ids = {r["relationship_id"] for r in static}
    for fk in GOLD_FACT_DIMENSION_FKS:
        assert fk.relationship_id in static_ids


def test_empty_lineage_edges_handled_safely():
    db = MagicMock()
    db.execute.side_effect = ProgrammingError("stmt", {}, Exception("no lineage_edge"))
    payload = build_relationships_response(db)
    assert payload["implementation_status"] == "implemented"
    assert payload["items"]
    assert payload["metadata"]["relationship_count"] == len(payload["items"])
    assert payload["groups"]["lineage_node_to_lineage_node"] == []
    assert "lineage_edges_limitation" in payload["metadata"]


def test_lineage_db_failure_still_returns_static_relationships():
    db = MagicMock()

    def execute_side_effect(stmt, params=None):
        sql = str(stmt)
        if "lineage_edge" in sql:
            raise OperationalError("stmt", {}, Exception("db unavailable"))
        raise ProgrammingError("stmt", {}, Exception("missing"))

    db.execute.side_effect = execute_side_effect
    payload = build_relationships_response(db)
    assert payload["implementation_status"] == "implemented"
    assert len(payload["items"]) >= len(build_static_relationships(db))


def test_no_database_writes_occur(client):
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(
        fetchall=MagicMock(return_value=[]),
        fetchone=MagicMock(return_value=None),
        scalar=MagicMock(return_value=0),
    )
    build_relationships_response(db)
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_manifest_lists_relationship_capabilities(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "relationship_model" in supported
    assert "relationship_surface" in supported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/data-products").status_code == 200
    assert client.get("/v1/product/relationships").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/v1/product/relationships" in paths


def test_entity_to_data_product_relationships_when_entities_available():
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(
        fetchall=MagicMock(return_value=[]),
        fetchone=MagicMock(return_value=None),
        scalar=MagicMock(return_value=0),
    )
    payload = build_relationships_response(db)
    entity_rels = payload["groups"]["entity_to_data_product"]
    assert isinstance(entity_rels, list)
    for rel in entity_rels:
        assert rel["relationship_type"] == "belongs_to"
        assert rel["source_object_type"] == "entity"
        assert rel["target_object_type"] == "data_product"
        assert rel["confidence"] >= MIN_CONFIDENCE
