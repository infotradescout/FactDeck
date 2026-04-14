from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def append_observed_outcome(
    *,
    path: str,
    case_id: str,
    option_id: str,
    observed_success: int,
    notes: str = "",
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "logged_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "option_id": option_id,
        "observed_success": int(observed_success),
        "notes": notes,
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

