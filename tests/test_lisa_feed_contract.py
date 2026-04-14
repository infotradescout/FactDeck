from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.orchestration import run_decision
from core.schemas import decision_case_from_dict
from lisa_feed.builder import build_lisa_feed_packet


class TestLisaFeedContract(unittest.TestCase):
    def test_packet_and_item_contract(self) -> None:
        with Path("config/examples/business_viability_case.json").open("r", encoding="utf-8") as f:
            case = decision_case_from_dict(json.load(f))
        report = run_decision(case)
        packet = build_lisa_feed_packet(case=case, report=report)

        for key in [
            "source_system",
            "packet_type",
            "generated_at",
            "lane",
            "priority",
            "summary",
            "items",
            "evidence_refs",
            "fresh_until",
            "publish_status",
        ]:
            self.assertIn(key, packet)

        type_required = {
            "FactSignal": {
                "source_system",
                "source_type",
                "generated_at",
                "lane",
                "entity",
                "topic",
                "claim",
                "normalized_fact",
                "fact_type",
                "confidence",
                "freshness",
                "source_count",
                "evidence_refs",
                "contradiction_risk",
                "status",
                "tags",
            },
            "EvidencePacket": {
                "packet_id",
                "entity",
                "topic",
                "supporting_claims",
                "sources",
                "source_quality_summary",
                "time_range",
                "confidence",
                "gaps",
            },
            "TopicIntelPacket": {
                "topic",
                "lane",
                "summary",
                "key_facts",
                "new_facts",
                "disputed_facts",
                "confidence",
                "recommended_attention_level",
            },
            "ContradictionSignal": {
                "entity",
                "topic",
                "claim_a",
                "claim_b",
                "source_a",
                "source_b",
                "relative_strength",
                "resolution_status",
            },
        }
        self.assertGreater(len(packet["items"]), 0)
        for item in packet["items"]:
            self.assertIn("object_type", item)
            required = type_required[item["object_type"]]
            for field in required:
                self.assertIn(field, item)


if __name__ == "__main__":
    unittest.main()

