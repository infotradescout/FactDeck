from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.schemas import DecisionCase


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _priority_from_score(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def _status_from_confidence(confidence: float, contradiction_risk: float) -> str:
    if contradiction_risk >= 0.6:
        return "disputed"
    if confidence >= 0.72:
        return "confirmed"
    return "provisional"


def _hash_item(item: dict[str, Any]) -> str:
    stable = {k: v for k, v in item.items() if k not in {"generated_at", "item_fingerprint"}}
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _source_quality(conf: float, source_count: int) -> str:
    if conf >= 0.72 and source_count >= 3:
        return "strong"
    if conf >= 0.62:
        return "moderate"
    return "weak"


def _fact_signal(
    *,
    case: DecisionCase,
    generated_at: str,
    lane: str,
    option: dict[str, Any],
) -> dict[str, Any]:
    contradiction_risk = round(min(1.0, (option["risk_score"] + option["uncertainty_score"]) / 180.0), 3)
    status = _status_from_confidence(option["confidence"], contradiction_risk)
    item = {
        "item_id": f"factsignal:{case.case_id}:{option['option_id']}",
        "object_type": "FactSignal",
        "source_system": "factdeck",
        "source_type": "fact",
        "generated_at": generated_at,
        "lane": lane,
        "entity": option["candidate_entity"],
        "topic": case.domain,
        "claim": (
            f"{option['candidate_entity']} in {option['geography']} is "
            f"'{option['decision_label']}' for {case.outcome_spec.target_label_name}."
        ),
        "normalized_fact": {
            "option_id": option["option_id"],
            "final_score": option["final_score"],
            "risk_score": option["risk_score"],
            "confidence": option["confidence"],
            "decision_label": option["decision_label"],
        },
        "fact_type": "evidence_backed_assertion",
        "confidence": option["confidence"],
        "freshness": "fresh",
        "source_count": len(case.raw_evidence_sources),
        "evidence_refs": list(case.raw_evidence_sources),
        "contradiction_risk": contradiction_risk,
        "status": status,
        "tags": [case.domain, "viability", option["geography"]],
    }
    item["item_fingerprint"] = _hash_item(item)
    return item


def _evidence_packet(
    *,
    case: DecisionCase,
    generated_at: str,
    option: dict[str, Any],
) -> dict[str, Any]:
    source_count = len(case.raw_evidence_sources)
    item = {
        "item_id": f"evidence:{case.case_id}:{option['option_id']}",
        "object_type": "EvidencePacket",
        "packet_id": f"packet:{case.case_id}:{option['option_id']}",
        "entity": option["candidate_entity"],
        "topic": case.domain,
        "supporting_claims": [d["driver"] for d in option["top_positive_drivers"]],
        "sources": list(case.raw_evidence_sources),
        "source_quality_summary": _source_quality(option["confidence"], source_count),
        "time_range": f"last_{case.timeframe_months}_months_to_present",
        "confidence": option["confidence"],
        "gaps": list(option["key_unknowns"]),
        "generated_at": generated_at,
    }
    item["item_fingerprint"] = _hash_item(item)
    return item


def _topic_packet(
    *,
    case: DecisionCase,
    generated_at: str,
    lane: str,
    option: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    disputed = [u for u in option["key_unknowns"]]
    attention = "high" if status in {"disputed", "provisional"} else "medium"
    item = {
        "item_id": f"topic:{case.case_id}:{option['option_id']}",
        "object_type": "TopicIntelPacket",
        "topic": option["candidate_entity"],
        "lane": lane,
        "summary": (
            f"{option['candidate_entity']} scored {option['final_score']} "
            f"({option['decision_label']}) with confidence {option['confidence']}."
        ),
        "key_facts": [
            f"score={option['final_score']}",
            f"risk={option['risk_score']}",
            f"uncertainty={option['uncertainty_score']}",
        ],
        "new_facts": [d["driver"] for d in option["top_positive_drivers"]],
        "disputed_facts": disputed,
        "confidence": option["confidence"],
        "recommended_attention_level": attention,
        "generated_at": generated_at,
    }
    item["item_fingerprint"] = _hash_item(item)
    return item


def _contradiction_signal(
    *,
    case: DecisionCase,
    generated_at: str,
    option: dict[str, Any],
    scenario_scores: dict[str, float],
    contradiction_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    base_score = scenario_scores["base"]
    downside = scenario_scores["downside"]
    drift = round(base_score - downside, 2)
    item_id = f"contradiction:{case.case_id}:{option['option_id']}"
    status = "unresolved"
    if contradiction_status and item_id in contradiction_status:
        status = contradiction_status[item_id]
    item = {
        "item_id": item_id,
        "object_type": "ContradictionSignal",
        "entity": option["candidate_entity"],
        "topic": case.domain,
        "claim_a": f"Base case supports {option['candidate_entity']} with score {base_score}.",
        "claim_b": f"Downside case weakens to score {downside}.",
        "source_a": "scenario_base",
        "source_b": "scenario_downside",
        "relative_strength": round(abs(drift) / 100.0, 3),
        "resolution_status": status,
        "generated_at": generated_at,
    }
    item["item_fingerprint"] = _hash_item(item)
    return item


def _parse_iso(when: str) -> datetime:
    normalized = when.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _delta_filter(items: list[dict[str, Any]], delta_from_path: str | None) -> list[dict[str, Any]]:
    if not delta_from_path:
        return items
    path = Path(delta_from_path)
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8") as f:
        previous = json.load(f)
    old_items = {}
    for item in previous.get("items", []):
        old_items[item.get("item_id")] = item.get("item_fingerprint")
    filtered: list[dict[str, Any]] = []
    for item in items:
        if old_items.get(item["item_id"]) != item.get("item_fingerprint"):
            filtered.append(item)
    return filtered


def _since_filter(items: list[dict[str, Any]], since: str | None) -> list[dict[str, Any]]:
    if not since:
        return items
    cutoff = _parse_iso(since)
    filtered: list[dict[str, Any]] = []
    for item in items:
        if _parse_iso(item["generated_at"]) >= cutoff:
            filtered.append(item)
    return filtered


def build_lisa_feed_packet(
    *,
    case: DecisionCase,
    report: dict[str, Any],
    lane: str = "fact_intelligence",
    publish_status: str = "draft",
    delta_from_path: str | None = None,
    since: str | None = None,
    contradiction_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    generated_at = _utc_now_iso()
    items: list[dict[str, Any]] = []

    for option in report["ranked_options"]:
        fact = _fact_signal(case=case, generated_at=generated_at, lane=lane, option=option)
        evidence = _evidence_packet(case=case, generated_at=generated_at, option=option)
        topic = _topic_packet(
            case=case,
            generated_at=generated_at,
            lane=lane,
            option=option,
            status=fact["status"],
        )
        contradiction = _contradiction_signal(
            case=case,
            generated_at=generated_at,
            option=option,
            scenario_scores=report["scenario_comparison"][option["option_id"]],
            contradiction_status=contradiction_status,
        )
        items.extend([fact, evidence, topic, contradiction])

    items = _delta_filter(items, delta_from_path)
    items = _since_filter(items, since)

    avg_score = 0.0
    if report["ranked_options"]:
        avg_score = sum(o["final_score"] for o in report["ranked_options"]) / len(report["ranked_options"])
    packet = {
        "source_system": "factdeck",
        "packet_type": "factdeck_lisa_feed",
        "generated_at": generated_at,
        "lane": lane,
        "priority": _priority_from_score(avg_score),
        "summary": (
            f"FactDeck knowledge translation for case {case.case_id}; "
            f"{len(items)} LISA-ready knowledge objects."
        ),
        "items": items,
        "evidence_refs": list(case.raw_evidence_sources),
        "fresh_until": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "publish_status": publish_status,
        "delta_mode": {"since": since, "delta_from_path": delta_from_path},
    }
    return packet
