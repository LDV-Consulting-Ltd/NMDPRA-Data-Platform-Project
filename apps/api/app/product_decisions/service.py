"""
PetroGrid Decision Products v0.1 — read-only decision-support objects from
signals, patterns, and illuminations. No automated decisions or persistence.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.product_decisions.rules import (
    DECISION_RULES,
    DECISION_STATUS_V01,
    DecisionProductRuleDefinition,
    FORBIDDEN_DECISION_PHRASES,
    REVIEW_PHRASES,
    THRESHOLDS,
)
from app.product_illuminations.service import evaluate_illuminations
from app.product_patterns.service import evaluate_patterns
from app.product_signals.service import build_signals_response

SIGNALS_SOURCE = "/v1/product/signals"
PATTERNS_SOURCE = "/v1/product/patterns"
ILLUMINATIONS_SOURCE = "/v1/product/illuminations"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _filter_by_type(items: list[dict[str, Any]], field: str, types: tuple[str, ...]) -> list[dict[str, Any]]:
    allowed = set(types)
    return [item for item in items if item.get(field) in allowed]


def _collect_ids(items: list[dict[str, Any]], id_field: str) -> list[str]:
    return [item[id_field] for item in items if item.get(id_field)]


def _merge_related_ids(*id_lists: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for ids in id_lists:
        for item_id in ids:
            if item_id not in seen:
                seen.add(item_id)
                merged.append(item_id)
    return merged


def _related_data_products(
    rule: DecisionProductRuleDefinition,
    illuminations: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> list[str]:
    products = set(rule.related_data_products)
    for item in illuminations + patterns + signals:
        products.update(item.get("related_data_products") or [])
    return sorted(products)


def _build_evidence(
    rule: DecisionProductRuleDefinition,
    *,
    illuminations: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    placeholder: bool,
) -> dict[str, Any]:
    return {
        "source_illumination_ids": _collect_ids(illuminations, "illumination_id"),
        "source_pattern_ids": _collect_ids(patterns, "pattern_id"),
        "source_signal_ids": _collect_ids(signals, "signal_id"),
        "rule": rule.rule_id,
        "decision_area": rule.decision_area,
        "placeholder": placeholder,
    }


def _build_decision_product(
    rule: DecisionProductRuleDefinition,
    *,
    illuminations: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    placeholder: bool,
) -> dict[str, Any]:
    evidence = _build_evidence(
        rule,
        illuminations=illuminations,
        patterns=patterns,
        signals=signals,
        placeholder=placeholder,
    )
    limitations = rule.shell_limitations if placeholder else rule.limitations
    return {
        "decision_product_id": f"{rule.decision_type}.{rule.rule_id}",
        "decision_product_name": rule.decision_product_name,
        "decision_type": rule.decision_type,
        "description": rule.description,
        "supported_decision": rule.supported_decision,
        "business_context": rule.business_context,
        "decision_owner_role": rule.decision_owner_role,
        "related_illuminations": _collect_ids(illuminations, "illumination_id"),
        "related_patterns": _merge_related_ids(
            _collect_ids(patterns, "pattern_id"),
            *[i.get("related_patterns") or [] for i in illuminations],
        ),
        "related_signals": _merge_related_ids(
            _collect_ids(signals, "signal_id"),
            *[i.get("related_signals") or [] for i in illuminations],
            *[p.get("related_signals") or [] for p in patterns],
        ),
        "related_data_products": _related_data_products(rule, illuminations, patterns, signals),
        "evidence": evidence,
        "decision_status": DECISION_STATUS_V01,
        "limitations": limitations,
        "placeholder": placeholder,
    }


def _evaluate_rule(
    rule: DecisionProductRuleDefinition,
    signals: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    illuminations: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    matched_illuminations = _filter_by_type(
        illuminations, "illumination_type", rule.source_illumination_types
    )
    matched_patterns = _filter_by_type(patterns, "pattern_type", rule.source_pattern_types)
    matched_signals = _filter_by_type(signals, "signal_type", rule.source_signal_types)

    if matched_illuminations:
        return _build_decision_product(
            rule,
            illuminations=matched_illuminations,
            patterns=matched_patterns,
            signals=matched_signals,
            placeholder=False,
        )

    has_shell_evidence = (
        len(matched_patterns) >= THRESHOLDS["minimum_patterns_for_shell"]
        or len(matched_signals) >= THRESHOLDS["minimum_signals_for_shell"]
    )
    if has_shell_evidence and (matched_patterns or matched_signals):
        return _build_decision_product(
            rule,
            illuminations=[],
            patterns=matched_patterns,
            signals=matched_signals,
            placeholder=True,
        )

    return None


def evaluate_decision_products(
    signals: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    illuminations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply decision rules; emit only products with supporting evidence."""
    if not signals and not patterns and not illuminations:
        return []

    items: list[dict[str, Any]] = []
    for rule in DECISION_RULES.values():
        product = _evaluate_rule(rule, signals, patterns, illuminations)
        if product is not None:
            items.append(product)
    return items


def validate_review_language(text: str) -> list[str]:
    """Return forbidden decision phrases found in text."""
    violations: list[str] = []
    lowered = text.lower()
    for phrase in FORBIDDEN_DECISION_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            violations.append(phrase)
    return violations


def validate_rule_texts() -> list[str]:
    """Validate narrative fields use review-oriented language."""
    violations: list[str] = []
    fields = ("description", "supported_decision", "business_context", "limitations", "shell_limitations")
    for rule in DECISION_RULES.values():
        for field in fields:
            text = getattr(rule, field)
            found = validate_review_language(text)
            if found:
                violations.append(f"{rule.rule_id}.{field}: {found}")
            if not any(phrase in text.lower() for phrase in REVIEW_PHRASES):
                violations.append(f"{rule.rule_id}.{field}: missing review phrase")
    return violations


def build_decision_products_response(db) -> dict[str, Any]:
    """Build GET /v1/product/decision-products payload."""
    warnings: list[str] = []
    signals_items: list[dict[str, Any]] = []
    patterns_items: list[dict[str, Any]] = []
    illuminations_items: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    try:
        signals_payload = build_signals_response(db)
        signals_items = signals_payload.get("items") or []
        if signals_payload.get("metadata", {}).get("warnings"):
            warnings.extend(f"Signals: {w}" for w in signals_payload["metadata"]["warnings"])

        patterns_items = evaluate_patterns(signals_items)
        illuminations_items = evaluate_illuminations(signals_items, patterns_items)
        items = evaluate_decision_products(signals_items, patterns_items, illuminations_items)
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Decision product evaluation failed: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.decision_product_service",
        "generated_at": _utc_now(),
        "notes": (
            "Decision products are rule-based decision-support objects derived from "
            "PetroGrid signals, patterns, and illuminations. Not automated decisions, "
            "approvals, or AI recommendations."
        ),
        "signals_source": SIGNALS_SOURCE,
        "patterns_source": PATTERNS_SOURCE,
        "illuminations_source": ILLUMINATIONS_SOURCE,
        "input_signal_count": len(signals_items),
        "input_pattern_count": len(patterns_items),
        "input_illumination_count": len(illuminations_items),
        "rule_count": len(DECISION_RULES),
        "thresholds": dict(THRESHOLDS),
        "review_phrases": list(REVIEW_PHRASES),
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "decision_products",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
