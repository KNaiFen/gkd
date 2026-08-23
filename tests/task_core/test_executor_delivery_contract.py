from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "canonical" / "payload" / "skills" / "gkd-execute" / "SKILL.md"


class ExecutorDeliveryContract(unittest.TestCase):
    def test_delivery_document_commit_is_the_deliver_cas_head(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("Commit all implementation changes first.", content)
        self.assertIn("--expected-head <delivery-document-commit-full-sha>", content)
        self.assertIn("never the implementation commit SHA", content)
        self.assertIn("only commit after the delivery document", content)


if __name__ == "__main__":
    unittest.main()
