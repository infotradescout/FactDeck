from __future__ import annotations

import unittest

from memory.contradictions import apply_contradiction_actions


class TestContradictionWorkflow(unittest.TestCase):
    def test_valid_transition_chain(self) -> None:
        store = {"signals": {"contradiction:case-1:A": {"resolution_status": "unresolved", "history": []}}}
        store = apply_contradiction_actions(store, ["contradiction:case-1:A:investigating"])
        self.assertEqual(store["signals"]["contradiction:case-1:A"]["resolution_status"], "investigating")
        store = apply_contradiction_actions(store, ["contradiction:case-1:A:resolved"])
        self.assertEqual(store["signals"]["contradiction:case-1:A"]["resolution_status"], "resolved")

    def test_invalid_transition_raises(self) -> None:
        store = {"signals": {"contradiction:case-1:A": {"resolution_status": "unresolved", "history": []}}}
        with self.assertRaises(ValueError):
            apply_contradiction_actions(store, ["contradiction:case-1:A:resolved"])


if __name__ == "__main__":
    unittest.main()

