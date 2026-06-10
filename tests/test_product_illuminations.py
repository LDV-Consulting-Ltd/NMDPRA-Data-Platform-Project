"""Tests for PetroGrid Illuminations v0.1 (GET /v1/product/illuminations)."""
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
from app.product_illuminations.rules import (  # noqa: E402
    ALLOWED_ILLUMINATION_TYPES,
    FORBIDDEN_PHRASES,
    ILLUMINATION_RULES,
)
from app.product_illuminations.service import (  # noqa: E402
    build_illuminations_response,
    evaluate_illuminations,
    validate_conservative_language,
    validate_rule_texts,
)

FORBIDDEN_ILLUMINATION_TYPES = (
    "price_anomaly_intelligence",
    "supply_shortage_intelligence",
    "market_intelligence",
    "regulatory_compliance_conclusion",
    "decision_illumination",
    "ai_generated_illumination",
)

REQUIRED_FIELDS = {
    "illumination_id",
    "illumination_name",
    "illumination_type",
    "summary",
    "interpretation",
    "business_implication",
    "recommended_attention",
    "confidence",
    "related_patterns",
    "related_signals",
    "related_data_products",
    "evidence",
    "status",
    "limitations",
}

REQUIRED_EVIDENCE_FIELDS = {
    "source_pattern_ids",
    "source_signal_ids",
    "rule",
    "threshold",
    "observed_value",
}

NARRATIVE_FIELDS = (
    "summary",
    "interpretation",
    "business_implication",
    "recommended_attention",
)


def _sample_signal(signal_id: str, signal_type: str) -> dict:
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "related_data_products": ["api.test"],
        "related_entities": [],
        "detected_at": "2026-06-09T12:00:00Z",
    }


def _sample_pattern(pattern_id: str, pattern_type: str, related_signals: list[str]) -> dict:
    return {
        "pattern_id": pattern_id,
        "pattern_type": pattern_type,
        "related_signals": related_signals,
        "related_data_products": ["api.test"],
    }


@pytest.fixture
def client():
    return TestClient(app)


def test_illuminations_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/illuminations")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["object_type"] == "illuminations"
    assert data["implementation_status"] == "implemented"
    assert data["metadata"]["source"] == "petrogrid.illumination_service"
    assert "Illuminations are rule-based" in data["metadata"]["notes"]


def test_illuminations_derived_from_signals_and_patterns():
    signals = [
        _sample_signal("source_coverage_signal.coverage_empty", "source_coverage_signal"),
        _sample_signal("api_coverage_signal.reports_empty", "api_coverage_signal"),
    ]
    patterns = [
        _sample_pattern(
            "recurring_coverage_gap_pattern.recurring_coverage_gap",
            "recurring_coverage_gap_pattern",
            [s["signal_id"] for s in signals],
        ),
    ]
    items = evaluate_illuminations(signals, patterns)
    assert items
    coverage = next(i for i in items if i["illumination_type"] == "coverage_gap_illumination")
    assert coverage["related_patterns"]
    assert coverage["related_signals"]
    assert coverage["evidence"]["source_signal_ids"]


def test_illuminations_include_evidence(client):
    data = client.get("/v1/product/illuminations").json()
    for item in data["items"]:
        assert REQUIRED_FIELDS.issubset(item.keys())
        assert REQUIRED_EVIDENCE_FIELDS.issubset(item["evidence"].keys())


def test_conservative_language_rules_followed():
    assert validate_rule_texts() == []
    for rule in ILLUMINATION_RULES.values():
        for field in NARRATIVE_FIELDS:
            text = getattr(rule, field)
            assert not validate_conservative_language(text), f"{rule.rule_id}.{field}"


def test_illumination_output_uses_conservative_language(client):
    data = client.get("/v1/product/illuminations").json()
    for item in data["items"]:
        assert item["illumination_type"] in ALLOWED_ILLUMINATION_TYPES
        assert item["illumination_type"] not in FORBIDDEN_ILLUMINATION_TYPES
        for field in NARRATIVE_FIELDS:
            assert not validate_conservative_language(item[field]), f"{item['illumination_id']}.{field}"
        assert 0 <= item["confidence"] <= 1


def test_empty_patterns_and_signals_produce_empty_illuminations():
    assert evaluate_illuminations([], []) == []


def test_signals_only_can_produce_illumination():
    signals = [_sample_signal("dq_failure_signal.dq_failures_count_gt_0", "dq_failure_signal")]
    items = evaluate_illuminations(signals, [])
    types = {i["illumination_type"] for i in items}
    assert "dq_reliability_illumination" in types


def test_unavailable_signal_source_does_not_crash_endpoint():
    with patch(
        "app.product_illuminations.service.build_signals_response",
        side_effect=OperationalError("stmt", {}, Exception("signals unavailable")),
    ):
        payload = build_illuminations_response(MagicMock())
    assert payload["implementation_status"] == "implemented"
    assert payload["items"] == []
    assert "warnings" in payload["metadata"]


def test_no_ingestion_or_backfill_functions_called(client):
    with patch("core.run_pipeline.run_full_pipeline") as mock_full, patch(
        "core.run_pipeline.run_discover"
    ) as mock_discover, patch("core.run_pipeline.run_download") as mock_download:
        res = client.get("/v1/product/illuminations")
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
    build_illuminations_response(db)
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_forbidden_phrases_constant_is_documented():
    for phrase in FORBIDDEN_PHRASES:
        assert phrase in ("proves", "confirms", "will cause", "guarantees", "definitely", "certainly", "must act")


def test_manifest_lists_rule_based_illuminations(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "rule_based_illuminations" in supported
    unsupported = {c["id"] for c in data["unsupported_capabilities"]}
    assert "decision_product_workflow_and_automation" in unsupported
    assert "illumination_persistence_and_advanced_illumination_engine" in unsupported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/signals").status_code == 200
    assert client.get("/v1/product/patterns").status_code == 200
    assert client.get("/v1/product/illuminations").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/v1/product/illuminations" in paths
