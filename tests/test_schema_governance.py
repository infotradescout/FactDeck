from __future__ import annotations

import unittest

from lisa_feed.schema_guard import assert_backward_compatible, validate_packet_contract


class TestSchemaGovernance(unittest.TestCase):
    def test_packet_contract_ok(self) -> None:
        packet = {
            "source_system": "factdeck",
            "packet_type": "factdeck_lisa_feed",
            "generated_at": "2026-04-14T00:00:00+00:00",
            "lane": "fact_intelligence",
            "priority": "medium",
            "summary": "x",
            "items": [],
            "evidence_refs": [],
            "fresh_until": "2026-04-30T00:00:00+00:00",
            "publish_status": "draft",
            "schema_version": "1.0",
        }
        validate_packet_contract(packet)
        assert_backward_compatible(packet, expected_major="1")

    def test_major_break_fails(self) -> None:
        packet = {
            "source_system": "factdeck",
            "packet_type": "factdeck_lisa_feed",
            "generated_at": "2026-04-14T00:00:00+00:00",
            "lane": "fact_intelligence",
            "priority": "medium",
            "summary": "x",
            "items": [],
            "evidence_refs": [],
            "fresh_until": "2026-04-30T00:00:00+00:00",
            "publish_status": "draft",
            "schema_version": "2.0",
        }
        with self.assertRaises(ValueError):
            assert_backward_compatible(packet, expected_major="1")


if __name__ == "__main__":
    unittest.main()

