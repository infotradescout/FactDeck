from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.orchestration import run_decision
from core.schemas import decision_case_from_dict
from core.validators import validate_decision_case
from memory.store import append_decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FactDeck decision engine v1")
    parser.add_argument("--input", required=True, help="Path to decision case JSON file")
    parser.add_argument("--memory", required=False, help="Optional JSONL decision memory log path")
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


if __name__ == "__main__":
    main()

