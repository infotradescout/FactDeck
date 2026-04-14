from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lisa_feed.exporter import write_feed_page, write_packet_json, write_packet_ndjson


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def publish_packet_versioned(
    *,
    packet: dict[str, Any],
    root_dir: str = "feeds",
    write_ndjson: bool = True,
) -> dict[str, str]:
    now = _utc_now()
    day = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%H%M%S")
    out_dir = Path(root_dir) / day
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"factdeck_lisa_feed_{stamp}.json"
    ndjson_path = out_dir / f"factdeck_lisa_feed_{stamp}.ndjson"
    page_path = out_dir / f"lisa-feed_{stamp}.html"
    manifest_path = out_dir / f"manifest_{stamp}.json"

    write_packet_json(str(json_path), packet)
    if write_ndjson:
        write_packet_ndjson(str(ndjson_path), packet)
    write_feed_page(str(page_path), packet, str(ndjson_path) if write_ndjson else None)
    manifest = {
        "generated_at": _utc_now().isoformat(),
        "json_sha256": _sha256_file(json_path),
        "ndjson_sha256": _sha256_file(ndjson_path) if write_ndjson else "",
        "page_sha256": _sha256_file(page_path),
        "packet_type": packet.get("packet_type"),
        "schema_version": packet.get("schema_version", "1.0"),
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    _update_latest_index(
        root_dir=root_dir,
        json_path=json_path,
        ndjson_path=ndjson_path if write_ndjson else None,
        page_path=page_path,
        manifest_path=manifest_path,
    )

    return {
        "json_path": json_path.as_posix(),
        "ndjson_path": ndjson_path.as_posix() if write_ndjson else "",
        "page_path": page_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _update_latest_index(
    *,
    root_dir: str,
    json_path: Path,
    ndjson_path: Path | None,
    page_path: Path,
    manifest_path: Path,
) -> None:
    root = Path(root_dir)
    latest = {
        "updated_at": _utc_now().isoformat(),
        "json_path": json_path.as_posix(),
        "ndjson_path": ndjson_path.as_posix() if ndjson_path else "",
        "page_path": page_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
    }
    with (root / "latest.json").open("w", encoding="utf-8") as f:
        json.dump(latest, f, indent=2)
