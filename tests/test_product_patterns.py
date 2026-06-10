"""Tests for PetroGrid Patterns v0.1 (GET /v1/product/patterns)."""
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
from app.product_patterns.rules import ALLOWED_PATTERN_TYPES, PATTERN_RULES  # noqa: E402
from app.product_patterns.service import (  # noqa: E402
    build_patterns_response,
    evaluate_patterns,
)

FORBIDDEN_PATTERN_TYPES = (
    "pricing_anomaly_pattern",
    "supply_shortage_pattern",
    "depot_risk_pattern",
    "market_movement_pattern",
    "regulatory_compliance_pattern",
    "decision_pattern",
    "ai_generated_pattern",
    "illumination_pattern",
)

REQUIRED_PATTERN_FIELDS = {
    "pattern_id",
    "pattern_name",
    "pattern_type",
    "description",
    "evidence_summary",
    "confidence",
    "detected_period_start",
    "detected_period_end",
    "related_signals",
    "related_data_products",
    "related_entities",
    "evidence",
    "status",
    "limitations",
}

REQUIRED_EVIDENCE_FIELDS = {
    "rule",
    "threshold",
    "observed_signal_count",
    "source_signal_ids",
    "signal_types",
}


def _sample_signal(
    signal_id: str,
    signal_type: str,
    *,
    severity: str = "medium",
    products: list[str] | None = None,
    entities: list[str] | None = None,
) -> dict:
    return {
        "signal_id": signal_id,
        "signal_name": signal_id,
        "signal_type": signal_type,
        "description": "test",
        "severity": severity,
        "confidence": 0.9,
        "detected_at": "2026-06-09T12:00:00Z",
        "source_endpoint": "/v1/test",
        "source_table": "bronze.test",
        "related_data_products": products or ["api.test"],
        "related_entities": entities or [],
        "evidence": {"rule": "test", "field": "x", "observed_value": 0, "threshold": 0},
        "status": "new",
        "limitations": "test",
    }


@pytest.fixture
def client():
    return TestClient(app)


def test_patterns_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/patterns")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["product_name"] == "PetroGrid"
    assert data["object_type"] == "patterns"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)
    assert data["metadata"]["source"] == "petrogrid.pattern_service"
    assert "generated_at" in data["metadata"]
    assert "Patterns are rule-based" in data["metadata"]["notes"]
    assert data["metadata"]["signals_source"] == "/v1/product/signals"


def test_patterns_are_derived_from_signals():
    signals = [
        _sample_signal("pipeline_status_signal.pipeline_status_failed", "pipeline_status_signal", severity="critical"),
        _sample_signal("data_readiness_signal.data_ready_false", "data_readiness_signal", severity="high"),
        _sample_signal("source_coverage_signal.coverage_empty", "source_coverage_signal"),
        _sample_signal("api_coverage_signal.reports_empty", "api_coverage_signal"),
    ]
    patterns = evaluate_patterns(signals)
    assert patterns
    for pattern in patterns:
        assert pattern["pattern_type"] in ALLOWED_PATTERN_TYPES
        assert pattern["pattern_type"] not in FORBIDDEN_PATTERN_TYPES
        assert pattern["evidence"]["source_signal_ids"]
        assert all(sid in {s["signal_id"] for s in signals} for sid in pattern["related_signals"])


def test_patterns_include_evidence(client):
    data = client.get("/v1/product/patterns").json()
    for item in data["items"]:
        assert REQUIRED_PATTERN_FIELDS.issubset(item.keys())
        assert REQUIRED_EVIDENCE_FIELDS.issubset(item["evidence"].keys())


def test_pattern_confidence_between_zero_and_one(client):
    data = client.get("/v1/product/patterns").json()
    for item in data["items"]:
        assert 0 <= item["confidence"] <= 1
    for rule in PATTERN_RULES.values():
        assert 0 <= rule.confidence <= 1


def test_empty_signals_produce_empty_patterns():
    assert evaluate_patterns([]) == []


def test_unavailable_signal_source_does_not_crash_endpoint():
    with patch(
        "app.product_patterns.service.build_signals_response",
        side_effect=OperationalError("stmt", {}, Exception("signals unavailable")),
    ):
        db = MagicMock()
        payload = build_patterns_response(db)
    assert payload["implementation_status"] == "implemented"
    assert payload["items"] == []
    assert "warnings" in payload["metadata"]


def test_no_ingestion_or_backfill_functions_called(client):
    with patch("core.run_pipeline.run_full_pipeline") as mock_full, patch(
        "core.run_pipeline.run_discover"
    ) as mock_discover, patch("core.run_pipeline.run_download") as mock_download:
        res = client.get("/v1/product/patterns")
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

    build_patterns_response(db)

    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
        assert "CREATE" not in sql
        assert "DROP" not in sql
    db.commit.assert_not_called()


def test_evaluate_recurring_coverage_gap_pattern():
    signals = [
        _sample_signal("source_coverage_signal.coverage_empty", "source_coverage_signal"),
        _sample_signal("api_coverage_signal.reports_empty", "api_coverage_signal"),
    ]
    patterns = evaluate_patterns(signals)
    ids = {p["pattern_id"] for p in patterns}
    assert "recurring_coverage_gap_pattern.recurring_coverage_gap" in ids


def test_evaluate_recurring_business_dataset_gap_pattern():
    signals = [
        _sample_signal("fuel_price_availability_signal.fuel_prices_empty", "fuel_price_availability_signal"),
        _sample_signal(
            "refinery_status_availability_signal.refinery_status_empty",
            "refinery_status_availability_signal",
        ),
    ]
    patterns = evaluate_patterns(signals)
    ids = {p["pattern_id"] for p in patterns}
    assert "recurring_business_dataset_gap_pattern.recurring_business_dataset_gap" in ids


def test_manifest_lists_rule_based_patterns(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "rule_based_patterns" in supported
    unsupported = {c["id"] for c in data["unsupported_capabilities"]}
    assert "illumination_persistence_and_advanced_illumination_engine" in unsupported
    assert "decision_product_workflow_and_automation" in unsupported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/manifest").status_code == 200
    assert client.get("/v1/product/signals").status_code == 200
    assert client.get("/v1/product/patterns").status_code == 200

    openapi = client.get("/openapi.json").json()
    paths = set(openapi.get("paths", {}))
    assert "/v1/product/patterns" in paths
    assert "/v1/product/signals" in paths
