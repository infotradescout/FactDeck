from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any


def _fetch_json(url: str) -> dict[str, Any]:
    if url.startswith("file://"):
        p = Path(url.replace("file://", "", 1))
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _check_keys(data: dict[str, Any], required_top_keys: list[str]) -> list[str]:
    missing = []
    for key in required_top_keys:
        if key not in data:
            missing.append(key)
    return missing


def pull_connector_sources(registry_path: str, output_dir: str) -> dict[str, Any]:
    reg = Path(registry_path)
    with reg.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    health: dict[str, Any] = {"sources": [], "all_healthy": True}
    for src in registry.get("sources", []):
        name = src["name"]
        url = src["url"]
        output = out / src["output"]
        required = list(src.get("required_top_keys", []))

        record: dict[str, Any] = {
            "name": name,
            "url": url,
            "output": output.as_posix(),
            "status": "ok",
            "missing_required_keys": [],
            "error": "",
        }

        try:
            data = _fetch_json(url)
            missing = _check_keys(data, required)
            if missing:
                record["status"] = "degraded"
                record["missing_required_keys"] = missing
                health["all_healthy"] = False
            with output.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:  # noqa: BLE001
            record["status"] = "failed"
            record["error"] = str(exc)
            health["all_healthy"] = False
        health["sources"].append(record)

    health_path = out / "health_report.json"
    with health_path.open("w", encoding="utf-8") as f:
        json.dump(health, f, indent=2)
    health["health_report"] = health_path.as_posix()
    return health

