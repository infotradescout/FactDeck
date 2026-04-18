from __future__ import annotations

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path("feeds")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_since(since: str) -> dict:
    latest = _load_json(ROOT / "latest.json")
    packet = latest
    if not packet:
        return {"items": [], "lanes": {}, "lane_counts": {}, "count": 0, "since": since}

    if "items" not in packet and latest.get("json_path"):
        packet = _load_json(Path(latest["json_path"]))

    items = []
    for item in packet.get("items", []):
        generated = item.get("receivedAt") or item.get("generated_at")
        if not generated:
            continue
        if datetime.fromisoformat(generated.replace("Z", "+00:00")) >= datetime.fromisoformat(
            since.replace("Z", "+00:00")
        ):
            items.append(item)

    lanes = {}
    for item in items:
        lane = str(item.get("lane") or item.get("signal") or "unclassified")
        lanes.setdefault(lane, []).append(item)

    return {
        "items": items,
        "lanes": lanes,
        "lane_counts": {lane: len(entries) for lane, entries in lanes.items()},
        "count": len(items),
        "since": since,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/latest":
            latest = _load_json(ROOT / "latest.json")
            if latest.get("items"):
                self._send_json(latest)
                return

            json_path = latest.get("json_path")
            if json_path:
                self._send_json(_load_json(Path(json_path)))
                return

            self._send_json({})
            return
        if parsed.path == "/since":
            params = parse_qs(parsed.query)
            since = params.get("ts", [""])[0]
            if not since:
                self._send_json({"error": "missing ts query parameter"}, status=400)
                return
            self._send_json(_load_since(since))
            return
        self._send_json({"error": "not found"}, status=404)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8087), Handler)
    print("Feed API listening on http://127.0.0.1:8087")
    server.serve_forever()


if __name__ == "__main__":
    main()

