from __future__ import annotations

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

    write_packet_json(str(json_path), packet)
    if write_ndjson:
        write_packet_ndjson(str(ndjson_path), packet)
    write_feed_page(str(page_path), packet, str(ndjson_path) if write_ndjson else None)

    return {
        "json_path": json_path.as_posix(),
        "ndjson_path": ndjson_path.as_posix() if write_ndjson else "",
        "page_path": page_path.as_posix(),
    }

