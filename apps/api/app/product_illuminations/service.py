"""
PetroGrid Illuminations v0.1 — read-only contextual interpretation from signals and patterns.
No persistence, no ingestion/backfill calls, no database writes beyond upstream reads.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.product_illuminations.rules import (
    CONSERVATIVE_PHRASES,
    FORBIDDEN_PHRASES,
    ILLUMINATION_RULES,
    IlluminationRuleDefinition,
    THRESHOLDS,
)
from app.product_patterns.service import evaluate_patterns
from app.product_signals.service import build_signals_response

SIGNALS_SOURCE = "/v1/product/signals"
PATTERNS_SOURCE = "/v1/product/patterns"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _matching_patterns(
    patterns: list[dict[str, Any]],
    types: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed = set(types)
    return [p for p in patterns if p.get("pattern_type") in allowed]


def _matching_signals(
    signals: list[dict[str, Any]],
    types: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed = set(types)
    return [s for s in signals if s.get("signal_type") in allowed]


def _related_data_products(
    patterns: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> list[str]:
    products: set[str] = set()
    for item in patterns + signals:
        products.update(item.get("related_data_products") or [])
    return sorted(products)


def _resolve_confidence(rule: IlluminationRuleDefinition, *, has_pattern: bool) -> float:
    confidence = rule.base_confidence
    if has_pattern:
        confidence = min(1.0, confidence + THRESHOLDS["pattern_confidence_boost"])
    else:
        confidence = max(0.0, confidence - THRESHOLDS["signal_only_confidence_penalty"])
    return round(confidence, 2)


def _build_evidence(
    rule: IlluminationRuleDefinition,
    *,
    matched_patterns: list[dict[str, Any]],
    matched_signals: list[dict[str, Any]],
    observed_value: str,
) -> dict[str, Any]:
    return {
        "source_pattern_ids": [p["pattern_id"] for p in matched_patterns],
        "source_signal_ids": [s["signal_id"] for s in matched_signals],
        "rule": rule.rule_id,
        "threshold": THRESHOLDS[rule.threshold_key],
        "observed_value": observed_value,
    }


def _build_illumination(
    rule: IlluminationRuleDefinition,
    *,
    matched_patterns: list[dict[str, Any]],
    matched_signals: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    pattern_ids = [p["pattern_id"] for p in matched_patterns]
    signal_ids = sorted(
        {s["signal_id"] for s in matched_signals}
        | {sid for p in matched_patterns for sid in (p.get("related_signals") or [])}
    )
    return {
        "illumination_id": f"{rule.illumination_type}.{rule.rule_id}",
        "illumination_name": rule.illumination_name,
        "illumination_type": rule.illumination_type,
        "summary": rule.summary,
        "interpretation": rule.interpretation,
        "business_implication": rule.business_implication,
        "recommended_attention": rule.recommended_attention,
        "confidence": _resolve_confidence(rule, has_pattern=bool(matched_patterns)),
        "related_patterns": pattern_ids,
        "related_signals": signal_ids,
        "related_data_products": _related_data_products(matched_patterns, matched_signals),
        "evidence": evidence,
        "status": "new",
        "limitations": rule.limitations,
    }


def _observed_value(
    matched_patterns: list[dict[str, Any]],
    matched_signals: list[dict[str, Any]],
) -> str:
    parts = []
    if matched_patterns:
        parts.append(f"patterns={len(matched_patterns)}")
    if matched_signals:
        parts.append(f"signals={len(matched_signals)}")
    return ",".join(parts) if parts else "none"


def _evaluate_rule(
    rule: IlluminationRuleDefinition,
    signals: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    matched_patterns = _matching_patterns(patterns, rule.source_pattern_types)
    matched_signals = _matching_signals(signals, rule.source_signal_types)

    has_pattern = len(matched_patterns) >= THRESHOLDS["minimum_patterns_without_signals"]
    has_signals = len(matched_signals) >= THRESHOLDS["minimum_signals_without_pattern"]

    if not has_pattern and not has_signals:
        return None

    if not matched_patterns and not matched_signals:
        return None

    evidence = _build_evidence(
        rule,
        matched_patterns=matched_patterns,
        matched_signals=matched_signals,
        observed_value=_observed_value(matched_patterns, matched_signals),
    )
    return _build_illumination(
        rule,
        matched_patterns=matched_patterns,
        matched_signals=matched_signals,
        evidence=evidence,
    )


def evaluate_illuminations(
    signals: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply illumination rules to signals and patterns; emit only with evidence."""
    if not signals and not patterns:
        return []

    items: list[dict[str, Any]] = []
    for rule in ILLUMINATION_RULES.values():
        illumination = _evaluate_rule(rule, signals, patterns)
        if illumination is not None:
            items.append(illumination)
    return items


def validate_conservative_language(text: str) -> list[str]:
    """Return forbidden phrases found in text (empty if compliant)."""
    violations: list[str] = []
    lowered = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            violations.append(phrase)
    return violations


def validate_rule_texts() -> list[str]:
    """Validate all rule narrative fields use conservative language."""
    violations: list[str] = []
    fields = ("summary", "interpretation", "business_implication", "recommended_attention")
    for rule in ILLUMINATION_RULES.values():
        for field in fields:
            text = getattr(rule, field)
            found = validate_conservative_language(text)
            if found:
                violations.append(f"{rule.rule_id}.{field}: {found}")
            if not any(phrase in text.lower() for phrase in CONSERVATIVE_PHRASES):
                violations.append(f"{rule.rule_id}.{field}: missing conservative phrase")
    return violations


def build_illuminations_response(db) -> dict[str, Any]:
    """Build GET /v1/product/illuminations payload from signals and patterns."""
    warnings: list[str] = []
    signals_items: list[dict[str, Any]] = []
    patterns_items: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    try:
        signals_payload = build_signals_response(db)
        signals_items = signals_payload.get("items") or []
        if signals_payload.get("metadata", {}).get("warnings"):
            warnings.extend(
                f"Signals: {w}" for w in signals_payload["metadata"]["warnings"]
            )
        patterns_items = evaluate_patterns(signals_items)
        items = evaluate_illuminations(signals_items, patterns_items)
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Illumination evaluation failed: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.illumination_service",
        "generated_at": _utc_now(),
        "notes": (
            "Illuminations are rule-based contextual interpretations derived from "
            "PetroGrid signals and patterns. Not decisions, AI narratives, or forecasts."
        ),
        "signals_source": SIGNALS_SOURCE,
        "patterns_source": PATTERNS_SOURCE,
        "input_signal_count": len(signals_items),
        "input_pattern_count": len(patterns_items),
        "rule_count": len(ILLUMINATION_RULES),
        "thresholds": dict(THRESHOLDS),
        "conservative_phrases": list(CONSERVATIVE_PHRASES),
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "illuminations",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
