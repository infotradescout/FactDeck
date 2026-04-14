from __future__ import annotations

import json
from pathlib import Path
from typing import Any


POLICY_PATHS = {
    "business_viability": "config/scoring/business_viability_v1.0.json",
    "opportunity_ranking": "config/scoring/opportunity_ranking_v1.0.json",
}


def load_policy(domain: str) -> dict[str, Any]:
    path = POLICY_PATHS.get(domain)
    if not path:
        raise ValueError(f"No scoring policy configured for domain '{domain}'.")
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_policy_locked(policy: dict[str, Any], expected_version: str = "1.0") -> None:
    version = str(policy.get("schema_version", ""))
    if version != expected_version:
        raise ValueError(f"Policy schema_version mismatch. Expected {expected_version}, got {version}.")
    if "locked_at_utc" not in policy:
        raise ValueError("Policy must include locked_at_utc to be considered frozen.")

