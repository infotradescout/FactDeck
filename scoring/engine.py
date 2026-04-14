from __future__ import annotations

from dataclasses import dataclass

from core.schemas import CandidateOption


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class ScoreBreakdown:
    structural_score: float
    demand_score: float
    feasibility_score: float
    risk_score: float
    uncertainty_score: float
    final_score: float
    confidence_level: float
    confidence_band: tuple[float, float]
    positive_drivers: list[tuple[str, float]]
    negative_drivers: list[tuple[str, float]]
    key_unknowns: list[str]


def score_option(option: CandidateOption) -> ScoreBreakdown:
    structural = option.evidence.structural.score
    comparative = option.evidence.comparative.score
    behavioral = option.evidence.behavioral.score
    constraint = option.evidence.constraint.score
    risk = option.evidence.risk.score

    demand = (comparative + behavioral) / 2.0
    feasibility = constraint

    confidences = [
        option.evidence.structural.confidence,
        option.evidence.comparative.confidence,
        option.evidence.constraint.confidence,
        option.evidence.behavioral.confidence,
        option.evidence.risk.confidence,
    ]
    confidence_level = sum(confidences) / len(confidences)

    missing = (
        option.evidence.structural.missing
        + option.evidence.comparative.missing
        + option.evidence.constraint.missing
        + option.evidence.behavioral.missing
        + option.evidence.risk.missing
    )
    uncertainty = _clamp((1.0 - confidence_level) * 100.0 + len(missing) * 3.0)

    bonus = 0.0
    if demand >= 70 and feasibility >= 65 and risk <= 45:
        bonus = 6.0

    c_struct = 0.30 * structural
    c_demand = 0.35 * demand
    c_feas = 0.35 * feasibility
    c_risk = -0.25 * risk
    c_unc = -0.20 * uncertainty

    raw = c_struct + c_demand + c_feas + c_risk + c_unc + bonus
    final = _clamp(raw)

    band_half_width = max(5.0, (1.0 - confidence_level) * 20.0 + len(missing) * 1.5)
    band = (_clamp(final - band_half_width), _clamp(final + band_half_width))

    positive_drivers = sorted(
        [
            ("structural evidence", c_struct),
            ("demand signals", c_demand),
            ("feasibility constraints", c_feas),
            ("opportunity bonus", bonus),
        ],
        key=lambda x: x[1],
        reverse=True,
    )[:3]
    negative_drivers = sorted(
        [
            ("risk penalty", c_risk),
            ("uncertainty penalty", c_unc),
            ("fragility penalty", -0.08 * option.fragility),
            ("resource intensity penalty", -0.06 * option.resource_intensity),
        ],
        key=lambda x: x[1],
    )[:3]

    return ScoreBreakdown(
        structural_score=round(structural, 2),
        demand_score=round(demand, 2),
        feasibility_score=round(feasibility, 2),
        risk_score=round(risk, 2),
        uncertainty_score=round(uncertainty, 2),
        final_score=round(final, 2),
        confidence_level=round(confidence_level, 3),
        confidence_band=(round(band[0], 2), round(band[1], 2)),
        positive_drivers=[(name, round(value, 2)) for name, value in positive_drivers],
        negative_drivers=[(name, round(value, 2)) for name, value in negative_drivers],
        key_unknowns=list(dict.fromkeys(missing))[:5],
    )

