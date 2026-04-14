from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.orchestration import run_decision
from core.schemas import decision_case_from_dict
from core.validators import validate_decision_case
from lisa_feed.builder import build_lisa_feed_packet
from lisa_feed.exporter import write_feed_page, write_packet_json, write_packet_ndjson
from memory.store import append_decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FactDeck decision engine v1")
    parser.add_argument("--input", required=True, help="Path to decision case JSON file")
    parser.add_argument("--memory", required=False, help="Optional JSONL decision memory log path")
    parser.add_argument("--emit-lisa-feed", action="store_true", help="Emit LISA feed artifacts")
    parser.add_argument(
        "--feed-json",
        default="factdeck_lisa_feed.json",
        help="Path to write LISA feed JSON packet",
    )
    parser.add_argument(
        "--feed-ndjson",
        required=False,
        help="Optional path to write LISA feed NDJSON items",
    )
    parser.add_argument(
        "--feed-page",
        default="dashboard/lisa-feed/index.html",
        help="Path to write LISA feed HTML page",
    )
    parser.add_argument(
        "--lane",
        default="fact_intelligence",
        help="Knowledge lane label for the LISA packet",
    )
    parser.add_argument(
        "--publish-status",
        choices=["draft", "published"],
        default="draft",
        help="Publish state for the LISA packet",
    )
    parser.add_argument(
        "--since",
        required=False,
        help="Emit only items generated at or after this ISO timestamp",
    )
    parser.add_argument(
        "--delta-from",
        required=False,
        help="Path to a previous feed JSON to emit only new/changed items",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    with input_path.open("r", encoding="utf-8") as f:
        raw_case = json.load(f)

    case = decision_case_from_dict(raw_case)
    errors = validate_decision_case(case)
    if errors:
        raise SystemExit("Validation failed:\n- " + "\n- ".join(errors))

    report = run_decision(case)
    print(json.dumps(report, indent=2))

    if args.memory:
        append_decision(args.memory, report)

    if args.emit_lisa_feed:
        packet = build_lisa_feed_packet(
            case=case,
            report=report,
            lane=args.lane,
            publish_status=args.publish_status,
            delta_from_path=args.delta_from,
            since=args.since,
        )
        write_packet_json(args.feed_json, packet)
        if args.feed_ndjson:
            write_packet_ndjson(args.feed_ndjson, packet)
        write_feed_page(args.feed_page, packet, args.feed_ndjson)


if __name__ == "__main__":
    main()
