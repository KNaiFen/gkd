from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tests.foundation.helpers import copy_governance_repo, gkd_bundle


class EvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = copy_governance_repo(self.root)
        self.protected = self.root / "protected"
        self.protected.mkdir()
        (self.protected / "config.toml").write_text("stable = true\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, name: str) -> tuple[dict, bytes]:
        run_root = self.root / name
        run_root.mkdir()
        output = self.root / f"{name}.json"
        result = gkd_bundle.generate_evidence(
            self.repo / "canonical", run_root, self.protected, output
        )
        return result, output.read_bytes()

    def test_two_clean_evidence_generations_are_byte_identical(self) -> None:
        first_result, first = self._run("run-a")
        second_result, second = self._run("run-b")
        self.assertEqual(first_result, second_result)
        self.assertEqual(first, second)

    def test_evidence_digest_is_canonical_and_self_excluding(self) -> None:
        _, raw = self._run("run")
        evidence = json.loads(raw)
        digest = evidence.pop("evidenceDigest")
        self.assertEqual(digest, gkd_bundle.sha256_bytes(gkd_bundle.canonical_bytes(evidence)))
        self.assertEqual(evidence["outcome"], "canonical_foundation_ready")
        self.assertTrue(evidence["protectedHome"]["unchanged"])

    def test_evidence_contains_no_temporary_or_machine_path(self) -> None:
        _, raw = self._run("run")
        text = raw.decode("utf-8").casefold()
        self.assertNotIn(str(self.root).casefold(), text)
        self.assertFalse(gkd_bundle._forbidden_content(raw))

    def test_protected_surface_change_is_detected(self) -> None:
        before = gkd_bundle._snapshot_protected(self.protected)
        (self.protected / "config.toml").write_text("stable = false\n", encoding="utf-8")
        after = gkd_bundle._snapshot_protected(self.protected)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
