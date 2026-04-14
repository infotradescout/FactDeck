from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.orchestration import run_decision
from core.schemas import decision_case_from_dict
from lisa_feed.builder import build_lisa_feed_packet


class TestDeltaFingerprintStability(unittest.TestCase):
    def test_fingerprints_stable_across_runs(self) -> None:
        with Path("config/examples/business_viability_case.json").open("r", encoding="utf-8") as f:
            case = decision_case_from_dict(json.load(f))
        report = run_decision(case)

        packet_a = build_lisa_feed_packet(case=case, report=report)
        packet_b = build_lisa_feed_packet(case=case, report=report)

        map_a = {i["item_id"]: i["item_fingerprint"] for i in packet_a["items"]}
        map_b = {i["item_id"]: i["item_fingerprint"] for i in packet_b["items"]}
        self.assertEqual(map_a, map_b)


if __name__ == "__main__":
    unittest.main()

