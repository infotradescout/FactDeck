from __future__ import annotations

import argparse
import json
from pathlib import Path

from connectors.fact_sources import enrich_case_with_connectors
from core.orchestration import run_decision
from core.schemas import decision_case_from_dict
from core.validators import validate_decision_case
from lisa_feed.builder import build_lisa_feed_packet
from lisa_feed.exporter import write_feed_page, write_packet_json, write_packet_ndjson
from lisa_feed.publisher import publish_packet_versioned
from memory.contradictions import (
    apply_contradiction_actions,
    contradiction_status_map,
    load_contradiction_store,
    merge_new_contradictions,
    save_contradiction_store,
)
from memory.lisa_publish import append_publish_history, last_published_event
from memory.store import append_decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FactDeck decision engine v1")
    parser.add_argument(
        "--command",
        choices=["run", "publish"],
        default="run",
        help="run: evaluate case. publish: versioned LISA publish workflow.",
    )
    parser.add_argument("--input", required=True, help="Path to decision case JSON file")
    parser.add_argument("--memory", required=False, help="Optional JSONL decision memory log path")
    parser.add_argument(
        "--use-connectors",
        action="store_true",
        help="Apply structured connector evidence before scoring",
    )
    parser.add_argument(
        "--evidence-dir",
        default="connectors/data",
        help="Connector evidence dataset directory",
    )
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
    parser.add_argument(
        "--auto-delta",
        action="store_true",
        help="If enabled and no --delta-from, use last published feed from history",
    )
    parser.add_argument(
        "--history-log",
        default="memory/lisa_feed_history.jsonl",
        help="Publish history JSONL path",
    )
    parser.add_argument(
        "--publish-root",
        default="feeds",
        help="Root directory for versioned publish snapshots",
    )
    parser.add_argument(
        "--contradiction-store",
        default="memory/contradictions.json",
        help="Path for contradiction lifecycle store",
    )
    parser.add_argument(
        "--contradiction-action",
        action="append",
        default=[],
        help="Contradiction status update, format: <item_id>:<status>",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    with input_path.open("r", encoding="utf-8") as f:
        raw_case = json.load(f)

    case = decision_case_from_dict(raw_case)
    if args.use_connectors:
        case = enrich_case_with_connectors(case, args.evidence_dir)

    errors = validate_decision_case(case)
    if errors:
        raise SystemExit("Validation failed:\n- " + "\n- ".join(errors))

    report = run_decision(case)
    print(json.dumps(report, indent=2))

    if args.memory:
        append_decision(args.memory, report)

    should_emit_feed = args.emit_lisa_feed or args.command == "publish"
    if should_emit_feed:
        contradiction_store = load_contradiction_store(args.contradiction_store)
        if args.contradiction_action:
            contradiction_store = apply_contradiction_actions(contradiction_store, args.contradiction_action)
            save_contradiction_store(args.contradiction_store, contradiction_store)

        auto_delta_from = args.delta_from
        if args.auto_delta and not auto_delta_from:
            last = last_published_event(args.history_log)
            if last and last.get("json_path"):
                auto_delta_from = str(last["json_path"])

        packet = build_lisa_feed_packet(
            case=case,
            report=report,
            lane=args.lane,
            publish_status=("published" if args.command == "publish" else args.publish_status),
            delta_from_path=auto_delta_from,
            since=args.since,
            contradiction_status=contradiction_status_map(contradiction_store),
        )

        contradiction_ids = [i["item_id"] for i in packet["items"] if i.get("object_type") == "ContradictionSignal"]
        contradiction_store = merge_new_contradictions(contradiction_store, contradiction_ids)
        save_contradiction_store(args.contradiction_store, contradiction_store)

        if args.command == "publish":
            publish_paths = publish_packet_versioned(
                packet=packet,
                root_dir=args.publish_root,
                write_ndjson=True,
            )
            append_publish_history(
                args.history_log,
                {
                    "command": "publish",
                    "case_id": case.case_id,
                    "json_path": publish_paths["json_path"],
                    "ndjson_path": publish_paths["ndjson_path"],
                    "page_path": publish_paths["page_path"],
                    "item_count": len(packet["items"]),
                    "delta_from": auto_delta_from,
                },
            )
            print(
                json.dumps(
                    {
                        "publish_result": "ok",
                        "json_path": publish_paths["json_path"],
                        "ndjson_path": publish_paths["ndjson_path"],
                        "page_path": publish_paths["page_path"],
                    },
                    indent=2,
                )
            )
        else:
            write_packet_json(args.feed_json, packet)
            if args.feed_ndjson:
                write_packet_ndjson(args.feed_ndjson, packet)
            write_feed_page(args.feed_page, packet, args.feed_ndjson)


if __name__ == "__main__":
    main()
