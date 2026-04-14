from __future__ import annotations

from copy import deepcopy

from core.schemas import CandidateOption


def apply_scenario(option: CandidateOption, scenario: str) -> CandidateOption:
    candidate = deepcopy(option)

    if scenario == "base":
        return candidate
    if scenario == "upside":
        candidate.evidence.behavioral.score = min(100.0, candidate.evidence.behavioral.score + 10.0)
        candidate.evidence.comparative.score = min(100.0, candidate.evidence.comparative.score + 8.0)
        candidate.evidence.constraint.score = min(100.0, candidate.evidence.constraint.score + 6.0)
        candidate.evidence.risk.score = max(0.0, candidate.evidence.risk.score - 8.0)
        return candidate
    if scenario == "downside":
        candidate.evidence.behavioral.score = max(0.0, candidate.evidence.behavioral.score - 12.0)
        candidate.evidence.comparative.score = max(0.0, candidate.evidence.comparative.score - 10.0)
        candidate.evidence.constraint.score = max(0.0, candidate.evidence.constraint.score - 8.0)
        candidate.evidence.risk.score = min(100.0, candidate.evidence.risk.score + 10.0)
        return candidate

    raise ValueError(f"Unknown scenario: {scenario}")

