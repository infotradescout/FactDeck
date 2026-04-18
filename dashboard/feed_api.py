from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path("feeds")
SCHEMA_VERSION = "2.0"
FEED_API_VERSION = "factdeck-feed-api/2.0"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _lane_summaries(items: list) -> dict:
    """Compute per-lane summaries from item list — works even if signalfactory didn't add them."""
    lanes: dict[str, list] = {}
    for item in items:
        lane = str(item.get("lane") or item.get("signal") or "unclassified")
        lanes.setdefault(lane, []).append(item)
    result = {}
    for lane, lane_items in lanes.items():
        confidences = [float(i.get("confidence") or 0) for i in lane_items]
        impacts     = [i.get("impact_level", "medium") for i in lane_items]
        trends      = [i.get("trend", "neutral") for i in lane_items]
        top_item    = max(lane_items, key=lambda i: float(i.get("confidence") or 0), default={})
        result[lane] = {
            "count":           len(lane_items),
            "avg_confidence":  round(sum(confidences) / len(confidences), 4) if confidences else 0,
            "dominant_impact": max(set(impacts), key=impacts.count) if impacts else "medium",
            "dominant_trend":  max(set(trends), key=trends.count) if trends else "neutral",
            "top_signal_id":   top_item.get("id"),
            "top_signal_kind": top_item.get("signal_kind"),
            "action_hint":     top_item.get("action_hint"),
        }
    return result


def _quality_score(items: list, failures: list) -> float:
    if not items:
        return 0.0
    all_c = [float(i.get("confidence") or 0) for i in items]
    penalty = min(len(failures) * 5, 30)
    return round(max(sum(all_c) / len(all_c) * 100 - penalty, 0), 1)


def _enrich_packet(packet: dict) -> dict:
    """Inject freshness_seconds, lane_summaries, quality_score at serve time so the
    consumer always sees live values even if the file was written without them."""
    if not packet:
        return packet

    items    = packet.get("items", [])
    failures = packet.get("failures", [])

    generated = packet.get("generated_at")
    freshness = None
    if generated:
        try:
            gen_dt    = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            freshness = int((datetime.now(timezone.utc) - gen_dt).total_seconds())
        except ValueError:
            pass

    enriched = {
        **packet,
        "schema_version":  packet.get("schema_version", SCHEMA_VERSION),
        "freshness_seconds": freshness,
        "lane_summaries":  packet.get("lane_summaries") or _lane_summaries(items),
        "quality_score":   packet.get("quality_score")  or _quality_score(items, failures),
    }
    return enriched


def _load_since(since: str) -> dict:
    latest  = _load_json(ROOT / "latest.json")
    packet  = latest
    if not packet:
        return {"items": [], "lanes": {}, "lane_counts": {}, "count": 0, "since": since}

    if "items" not in packet and latest.get("json_path"):
        packet = _load_json(Path(latest["json_path"]))

    items = []
    for item in packet.get("items", []):
        generated = item.get("receivedAt") or item.get("generated_at")
        if not generated:
            continue
        try:
            if datetime.fromisoformat(generated.replace("Z", "+00:00")) >= datetime.fromisoformat(
                since.replace("Z", "+00:00")
            ):
                items.append(item)
        except ValueError:
            continue

    lanes: dict = {}
    for item in items:
        lane = str(item.get("lane") or item.get("signal") or "unclassified")
        lanes.setdefault(lane, []).append(item)

    return {
        "schema_version":  SCHEMA_VERSION,
        "items":           items,
        "lanes":           lanes,
        "lane_counts":     {lane: len(entries) for lane, entries in lanes.items()},
        "lane_summaries":  _lane_summaries(items),
        "quality_score":   _quality_score(items, []),
        "count":           len(items),
        "since":           since,
    }


# ── Request handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            latest_path = ROOT / "latest.json"
            age_seconds = None
            item_count  = 0
            if latest_path.exists():
                raw = _load_json(latest_path)
                items = raw.get("items", [])
                item_count = len(items)
                generated = raw.get("generated_at")
                if generated:
                    try:
                        gen_dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
                        age_seconds = int((datetime.now(timezone.utc) - gen_dt).total_seconds())
                    except ValueError:
                        pass
            self._send_json({
                "ok":            True,
                "service":       FEED_API_VERSION,
                "now":           datetime.now(timezone.utc).isoformat(),
                "feed_path":     str(latest_path),
                "feed_exists":   latest_path.exists(),
                "item_count":    item_count,
                "age_seconds":   age_seconds,
            })
            return

        if parsed.path == "/latest":
            latest = _load_json(ROOT / "latest.json")
            if latest.get("items"):
                self._send_json(_enrich_packet(latest))
                return
            json_path = latest.get("json_path")
            if json_path:
                full = _load_json(Path(json_path))
                self._send_json(_enrich_packet(full) if full else {})
                return
            self._send_json({})
            return

        if parsed.path == "/since":
            params = parse_qs(parsed.query)
            since  = params.get("ts", [""])[0]
            if not since:
                self._send_json({"error": "missing ts query parameter"}, status=400)
                return
            self._send_json(_load_since(since))
            return

        self._send_json({"error": "not found"}, status=404)

    def _add_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        etag = f'"{hashlib.md5(body).hexdigest()}"'
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Feed-Version", FEED_API_VERSION)
        self.send_header("X-Schema-Version", SCHEMA_VERSION)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("ETag", etag)
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # noqa: N802
        # Suppress default access log noise; replace with structured output.
        print(f"[feed-api] {self.address_string()} {fmt % args}")


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8087), Handler)
    print(f"[feed-api] {FEED_API_VERSION} listening on http://127.0.0.1:8087")
    server.serve_forever()


if __name__ == "__main__":
    main()

