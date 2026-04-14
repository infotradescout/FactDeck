from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FactorEvidence:
    score: float
    confidence: float
    notes: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class EvidenceSet:
    structural: FactorEvidence
    comparative: FactorEvidence
    constraint: FactorEvidence
    behavioral: FactorEvidence
    risk: FactorEvidence


@dataclass
class CandidateOption:
    option_id: str
    candidate_entity: str
    geography: str
    assumptions: list[str]
    evidence: EvidenceSet
    resource_intensity: float
    speed_to_payoff_months: float
    fragility: float


@dataclass
class ConstraintSet:
    max_capital: float
    max_time_months: float
    geography_limit: str | None
    labor_limit_hours_week: float | None
    required_skills: list[str] = field(default_factory=list)
    regulatory_notes: list[str] = field(default_factory=list)


@dataclass
class OutcomeSpec:
    target_label_name: str
    target_rule: str
    observation_window_months: int
    source_of_truth: str
    measurement_lag_months: int


@dataclass
class DecisionCase:
    case_id: str
    domain: str
    timeframe_months: int
    resources_available: dict[str, Any]
    constraints: ConstraintSet
    outcome_spec: OutcomeSpec
    options: list[CandidateOption]
    raw_evidence_sources: list[str]
    current_state_snapshot: dict[str, Any]


def _factor_from_dict(data: dict[str, Any]) -> FactorEvidence:
    return FactorEvidence(
        score=float(data["score"]),
        confidence=float(data["confidence"]),
        notes=list(data.get("notes", [])),
        missing=list(data.get("missing", [])),
    )


def _evidence_from_dict(data: dict[str, Any]) -> EvidenceSet:
    return EvidenceSet(
        structural=_factor_from_dict(data["structural"]),
        comparative=_factor_from_dict(data["comparative"]),
        constraint=_factor_from_dict(data["constraint"]),
        behavioral=_factor_from_dict(data["behavioral"]),
        risk=_factor_from_dict(data["risk"]),
    )


def decision_case_from_dict(data: dict[str, Any]) -> DecisionCase:
    constraints = ConstraintSet(**data["constraints"])
    outcome_spec = OutcomeSpec(**data["outcome_spec"])
    options = []
    for option in data["options"]:
        options.append(
            CandidateOption(
                option_id=option["option_id"],
                candidate_entity=option["candidate_entity"],
                geography=option["geography"],
                assumptions=list(option.get("assumptions", [])),
                evidence=_evidence_from_dict(option["evidence"]),
                resource_intensity=float(option["resource_intensity"]),
                speed_to_payoff_months=float(option["speed_to_payoff_months"]),
                fragility=float(option["fragility"]),
            )
        )
    return DecisionCase(
        case_id=data["case_id"],
        domain=data["domain"],
        timeframe_months=int(data["timeframe_months"]),
        resources_available=dict(data["resources_available"]),
        constraints=constraints,
        outcome_spec=outcome_spec,
        options=options,
        raw_evidence_sources=list(data.get("raw_evidence_sources", [])),
        current_state_snapshot=dict(data.get("current_state_snapshot", {})),
    )

