"""Tests for PetroGrid product manifest (GET /v1/product/manifest)."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402
from app.product_manifest import build_product_manifest  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_manifest_endpoint_returns_200(client):
    res = client.get("/v1/product/manifest")
    assert res.status_code == 200


def test_manifest_core_identity_fields(client):
    data = client.get("/v1/product/manifest").json()
    assert data["product_id"] == "petrogrid"
    assert data["product_name"] == "PetroGrid"
    assert data["legacy_branding"] == "PetroSight / NMDPRA Data Platform"
    assert data["product_category"] == "Downstream Petroleum Intelligence"
    assert data["owner"] == "LDV"
    assert "NMDPRA Downstream Regulatory Intelligence API" in data["api_title"]


def test_manifest_required_top_level_keys(client):
    data = client.get("/v1/product/manifest").json()
    required = {
        "product_id",
        "product_name",
        "legacy_branding",
        "product_category",
        "owner",
        "api_title",
        "available_api_groups",
        "available_data_layers",
        "supported_domains",
        "supported_capabilities",
        "unsupported_capabilities",
        "current_limitations",
        "generated_at",
    }
    assert required.issubset(data.keys())


def test_manifest_supported_capabilities_are_factual(client):
    data = client.get("/v1/product/manifest").json()
    ids = {c["id"] for c in data["supported_capabilities"]}
    assert "api_liveness" in ids
    assert "business_apis" in ids
    assert "bronze_data_products" in ids
    assert "rule_based_signals" in ids
    assert "rule_based_patterns" in ids
    assert "rule_based_illuminations" in ids
    assert "rule_based_decision_products" in ids
    assert "relationship_model" in ids
    assert "relationship_surface" in ids
    assert "entity_surface" in ids
    assert "knowledge_asset_surface" in ids


def test_manifest_unsupported_capabilities_explicit(client):
    data = client.get("/v1/product/manifest").json()
    unsupported_ids = {c["id"] for c in data["unsupported_capabilities"]}
    assert unsupported_ids == {
        "signal_persistence_and_advanced_signal_engine",
        "pattern_persistence_and_advanced_pattern_engine",
        "illumination_persistence_and_advanced_illumination_engine",
        "decision_product_workflow_and_automation",
        "tanna_connector",
    }


def test_manifest_silver_layer_not_implemented(client):
    data = client.get("/v1/product/manifest").json()
    silver = next(l for l in data["available_data_layers"] if l["layer"] == "silver")
    assert silver["status"] == "not_implemented"


def test_build_product_manifest_generated_at_utc():
    payload = build_product_manifest(api_title="Test API")
    assert payload["generated_at"].endswith("Z")


def test_manifest_does_not_require_auth(client):
    res = client.get("/v1/product/manifest")
    assert res.status_code == 200
    assert "error" not in res.json()
