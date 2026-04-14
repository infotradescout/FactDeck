from __future__ import annotations

from core.schemas import CandidateOption, DecisionCase, EvidenceSet, FactorEvidence


def _in_range(value: float, low: float, high: float, name: str) -> list[str]:
    if value < low or value > high:
        return [f"{name} must be between {low} and {high}, got {value}."]
    return []


def _validate_factor(prefix: str, factor: FactorEvidence) -> list[str]:
    errors: list[str] = []
    errors.extend(_in_range(factor.score, 0.0, 100.0, f"{prefix}.score"))
    errors.extend(_in_range(factor.confidence, 0.0, 1.0, f"{prefix}.confidence"))
    return errors


def _validate_evidence(evidence: EvidenceSet) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_factor("evidence.structural", evidence.structural))
    errors.extend(_validate_factor("evidence.comparative", evidence.comparative))
    errors.extend(_validate_factor("evidence.constraint", evidence.constraint))
    errors.extend(_validate_factor("evidence.behavioral", evidence.behavioral))
    errors.extend(_validate_factor("evidence.risk", evidence.risk))
    return errors


def _validate_option(option: CandidateOption) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_evidence(option.evidence))
    errors.extend(_in_range(option.resource_intensity, 0.0, 100.0, "resource_intensity"))
    errors.extend(_in_range(option.fragility, 0.0, 100.0, "fragility"))
    if option.speed_to_payoff_months <= 0:
        errors.append("speed_to_payoff_months must be > 0.")
    if not option.assumptions:
        errors.append(f"option {option.option_id} must include at least one assumption.")
    return errors


def validate_decision_case(case: DecisionCase) -> list[str]:
    errors: list[str] = []

    if case.domain != "business_viability":
        errors.append(f"Unsupported domain: {case.domain}. Expected 'business_viability'.")
    if not case.options:
        errors.append("At least one option is required.")
    if len(case.options) < 2:
        errors.append("Comparison mode requires at least two options.")

    if not case.outcome_spec.target_label_name.strip():
        errors.append("outcome_spec.target_label_name must be explicit.")
    if not case.outcome_spec.target_rule.strip():
        errors.append("outcome_spec.target_rule must be explicit.")
    if case.outcome_spec.observation_window_months <= 0:
        errors.append("outcome_spec.observation_window_months must be > 0.")
    if case.outcome_spec.measurement_lag_months < 0:
        errors.append("outcome_spec.measurement_lag_months must be >= 0.")

    if case.timeframe_months <= 0:
        errors.append("timeframe_months must be > 0.")

    for option in case.options:
        errors.extend(_validate_option(option))

    return errors

