from __future__ import annotations

from typing import Any

from core.schemas import DecisionCase
from domains.business_viability.domain import validate_domain_fit
from reports.renderer import render_report
from scoring.engine import score_option
from scenarios.transforms import apply_scenario


def run_decision(case: DecisionCase) -> dict[str, Any]:
    domain_errors = validate_domain_fit(case)
    if domain_errors:
        raise ValueError("; ".join(domain_errors))

    option_records: list[dict[str, Any]] = []
    scenario_comparison: dict[str, dict[str, float]] = {}

    for option in case.options:
        base_breakdown = score_option(option)
        option_records.append(
            {
                **{
                    "option_id": option.option_id,
                    "candidate_entity": option.candidate_entity,
                    "geography": option.geography,
                },
                **_record_fields(option, base_breakdown),
            }
        )

        scenario_comparison[option.option_id] = {
            "base": base_breakdown.final_score,
            "upside": score_option(apply_scenario(option, "upside")).final_score,
            "downside": score_option(apply_scenario(option, "downside")).final_score,
        }

    return render_report(
        case_id=case.case_id,
        domain=case.domain,
        outcome_spec=case.outcome_spec,
        option_records=option_records,
        scenarios=scenario_comparison,
    )


def _record_fields(option: Any, base_breakdown: Any) -> dict[str, Any]:
    from reports.renderer import _to_option_record

    return _to_option_record(option, base_breakdown)

