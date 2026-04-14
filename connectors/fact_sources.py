from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from core.schemas import DecisionCase


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def enrich_case_with_connectors(case: DecisionCase, evidence_dir: str) -> DecisionCase:
    """Apply structured evidence updates from connector datasets."""
    root = Path(evidence_dir)
    demographics = _load_json(root / "demographics.json")
    search_signals = _load_json(root / "search_signals.json")
    cost_pressures = _load_json(root / "cost_pressures.json")
    regulatory_flags = _load_json(root / "regulatory_flags.json")

    enriched = deepcopy(case)

    for option in enriched.options:
        geo = option.geography
        entity = option.candidate_entity

        demo_entry = demographics.get(geo, {})
        search_entry = search_signals.get(entity, {})
        cost_entry = cost_pressures.get(geo, {})
        reg_entry = regulatory_flags.get(geo, {})

        structural_delta = float(demo_entry.get("structural_delta", 0.0))
        behavioral_delta = float(search_entry.get("behavioral_delta", 0.0))
        constraint_delta = float(cost_entry.get("constraint_delta", 0.0))
        risk_delta = float(reg_entry.get("risk_delta", 0.0))

        option.evidence.structural.score = _clamp(option.evidence.structural.score + structural_delta)
        option.evidence.behavioral.score = _clamp(option.evidence.behavioral.score + behavioral_delta)
        option.evidence.constraint.score = _clamp(option.evidence.constraint.score + constraint_delta)
        option.evidence.risk.score = _clamp(option.evidence.risk.score + risk_delta)

        for field, note in [
            (option.evidence.structural.notes, demo_entry.get("note")),
            (option.evidence.behavioral.notes, search_entry.get("note")),
            (option.evidence.constraint.notes, cost_entry.get("note")),
            (option.evidence.risk.notes, reg_entry.get("note")),
        ]:
            if note:
                field.append(str(note))

    sources = set(enriched.raw_evidence_sources)
    for src in [
        f"{root.as_posix()}/demographics.json",
        f"{root.as_posix()}/search_signals.json",
        f"{root.as_posix()}/cost_pressures.json",
        f"{root.as_posix()}/regulatory_flags.json",
    ]:
        sources.add(src)
    enriched.raw_evidence_sources = sorted(sources)
    return enriched

