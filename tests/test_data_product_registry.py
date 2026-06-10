"""Tests for PetroGrid data product registry (GET /v1/product/data-products)."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402
from app.data_product_registry import (  # noqa: E402
    ALL_KNOWN_PRODUCT_IDS,
    KNOWN_API_PRODUCT_IDS,
    KNOWN_GOLD_PRODUCT_IDS,
    build_data_product_registry,
)

FAKE_PRODUCT_MARKERS = (
    "fake_product",
    "signal_engine",
    "illumination",
    "decision_product",
    "tanna_connector_product",
    "silver.dim_date",
    "silver.fact",
)


@pytest.fixture
def client():
    return TestClient(app)


def test_data_products_endpoint_returns_valid_json(client):
    res = client.get("/v1/product/data-products")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["registry_version"] == "0.1"
    assert data["product_id"] == "petrogrid"


def test_registry_has_three_groups(client):
    data = client.get("/v1/product/data-products").json()
    groups = data["groups"]
    assert set(groups.keys()) == {
        "api_data_products",
        "bronze_data_products",
        "gold_data_products",
    }


def test_no_fake_products_in_registry(client):
    data = client.get("/v1/product/data-products").json()
    all_ids = []
    for group in data["groups"].values():
        for product in group:
            all_ids.append(product["product_id"])
            for marker in FAKE_PRODUCT_MARKERS:
                assert marker not in product["product_id"]
    assert set(all_ids) == ALL_KNOWN_PRODUCT_IDS


def test_silver_not_exposed_as_active_products(client):
    data = client.get("/v1/product/data-products").json()
    excluded = data["excluded_layers"]["silver"]
    assert excluded["active_products_exposed"] is False
    assert excluded["status"] == "not_implemented"
    for group in data["groups"].values():
        for product in group:
            assert not product["product_id"].startswith("silver.")
            assert product["source_layer"] != "silver"


def test_gold_products_table_backed_not_api_backed(client):
    data = client.get("/v1/product/data-products").json()
    gold = data["groups"]["gold_data_products"]
    assert len(gold) == len(KNOWN_GOLD_PRODUCT_IDS)
    for product in gold:
        assert product["gold_backed"] is True
        assert product["table_backed"] is True
        assert product["api_backed"] is False
        assert product["tanna_sync_ready"] is False
        assert product["status"] == "introspection_only"


def test_api_data_products_include_required_catalog(client):
    data = client.get("/v1/product/data-products").json()
    api_ids = {p["product_id"] for p in data["groups"]["api_data_products"]}
    assert api_ids == KNOWN_API_PRODUCT_IDS
    expected = {
        "api.reports",
        "api.coverage",
        "api.highlights",
        "api.refineries",
        "api.consumption",
        "api.fuel_prices",
        "api.gas_infrastructure",
        "api.charts",
        "api.vessels",
        "api.archive",
        "api.data_layers",
    }
    assert expected == api_ids


def test_each_product_has_required_fields(client):
    required = {
        "product_id",
        "product_name",
        "description",
        "domain",
        "source_layer",
        "backing_api",
        "backing_table",
        "freshness_source",
        "quality_source",
        "status",
        "limitations",
        "api_backed",
        "table_backed",
        "gold_backed",
        "tanna_sync_ready",
    }
    data = client.get("/v1/product/data-products").json()
    for group in data["groups"].values():
        for product in group:
            assert required.issubset(product.keys())


def test_existing_apis_still_work(client):
    """Registry addition must not break existing public endpoints or route registration."""
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/data-products").status_code == 200

    openapi = client.get("/openapi.json").json()
    paths = set(openapi.get("paths", {}))
    expected_business_routes = {
        "/v1/reports",
        "/v1/coverage",
        "/v1/highlights",
        "/v1/refineries/status",
        "/v1/consumption/benchmarks",
        "/v1/prices/fuel",
        "/v1/gas/infra",
        "/v1/charts/series",
        "/v1/vessels/clearance",
        "/v1/data-layers/tables",
    }
    assert expected_business_routes.issubset(paths)


def test_build_registry_product_count():
    payload = build_data_product_registry()
    assert len(payload["groups"]["api_data_products"]) == 11
    assert len(payload["groups"]["bronze_data_products"]) == 20
    assert len(payload["groups"]["gold_data_products"]) == 11
