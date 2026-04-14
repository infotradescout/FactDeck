from __future__ import annotations

from core.schemas import DecisionCase


DOMAIN_NAME = "business_viability"
UNIT_OF_EVALUATION = "one concept in one geography"
SUCCESS_OUTCOME_HINT = "revenue viability / survival / margin viability over horizon"
DEFAULT_HORIZON_MONTHS = (6, 12)
ALLOWED_RECOMMENDATION_STATES = [
    "pursue",
    "pursue cautiously",
    "gather more evidence",
    "deprioritize",
    "reject",
]


def recommendation_state(final_score: float, confidence: float, risk_score: float, uncertainty: float) -> str:
    if uncertainty > 45:
        return "gather more evidence"
    if final_score >= 75 and confidence >= 0.65 and risk_score < 50:
        return "pursue"
    if final_score >= 60:
        return "pursue cautiously"
    if final_score >= 45:
        return "deprioritize"
    return "reject"


def validate_domain_fit(case: DecisionCase) -> list[str]:
    errors: list[str] = []
    if case.domain != DOMAIN_NAME:
        errors.append(f"Case domain must be '{DOMAIN_NAME}'.")
    return errors

