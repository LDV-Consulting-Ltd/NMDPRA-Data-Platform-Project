"""Tests for PetroGrid Signals v0.1 (GET /v1/product/signals)."""
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
from app.product_signals.rules import ALLOWED_SIGNAL_TYPES, SIGNAL_RULES  # noqa: E402
from app.product_signals.service import (  # noqa: E402
    build_signals_response,
    evaluate_signals,
    gather_evidence,
)

FORBIDDEN_SIGNAL_TYPES = (
    "market_intelligence_signal",
    "supply_shortage_signal",
    "pricing_anomaly_signal",
    "decision_signal",
    "ai_generated_signal",
    "pattern_signal",
    "illumination_signal",
)

REQUIRED_SIGNAL_FIELDS = {
    "signal_id",
    "signal_name",
    "signal_type",
    "description",
    "severity",
    "confidence",
    "detected_at",
    "source_endpoint",
    "source_table",
    "related_data_products",
    "related_entities",
    "evidence",
    "status",
    "limitations",
}

REQUIRED_EVIDENCE_FIELDS = {"source", "field", "observed_value", "rule", "threshold"}


@pytest.fixture
def client():
    return TestClient(app)


def test_signals_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/signals")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["product_name"] == "PetroGrid"
    assert data["object_type"] == "signals"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)
    assert data["metadata"]["source"] == "petrogrid.signal_service"
    assert "generated_at" in data["metadata"]
    assert "Signals are rule-based" in data["metadata"]["notes"]


def test_signals_are_rule_based(client):
    data = client.get("/v1/product/signals").json()
    assert data["metadata"]["rule_count"] == len(SIGNAL_RULES)
    assert "thresholds" in data["metadata"]
    for item in data["items"]:
        assert item["evidence"]["rule"] in SIGNAL_RULES
        assert item["signal_type"] in ALLOWED_SIGNAL_TYPES
        assert item["signal_type"] not in FORBIDDEN_SIGNAL_TYPES


def test_signals_include_evidence(client):
    data = client.get("/v1/product/signals").json()
    for item in data["items"]:
        assert REQUIRED_SIGNAL_FIELDS.issubset(item.keys())
        assert REQUIRED_EVIDENCE_FIELDS.issubset(item["evidence"].keys())
        assert item["evidence"]["source"] == item["source_endpoint"]


def test_signal_confidence_between_zero_and_one(client):
    data = client.get("/v1/product/signals").json()
    for item in data["items"]:
        assert 0 <= item["confidence"] <= 1
    for rule in SIGNAL_RULES.values():
        assert 0 <= rule.confidence <= 1


def test_unavailable_sources_do_not_crash_endpoint(client):
    failing_db = MagicMock()
    failing_db.execute.side_effect = OperationalError("stmt", {}, Exception("db down"))

    payload = build_signals_response(failing_db)
    assert payload["implementation_status"] == "implemented"
    assert isinstance(payload["items"], list)
    assert "warnings" in payload["metadata"]


def test_partial_source_failure_still_returns_signals():
    good_db = MagicMock()

    def execute_side_effect(stmt, params=None):
        sql = str(stmt)
        result = MagicMock()
        if "ingest_run" in sql:
            raise OperationalError("stmt", {}, Exception("ingest unavailable"))
        if "file_registry" in sql:
            result.scalar.return_value = 0
            result.fetchone.return_value = None
            result.fetchall.return_value = []
            return result
        if "pg_class" in sql:
            result.fetchone.return_value = (0,)
            return result
        if "COUNT" in sql:
            result.scalar.return_value = 0
            return result
        result.fetchone.return_value = None
        result.fetchall.return_value = []
        result.scalar.return_value = 0
        return result

    good_db.execute.side_effect = execute_side_effect
    evidence, warnings = gather_evidence(good_db)
    assert warnings
    payload = build_signals_response(good_db)
    assert payload["implementation_status"] == "implemented"


def test_no_ingestion_or_backfill_functions_called(client):
    with patch("core.run_pipeline.run_full_pipeline") as mock_full, patch(
        "core.run_pipeline.run_discover"
    ) as mock_discover, patch("core.run_pipeline.run_download") as mock_download:
        res = client.get("/v1/product/signals")
        assert res.status_code == 200
        mock_full.assert_not_called()
        mock_discover.assert_not_called()
        mock_download.assert_not_called()


def test_no_database_writes_occur():
    db = MagicMock()
    db.execute.side_effect = lambda stmt, params=None: MagicMock(
        scalar=MagicMock(return_value=0),
        fetchone=MagicMock(return_value=None),
        fetchall=MagicMock(return_value=[]),
    )

    build_signals_response(db)

    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
        assert "CREATE" not in sql
        assert "DROP" not in sql
    db.commit.assert_not_called()


def test_evaluate_signals_requires_evidence():
    """Signals are not emitted when supporting evidence is missing."""
    items = evaluate_signals({})
    assert items == []


def test_evaluate_signals_emits_data_ready_false_signal():
    evidence = {
        "pipeline_status": {"data_ready": False, "status": "success"},
    }
    items = evaluate_signals(evidence)
    ids = {item["signal_id"] for item in items}
    assert "data_readiness_signal.data_ready_false" in ids
    signal = next(i for i in items if i["signal_id"] == "data_readiness_signal.data_ready_false")
    assert signal["evidence"]["observed_value"] is False


def test_manifest_lists_rule_based_signals(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "rule_based_signals" in supported
    assert "rule_based_patterns" in supported
    assert "rule_based_illuminations" in supported
    assert "rule_based_decision_products" in supported
    unsupported = {c["id"] for c in data["unsupported_capabilities"]}
    assert "pattern_persistence_and_advanced_pattern_engine" in unsupported
    assert "illumination_persistence_and_advanced_illumination_engine" in unsupported
    assert "decision_product_workflow_and_automation" in unsupported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/data-products").status_code == 200
    assert client.get("/v1/product/signals").status_code == 200

    openapi = client.get("/openapi.json").json()
    paths = set(openapi.get("paths", {}))
    assert "/v1/product/signals" in paths
    assert "/v1/coverage" in paths
