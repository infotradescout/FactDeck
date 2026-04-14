from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _ensure_parent(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_packet_json(path: str, packet: dict[str, Any]) -> None:
    p = _ensure_parent(path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2)


def write_packet_ndjson(path: str, packet: dict[str, Any]) -> None:
    p = _ensure_parent(path)
    with p.open("w", encoding="utf-8") as f:
        for item in packet["items"]:
            f.write(json.dumps(item) + "\n")


def _cards(packet: dict[str, Any]) -> tuple[int, int, int, int]:
    new_count = sum(1 for i in packet["items"] if i.get("object_type") == "FactSignal")
    changed_count = sum(1 for i in packet["items"] if i.get("object_type") == "TopicIntelPacket")
    disputed_count = sum(
        1
        for i in packet["items"]
        if i.get("object_type") == "FactSignal" and i.get("status") == "disputed"
    )
    high_conf_count = sum(
        1
        for i in packet["items"]
        if i.get("object_type") == "TopicIntelPacket" and float(i.get("confidence", 0)) >= 0.72
    )
    return new_count, changed_count, disputed_count, high_conf_count


def write_feed_page(path: str, packet: dict[str, Any], ndjson_path: str | None = None) -> None:
    p = _ensure_parent(path)
    packet_json = json.dumps(packet, indent=2)
    packet_ndjson = "\n".join(json.dumps(item) for item in packet["items"])
    new_count, changed_count, disputed_count, high_conf_count = _cards(packet)

    evidence_rows = []
    for item in packet["items"]:
        if item.get("object_type") != "FactSignal":
            continue
        evidence_rows.append(
            "<tr>"
            f"<td>{html.escape(item.get('item_id', ''))}</td>"
            f"<td>{html.escape(item.get('entity', ''))}</td>"
            f"<td>{html.escape(item.get('topic', ''))}</td>"
            f"<td>{html.escape(', '.join(item.get('evidence_refs', [])))}</td>"
            f"<td>{html.escape(str(item.get('generated_at', '')))}</td>"
            f"<td>{html.escape(str(item.get('confidence', '')))}</td>"
            f"<td>{html.escape(str(item.get('contradiction_risk', '')))}</td>"
            f"<td>{html.escape(str(item.get('status', '')))}</td>"
            "</tr>"
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FactDeck LISA Feed</title>
  <style>
    :root {{
      --bg: #f8f4ed;
      --panel: #fffef9;
      --ink: #1f1f1a;
      --muted: #685f56;
      --line: #d9d0c5;
      --accent: #9d4b2b;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 10% 0%, #fff7e6, var(--bg));
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 16px;
    }}
    h1, h2 {{
      margin: 0 0 10px 0;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: #fff;
    }}
    .metric {{
      font-size: 1.6rem;
      color: var(--accent);
      font-weight: 700;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #f5f1ea;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      max-height: 360px;
      overflow: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f0e9dc;
    }}
    .sub {{
      color: var(--muted);
      margin-top: 4px;
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="panel">
      <h1>/lisa-feed</h1>
      <div class="sub">FactDeck knowledge translation layer for LISA.</div>
      <div class="sub">Generated: {html.escape(packet.get("generated_at", ""))} | Publish status: {html.escape(packet.get("publish_status", ""))}</div>
    </section>

    <section class="panel">
      <h2>Section A - LISA-ready fact signals</h2>
      <div class="cards">
        <article class="card"><div class="sub">new facts</div><div class="metric">{new_count}</div></article>
        <article class="card"><div class="sub">changed facts</div><div class="metric">{changed_count}</div></article>
        <article class="card"><div class="sub">disputed facts</div><div class="metric">{disputed_count}</div></article>
        <article class="card"><div class="sub">high-confidence topic updates</div><div class="metric">{high_conf_count}</div></article>
      </div>
    </section>

    <section class="panel">
      <h2>Section B - raw export payload</h2>
      <div class="sub">JSON (copy/export)</div>
      <pre>{html.escape(packet_json)}</pre>
      <div class="sub">NDJSON (copy/export)</div>
      <pre>{html.escape(packet_ndjson)}</pre>
      <div class="sub">NDJSON file path: {html.escape(ndjson_path or "(not exported)")}</div>
    </section>

    <section class="panel">
      <h2>Section C - evidence explorer</h2>
      <table>
        <thead>
          <tr>
            <th>fact id</th>
            <th>entity</th>
            <th>topic</th>
            <th>sources</th>
            <th>timestamp</th>
            <th>confidence</th>
            <th>contradiction risk</th>
            <th>status</th>
          </tr>
        </thead>
        <tbody>
          {''.join(evidence_rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    with p.open("w", encoding="utf-8") as f:
        f.write(html_doc)

