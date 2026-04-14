from __future__ import annotations

from typing import Any, Callable

from core.schemas import DecisionCase
from reports.renderer import render_report
from scoring.engine import score_option
from scoring.policy import ensure_policy_locked, load_policy
from scenarios.transforms import apply_scenario


def run_decision(case: DecisionCase) -> dict[str, Any]:
    validate_domain_fit, recommendation_fn = _domain_handlers(case.domain)
    domain_errors = validate_domain_fit(case)
    if domain_errors:
        raise ValueError("; ".join(domain_errors))

    policy = load_policy(case.domain)
    ensure_policy_locked(policy)

    option_records: list[dict[str, Any]] = []
    scenario_comparison: dict[str, dict[str, float]] = {}

    for option in case.options:
        base_breakdown = score_option(option, policy=policy)
        option_records.append(
            {
                **{
                    "option_id": option.option_id,
                    "candidate_entity": option.candidate_entity,
                    "geography": option.geography,
                },
                **_record_fields(option, base_breakdown, recommendation_fn),
            }
        )

        scenario_comparison[option.option_id] = {
            "base": base_breakdown.final_score,
            "upside": score_option(apply_scenario(option, "upside"), policy=policy).final_score,
            "downside": score_option(apply_scenario(option, "downside"), policy=policy).final_score,
        }

    return render_report(
        case_id=case.case_id,
        domain=case.domain,
        outcome_spec=case.outcome_spec,
        option_records=option_records,
        scenarios=scenario_comparison,
    )


def _record_fields(
    option: Any,
    base_breakdown: Any,
    recommendation_fn: Callable[[float, float, float, float], str],
) -> dict[str, Any]:
    from reports.renderer import _to_option_record

    return _to_option_record(option, base_breakdown, recommendation_fn)


def _domain_handlers(
    domain: str,
) -> tuple[
    Callable[[DecisionCase], list[str]],
    Callable[[float, float, float, float], str],
]:
    if domain == "business_viability":
        from domains.business_viability.domain import recommendation_state, validate_domain_fit

        return validate_domain_fit, recommendation_state
    if domain == "opportunity_ranking":
        from domains.opportunity_ranking.domain import recommendation_state, validate_domain_fit

        return validate_domain_fit, recommendation_state
    raise ValueError(f"Unsupported domain '{domain}'.")
