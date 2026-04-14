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
    json_path = latest.get("json_path")
    if not json_path:
        return {"items": []}
    packet = _load_json(Path(json_path))
    items = []
    for item in packet.get("items", []):
        generated = item.get("generated_at")
        if not generated:
            continue
        if datetime.fromisoformat(generated.replace("Z", "+00:00")) >= datetime.fromisoformat(
            since.replace("Z", "+00:00")
        ):
            items.append(item)
    return {"items": items, "count": len(items), "since": since}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/latest":
            self._send_json(_load_json(ROOT / "latest.json"))
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

