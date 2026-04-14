from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from core.schemas import CandidateOption, OutcomeSpec
from scoring.engine import ScoreBreakdown


def _next_action(state: str, option: CandidateOption, unknowns: list[str]) -> str:
    if state == "pursue":
        return f"Start a 30-day pilot for '{option.candidate_entity}' in {option.geography} with weekly KPI checks."
    if state == "pursue cautiously":
        return (
            f"Run a low-capital pilot for '{option.candidate_entity}' and validate top risk before scaling."
        )
    if state == "gather more evidence":
        needs = ", ".join(unknowns[:3]) if unknowns else "key demand and cost assumptions"
        return f"Collect missing evidence for: {needs}, then rerun comparison."
    if state == "deprioritize":
        return f"Deprioritize '{option.candidate_entity}' for now and re-evaluate after material evidence change."
    return f"Reject '{option.candidate_entity}' under current constraints."


def _to_option_record(
    option: CandidateOption,
    breakdown: ScoreBreakdown,
    recommendation_fn: Callable[[float, float, float, float], str],
) -> dict[str, Any]:
    state = recommendation_fn(
        final_score=breakdown.final_score,
        confidence=breakdown.confidence_level,
        risk_score=breakdown.risk_score,
        uncertainty=breakdown.uncertainty_score,
    )
    return {
        "option_id": option.option_id,
        "candidate_entity": option.candidate_entity,
        "geography": option.geography,
        "final_score": breakdown.final_score,
        "risk_score": breakdown.risk_score,
        "confidence": breakdown.confidence_level,
        "confidence_band": list(breakdown.confidence_band),
        "resource_intensity": option.resource_intensity,
        "speed_to_payoff_months": option.speed_to_payoff_months,
        "fragility": option.fragility,
        "structural_score": breakdown.structural_score,
        "demand_score": breakdown.demand_score,
        "feasibility_score": breakdown.feasibility_score,
        "uncertainty_score": breakdown.uncertainty_score,
        "decision_label": state,
        "top_positive_drivers": [
            {"driver": name, "contribution": value} for name, value in breakdown.positive_drivers
        ],
        "top_negative_drivers": [
            {"driver": name, "contribution": value} for name, value in breakdown.negative_drivers
        ],
        "key_unknowns": breakdown.key_unknowns,
        "assumptions": option.assumptions,
        "recommended_next_action": _next_action(state, option, breakdown.key_unknowns),
    }


def _winner(records: list[dict[str, Any]], key: str, reverse: bool = True) -> dict[str, Any]:
    return sorted(records, key=lambda r: r[key], reverse=reverse)[0]


def render_report(
    case_id: str,
    domain: str,
    outcome_spec: OutcomeSpec,
    option_records: list[dict[str, Any]],
    scenarios: dict[str, dict[str, float]],
) -> dict[str, Any]:
    ranked = sorted(option_records, key=lambda r: r["final_score"], reverse=True)
    best = ranked[0]

    low_capital_winner = _winner(
        ranked,
        key="final_score",
    )
    low_capital_winner = sorted(
        ranked,
        key=lambda r: (r["resource_intensity"], -r["final_score"]),
    )[0]
    speed_winner = sorted(
        ranked,
        key=lambda r: (r["speed_to_payoff_months"], -r["final_score"]),
    )[0]
    safety_winner = sorted(
        ranked,
        key=lambda r: (r["risk_score"], -r["final_score"]),
    )[0]

    return {
        "case_id": case_id,
        "domain": domain,
        "outcome_spec": asdict(outcome_spec),
        "best_overall": {
            "option_id": best["option_id"],
            "candidate_entity": best["candidate_entity"],
            "decision_label": best["decision_label"],
            "confidence": best["confidence"],
            "confidence_band": best["confidence_band"],
            "recommended_next_action": best["recommended_next_action"],
        },
        "comparison_summary": {
            "best_under_low_capital_constraint": low_capital_winner["option_id"],
            "best_under_speed_priority": speed_winner["option_id"],
            "best_under_safety_priority": safety_winner["option_id"],
        },
        "ranked_options": ranked,
        "scenario_comparison": scenarios,
        "what_would_change_answer": [
            "material change in fixed-cost assumptions",
            "new demand validation in target geography",
            "regulatory or permit constraints shift",
        ],
    }
