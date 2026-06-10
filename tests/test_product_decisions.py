"""Tests for PetroGrid Decision Products v0.1 (GET /v1/product/decision-products)."""
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
from app.product_decisions.rules import (  # noqa: E402
    ALLOWED_DECISION_TYPES,
    DECISION_RULES,
    FORBIDDEN_DECISION_PHRASES,
)
from app.product_decisions.service import (  # noqa: E402
    build_decision_products_response,
    evaluate_decision_products,
    validate_review_language,
    validate_rule_texts,
)

FORBIDDEN_DECISION_TYPES = (
    "pricing_decision",
    "supply_allocation_decision",
    "market_intervention_decision",
    "regulatory_enforcement_decision",
    "investment_decision",
    "ai_recommendation",
)

REQUIRED_FIELDS = {
    "decision_product_id",
    "decision_product_name",
    "decision_type",
    "description",
    "supported_decision",
    "business_context",
    "decision_owner_role",
    "related_illuminations",
    "related_patterns",
    "related_signals",
    "related_data_products",
    "evidence",
    "decision_status",
    "limitations",
    "placeholder",
}

REQUIRED_EVIDENCE_FIELDS = {
    "source_illumination_ids",
    "source_pattern_ids",
    "source_signal_ids",
    "rule",
    "decision_area",
    "placeholder",
}

NARRATIVE_FIELDS = ("description", "supported_decision", "business_context", "limitations")

AUTOMATED_DECISION_MARKERS = (
    "decision_outcome",
    "approved",
    "rejected",
    "auto_execute",
    "enforcement_action",
)


def _sample_signal(signal_id: str, signal_type: str) -> dict:
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "related_data_products": ["api.test"],
    }


def _sample_pattern(pattern_id: str, pattern_type: str, related_signals: list[str]) -> dict:
    return {
        "pattern_id": pattern_id,
        "pattern_type": pattern_type,
        "related_signals": related_signals,
        "related_data_products": ["api.test"],
    }


def _sample_illumination(illumination_id: str, illumination_type: str) -> dict:
    return {
        "illumination_id": illumination_id,
        "illumination_type": illumination_type,
        "related_signals": ["signal.a"],
        "related_patterns": ["pattern.a"],
        "related_data_products": ["api.test"],
    }


@pytest.fixture
def client():
    return TestClient(app)


def test_decision_products_endpoint_returns_valid_response(client):
    res = client.get("/v1/product/decision-products")
    assert res.status_code == 200
    data = res.json()
    json.dumps(data)
    assert data["product_id"] == "petrogrid"
    assert data["object_type"] == "decision_products"
    assert data["implementation_status"] == "implemented"
    assert data["metadata"]["source"] == "petrogrid.decision_product_service"
    assert "Decision products are rule-based" in data["metadata"]["notes"]


def test_decision_products_derived_from_illuminations_signals_patterns():
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
    illuminations = [
        _sample_illumination(
            "coverage_gap_illumination.coverage_gap_illumination",
            "coverage_gap_illumination",
        ),
    ]
    items = evaluate_decision_products(signals, patterns, illuminations)
    coverage = next(i for i in items if i["decision_type"] == "coverage_gap_review")
    assert coverage["placeholder"] is False
    assert coverage["related_illuminations"]
    assert coverage["evidence"]["source_signal_ids"]


def test_decision_products_include_evidence(client):
    data = client.get("/v1/product/decision-products").json()
    for item in data["items"]:
        assert REQUIRED_FIELDS.issubset(item.keys())
        assert REQUIRED_EVIDENCE_FIELDS.issubset(item["evidence"].keys())
        assert item["decision_status"] == "draft"


def test_review_oriented_language_rules_followed():
    assert validate_rule_texts() == []
    for rule in DECISION_RULES.values():
        for field in NARRATIVE_FIELDS + ("shell_limitations",):
            text = getattr(rule, field)
            assert not validate_review_language(text), f"{rule.rule_id}.{field}"


def test_no_automated_decisions_generated(client):
    data = client.get("/v1/product/decision-products").json()
    for item in data["items"]:
        assert item["decision_type"] in ALLOWED_DECISION_TYPES
        assert item["decision_type"] not in FORBIDDEN_DECISION_TYPES
        assert "decision_outcome" not in item
        serialized = json.dumps(item).lower()
        for field in NARRATIVE_FIELDS:
            assert not validate_review_language(item[field])
        assert "should approve" not in serialized
        assert "should reject" not in serialized
        assert "must enforce" not in serialized


def test_empty_illuminations_produce_placeholder_shells():
    signals = [_sample_signal("dq_failure_signal.dq_failures_count_gt_0", "dq_failure_signal")]
    items = evaluate_decision_products(signals, [], [])
    dq = next(i for i in items if i["decision_type"] == "dq_remediation_review")
    assert dq["placeholder"] is True
    assert dq["related_illuminations"] == []


def test_empty_inputs_produce_empty_decision_products():
    assert evaluate_decision_products([], [], []) == []


def test_unavailable_upstream_does_not_crash_endpoint():
    with patch(
        "app.product_decisions.service.build_signals_response",
        side_effect=OperationalError("stmt", {}, Exception("upstream unavailable")),
    ):
        payload = build_decision_products_response(MagicMock())
    assert payload["implementation_status"] == "implemented"
    assert payload["items"] == []
    assert "warnings" in payload["metadata"]


def test_no_ingestion_or_backfill_functions_called(client):
    with patch("core.run_pipeline.run_full_pipeline") as mock_full, patch(
        "core.run_pipeline.run_discover"
    ) as mock_discover, patch("core.run_pipeline.run_download") as mock_download:
        res = client.get("/v1/product/decision-products")
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
    build_decision_products_response(db)
    for call in db.execute.call_args_list:
        sql = str(call.args[0]).upper()
        assert "INSERT" not in sql
        assert "UPDATE" not in sql
        assert "DELETE" not in sql
    db.commit.assert_not_called()


def test_manifest_lists_rule_based_decision_products(client):
    data = client.get("/v1/product/manifest").json()
    supported = {c["id"] for c in data["supported_capabilities"]}
    assert "rule_based_decision_products" in supported
    unsupported = {c["id"] for c in data["unsupported_capabilities"]}
    assert "decision_product_workflow_and_automation" in unsupported


def test_existing_apis_still_work(client):
    assert client.get("/health").status_code == 200
    assert client.get("/v1/product/signals").status_code == 200
    assert client.get("/v1/product/patterns").status_code == 200
    assert client.get("/v1/product/illuminations").status_code == 200
    assert client.get("/v1/product/decision-products").status_code == 200
    paths = set(client.get("/openapi.json").json().get("paths", {}))
    assert "/v1/product/decision-products" in paths


def test_forbidden_phrases_documented():
    assert "should approve" in FORBIDDEN_DECISION_PHRASES
    assert "guarantees" in FORBIDDEN_DECISION_PHRASES
