from __future__ import annotations

from core.schemas import DecisionCase
from scoring.policy import load_policy

DOMAIN_NAME = "opportunity_ranking"
UNIT_OF_EVALUATION = "one opportunity option in one context"


def recommendation_state(final_score: float, confidence: float, risk_score: float, uncertainty: float) -> str:
    policy = load_policy(DOMAIN_NAME)
    thresholds = policy["decision_thresholds"]
    if uncertainty > float(thresholds["gather_more_if_uncertainty_gt"]):
        return "gather more evidence"
    pursue = thresholds["pursue"]
    if (
        final_score >= float(pursue["score_min"])
        and confidence >= float(pursue["confidence_min"])
        and risk_score < float(pursue["risk_max"])
    ):
        return "pursue"
    if final_score >= float(thresholds["pursue_cautiously_score_min"]):
        return "pursue cautiously"
    if final_score >= float(thresholds["deprioritize_score_min"]):
        return "deprioritize"
    return "reject"


def validate_domain_fit(case: DecisionCase) -> list[str]:
    errors: list[str] = []
    if case.domain != DOMAIN_NAME:
        errors.append(f"Case domain must be '{DOMAIN_NAME}'.")
    return errors

