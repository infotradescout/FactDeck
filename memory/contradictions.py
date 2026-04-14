from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED = {"unresolved", "investigating", "resolved"}
TRANSITIONS = {
    "unresolved": {"unresolved", "investigating"},
    "investigating": {"investigating", "resolved"},
    "resolved": {"resolved"},
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_contradiction_store(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"signals": {}}
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "signals" not in data or not isinstance(data["signals"], dict):
        return {"signals": {}}
    return data


def save_contradiction_store(path: str, store: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _parse_action(action: str) -> tuple[str, str]:
    if ":" not in action:
        raise ValueError(f"Invalid contradiction action '{action}'. Use id:status.")
    item_id, status = action.rsplit(":", 1)
    item_id = item_id.strip()
    status = status.strip()
    if status not in ALLOWED:
        raise ValueError(f"Invalid status '{status}'. Allowed: unresolved, investigating, resolved.")
    return item_id, status


def apply_contradiction_actions(store: dict[str, Any], actions: list[str]) -> dict[str, Any]:
    signals = store.setdefault("signals", {})
    now = _utc()
    for action in actions:
        item_id, new_status = _parse_action(action)
        record = signals.get(item_id, {"resolution_status": "unresolved", "history": []})
        old_status = record.get("resolution_status", "unresolved")
        if new_status not in TRANSITIONS.get(old_status, {old_status}):
            raise ValueError(
                f"Invalid transition for {item_id}: {old_status} -> {new_status}. "
                "Allowed: unresolved->investigating->resolved."
            )
        record["resolution_status"] = new_status
        record["updated_at"] = now
        record.setdefault("history", []).append(
            {"from": old_status, "to": new_status, "changed_at": now}
        )
        signals[item_id] = record
    return store


def contradiction_status_map(store: dict[str, Any]) -> dict[str, str]:
    return {
        item_id: details.get("resolution_status", "unresolved")
        for item_id, details in store.get("signals", {}).items()
    }


def merge_new_contradictions(
    store: dict[str, Any],
    contradiction_ids: list[str],
) -> dict[str, Any]:
    signals = store.setdefault("signals", {})
    for item_id in contradiction_ids:
        if item_id not in signals:
            signals[item_id] = {
                "resolution_status": "unresolved",
                "updated_at": _utc(),
                "history": [{"from": "unresolved", "to": "unresolved", "changed_at": _utc()}],
            }
    return store
