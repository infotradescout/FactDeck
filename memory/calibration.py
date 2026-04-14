from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scoring.policy import load_policy


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _brier(probs: list[float], outcomes: list[int]) -> float:
    if not probs:
        return 0.0
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def _mae(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(abs(v) for v in values) / len(values)


def run_monthly_calibration(
    *,
    decision_log_path: str,
    outcomes_log_path: str,
    domain: str,
    output_dir: str = "memory/calibration_reports",
) -> dict[str, Any]:
    decisions = _read_jsonl(decision_log_path)
    outcomes = _read_jsonl(outcomes_log_path)

    outcome_map = {}
    for row in outcomes:
        key = (row.get("case_id"), row.get("option_id"))
        outcome_map[key] = int(row.get("observed_success", 0))

    probs: list[float] = []
    labels: list[int] = []
    confidence_gap: list[float] = []
    matched = 0

    for dec in decisions:
        for option in dec.get("ranked_options", []):
            key = (dec.get("case_id"), option.get("option_id"))
            if key not in outcome_map:
                continue
            observed = outcome_map[key]
            conf = float(option.get("confidence", 0.0))
            probs.append(conf)
            labels.append(observed)
            confidence_gap.append(conf - observed)
            matched += 1

    brier = _brier(probs, labels)
    mean_gap = _mae(confidence_gap)

    policy = load_policy(domain)
    suggestion = "hold"
    tweak = {
        "uncertainty_penalty": policy["weights"]["uncertainty_penalty"],
        "risk_penalty": policy["weights"]["risk_penalty"],
    }

    if matched > 0:
        if mean_gap > 0.15:
            suggestion = "increase_caution"
            tweak["uncertainty_penalty"] = round(float(tweak["uncertainty_penalty"]) + 0.02, 3)
            tweak["risk_penalty"] = round(float(tweak["risk_penalty"]) + 0.01, 3)
        elif mean_gap < 0.05 and brier < 0.12:
            suggestion = "consider_relaxing"
            tweak["uncertainty_penalty"] = round(max(0.05, float(tweak["uncertainty_penalty"]) - 0.01), 3)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "matched_outcomes": matched,
        "brier_score": round(brier, 4),
        "mean_absolute_confidence_gap": round(mean_gap, 4),
        "policy_id": policy["policy_id"],
        "recommendation": suggestion,
        "suggested_penalty_weights": tweak,
    }

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m")
    report_path = out / f"{domain}_{stamp}.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    report["report_path"] = report_path.as_posix()
    return report

