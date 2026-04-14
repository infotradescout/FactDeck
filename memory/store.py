from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_decision(path: str, record: dict[str, Any]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "logged_at_utc": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

