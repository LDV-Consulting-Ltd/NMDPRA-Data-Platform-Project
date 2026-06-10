"""
PetroGrid Patterns v0.1 — read-only pattern detection from PetroGrid Signals v0.1.
No persistence, no ingestion/backfill calls, no database writes beyond signal reads.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.product_patterns.rules import (
    HIGH_SEVERITIES,
    PATTERN_RULES,
    PatternRuleDefinition,
    THRESHOLDS,
)
from app.product_signals.service import build_signals_response

SIGNALS_SOURCE = "/v1/product/signals"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_detected_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _period_from_signals(signals: list[dict[str, Any]]) -> tuple[str, str]:
    timestamps = [_parse_detected_at(s["detected_at"]) for s in signals if s.get("detected_at")]
    if not timestamps:
        now = _utc_now()
        return now, now
    start = min(timestamps).isoformat().replace("+00:00", "Z")
    end = max(timestamps).isoformat().replace("+00:00", "Z")
    return start, end


def _related_data_products(signals: list[dict[str, Any]]) -> list[str]:
    products: set[str] = set()
    for signal in signals:
        products.update(signal.get("related_data_products") or [])
    return sorted(products)


def _related_entities(signals: list[dict[str, Any]]) -> list[str]:
    entities: set[str] = set()
    for signal in signals:
        entities.update(signal.get("related_entities") or [])
    return sorted(entities)


def _signals_matching_types(
    signals: list[dict[str, Any]],
    types: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed = set(types)
    return [s for s in signals if s.get("signal_type") in allowed]


def _distinct_signal_types(signals: list[dict[str, Any]]) -> list[str]:
    return sorted({s["signal_type"] for s in signals if s.get("signal_type")})


def _high_severity_count(signals: list[dict[str, Any]]) -> int:
    return sum(1 for s in signals if s.get("severity") in HIGH_SEVERITIES)


def _build_evidence(
    *,
    rule: PatternRuleDefinition,
    matched_signals: list[dict[str, Any]],
    cluster_signals: list[dict[str, Any]],
    threshold: Any,
    rule_name: str,
) -> dict[str, Any]:
    return {
        "rule": rule_name,
        "threshold": threshold,
        "observed_signal_count": len(matched_signals),
        "cluster_signal_count": len(cluster_signals),
        "source_signal_ids": [s["signal_id"] for s in cluster_signals],
        "signal_types": _distinct_signal_types(cluster_signals),
        "high_severity_signal_count": _high_severity_count(cluster_signals),
    }


def _build_pattern(
    rule: PatternRuleDefinition,
    *,
    matched_signals: list[dict[str, Any]],
    cluster_signals: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    type_count = len(_distinct_signal_types(matched_signals))
    period_start, period_end = _period_from_signals(cluster_signals)
    return {
        "pattern_id": f"{rule.pattern_type}.{rule.rule_id}",
        "pattern_name": rule.pattern_name,
        "pattern_type": rule.pattern_type,
        "description": rule.description,
        "evidence_summary": rule.evidence_summary_template.format(
            count=len(matched_signals),
            type_count=type_count,
        ),
        "confidence": rule.confidence,
        "detected_period_start": period_start,
        "detected_period_end": period_end,
        "related_signals": [s["signal_id"] for s in cluster_signals],
        "related_data_products": _related_data_products(cluster_signals),
        "related_entities": _related_entities(cluster_signals),
        "evidence": evidence,
        "status": "new",
        "limitations": rule.limitations,
    }


def _evaluate_matching_types_rule(
    rule: PatternRuleDefinition,
    signals: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    threshold = THRESHOLDS[rule.threshold_key]
    matched = _signals_matching_types(signals, rule.matching_signal_types)
    if len(matched) < threshold:
        return None
    distinct_types = _distinct_signal_types(matched)
    if len(distinct_types) < THRESHOLDS["minimum_signal_types_for_cluster"]:
        return None
    evidence = _build_evidence(
        rule=rule,
        matched_signals=matched,
        cluster_signals=matched,
        threshold=threshold,
        rule_name=rule.cluster_rule,
    )
    return _build_pattern(rule, matched_signals=matched, cluster_signals=matched, evidence=evidence)


def _evaluate_anchor_cluster_rule(
    rule: PatternRuleDefinition,
    signals: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    threshold = THRESHOLDS[rule.threshold_key]
    anchors = _signals_matching_types(signals, rule.matching_signal_types)
    if not anchors:
        return None
    anchor_ids = {s["signal_id"] for s in anchors}
    cluster = list(signals)
    if len(cluster) < threshold:
        return None
    if len(_distinct_signal_types(cluster)) < THRESHOLDS["minimum_signal_types_for_cluster"]:
        return None
    evidence = _build_evidence(
        rule=rule,
        matched_signals=anchors,
        cluster_signals=cluster,
        threshold=threshold,
        rule_name=rule.cluster_rule,
    )
    evidence["anchor_signal_ids"] = sorted(anchor_ids)
    return _build_pattern(
        rule,
        matched_signals=anchors,
        cluster_signals=cluster,
        evidence=evidence,
    )


def evaluate_patterns(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply pattern rules to signal items; only emit patterns with supporting evidence."""
    if not signals:
        return []

    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for rule_id, rule in PATTERN_RULES.items():
        if rule.cluster_rule == "matching_signal_types":
            pattern = _evaluate_matching_types_rule(rule, signals)
        elif rule.cluster_rule == "anchor_with_cluster":
            pattern = _evaluate_anchor_cluster_rule(rule, signals)
        else:
            continue
        if pattern is not None and pattern["pattern_id"] not in seen_ids:
            items.append(pattern)
            seen_ids.add(pattern["pattern_id"])

    return items


def build_patterns_response(db) -> dict[str, Any]:
    """Build GET /v1/product/patterns payload from PetroGrid Signals v0.1."""
    warnings: list[str] = []
    signals_items: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    try:
        signals_payload = build_signals_response(db)
        signals_items = signals_payload.get("items") or []
        if signals_payload.get("metadata", {}).get("warnings"):
            warnings.extend(
                f"Signals: {w}" for w in signals_payload["metadata"]["warnings"]
            )
        items = evaluate_patterns(signals_items)
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Pattern evaluation failed: {exc}")

    metadata: dict[str, Any] = {
        "source": "petrogrid.pattern_service",
        "generated_at": _utc_now(),
        "notes": "Patterns are rule-based and derived from PetroGrid signals.",
        "signals_source": SIGNALS_SOURCE,
        "input_signal_count": len(signals_items),
        "rule_count": len(PATTERN_RULES),
        "thresholds": dict(THRESHOLDS),
    }
    if warnings:
        metadata["warnings"] = warnings

    return {
        "product_id": "petrogrid",
        "product_name": "PetroGrid",
        "object_type": "patterns",
        "implementation_status": "implemented",
        "items": items,
        "metadata": metadata,
    }
