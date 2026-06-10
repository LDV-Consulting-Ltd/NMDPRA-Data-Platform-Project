"""Tests for PetroGrid Tanna Connector v0.1 (GET /api/v1/tanna/*)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402
from app.tanna_connector.config import reset_tanna_config_cache  # noqa: E402
from app.tanna_connector.services.status_service import build_tanna_status  # noqa: E402

TANNA_ENDPOINTS = (
    "/api/v1/tanna/manifest",
    "/api/v1/tanna/health",
    "/api/v1/tanna/status",
    "/api/v1/tanna/data-products",
    "/api/v1/tanna/entities",
    "/api/v1/tanna/relationships",
    "/api/v1/tanna/signals",
    "/api/v1/tanna/patterns",
    "/api/v1/tanna/illuminations",
    "/api/v1/tanna/decision-products",
    "/api/v1/tanna/knowledge-assets",
)

ENVELOPE_OBJECT_ENDPOINTS = TANNA_ENDPOINTS[3:]

ENVELOPE_KEYS = {
    "module_id",
    "module_name",
    "object_type",
    "implementation_status",
    "items",
    "metadata",
}

METADATA_KEYS = {
    "source",
    "notes",
    "generated_at",
    "sync_ready",
    "sync_notes",
    "external_id_strategy",
    "duplicate_handling_notes",
}

TEST_TOKEN = "test-tanna-connector-token"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def configure_tanna_token(monkeypatch):
    monkeypatch.setenv("TANNA_CONNECTOR_TOKEN", TEST_TOKEN)
    reset_tanna_config_cache()
    yield
    reset_tanna_config_cache()


def auth_headers(token: str | None = TEST_TOKEN) -> dict[str, str]:
    if token is None:
        return {}
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", TANNA_ENDPOINTS)
def test_tanna_endpoints_require_token(client, path):
    response = client.get(path)
    assert response.status_code == 401


def test_missing_token_returns_401(client):
    response = client.get("/api/v1/tanna/manifest")
    assert response.status_code == 401
    assert "Missing" in response.json()["detail"]


def test_invalid_token_returns_403(client):
    response = client.get("/api/v1/tanna/manifest", headers=auth_headers("wrong-token"))
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid connector token"


@pytest.mark.parametrize("path", TANNA_ENDPOINTS)
def test_valid_token_succeeds(client, path):
    response = client.get(path, headers=auth_headers())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("path", ENVELOPE_OBJECT_ENDPOINTS)
def test_envelope_shape(client, path):
    data = client.get(path, headers=auth_headers()).json()
    assert ENVELOPE_KEYS.issubset(data.keys())
    assert data["module_id"] == "petrogrid"
    assert data["module_name"] == "PetroGrid"
    assert data["implementation_status"] in {
        "implemented",
        "partial",
        "placeholder",
        "not_implemented",
    }
    assert isinstance(data["items"], list)
    assert METADATA_KEYS.issubset(data["metadata"].keys())
    assert data["metadata"]["external_id_strategy"].startswith("petrogrid:")


def test_manifest_envelope(client):
    data = client.get("/api/v1/tanna/manifest", headers=auth_headers()).json()
    assert data["object_type"] == "manifest"
    assert len(data["items"]) > 0
    assert all(item["external_id"].startswith("petrogrid:capability:") for item in data["items"])


def test_status_endpoint_returns_maturity_matrix(client):
    data = client.get("/api/v1/tanna/status", headers=auth_headers()).json()
    required = {
        "connector_version",
        "module_id",
        "module_name",
        "overall_status",
        "endpoint_maturity_matrix",
        "implemented_objects",
        "partial_objects",
        "placeholder_objects",
        "not_implemented_objects",
        "sync_ready_objects",
        "sync_blocked_objects",
        "last_generated_at",
    }
    assert required.issubset(data.keys())
    assert data["module_id"] == "petrogrid"
    assert data["module_name"] == "PetroGrid"
    matrix = data["endpoint_maturity_matrix"]
    for endpoint in (
        "manifest",
        "health",
        "data_products",
        "entities",
        "relationships",
        "signals",
        "patterns",
        "illuminations",
        "decision_products",
        "knowledge_assets",
    ):
        assert endpoint in matrix
        assert "implementation_status" in matrix[endpoint]
        assert "sync_ready" in matrix[endpoint]


def test_sync_ready_rules(client):
    data = client.get("/api/v1/tanna/data-products", headers=auth_headers()).json()
    if data["implementation_status"] == "implemented":
        assert data["metadata"]["sync_ready"] is True
    for item in data["items"]:
        assert item["external_id"].startswith("petrogrid:data_product:")


def test_external_ids_are_stable(client):
    first = client.get("/api/v1/tanna/signals", headers=auth_headers()).json()
    second = client.get("/api/v1/tanna/signals", headers=auth_headers()).json()
    first_ids = [item["external_id"] for item in first["items"]]
    second_ids = [item["external_id"] for item in second["items"]]
    assert first_ids == second_ids
    for external_id in first_ids:
        assert external_id.startswith("petrogrid:signal:")


def test_connector_does_not_write_to_database():
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(
        fetchall=MagicMock(return_value=[]),
        fetchone=MagicMock(return_value=None),
        scalar=MagicMock(return_value=0),
    )
    build_tanna_status(db, api_title="Test API")
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_connector_does_not_trigger_ingestion(client):
    response = client.get("/api/v1/tanna/health", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    checks = {item["check"] for item in data["items"]}
    assert "api_liveness" in checks
    assert "pipeline_status" in checks
    for item in data["items"]:
        detail = item.get("detail") or {}
        assert "backfill" not in str(detail).lower()


def test_existing_product_endpoints_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/data-products").status_code == 200
    assert client.get("/v1/product/relationships").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/api/v1/tanna/manifest" in paths
    assert "/api/v1/tanna/status" in paths
