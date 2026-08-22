from __future__ import annotations

import json
from pathlib import Path
import unittest

from gkd_release.core import build_release_candidate, promotion_request, validate_traceability
from gkd_task.errors import TaskError


class ReleaseCandidateContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.traceability = json.loads(Path("canonical/payload/fixtures/release/traceability.json").read_text())

    def test_all_decisions_have_positive_negative_and_critical_mutations(self) -> None:
        validate_traceability(self.traceability)

    def test_missing_decision_is_rejected(self) -> None:
        self.traceability["decisions"].pop()
        with self.assertRaisesRegex(TaskError, "TRACEABILITY_INCOMPLETE"):
            validate_traceability(self.traceability)

    def test_exact_sha_sandbox_and_provenance_bind_promotion(self) -> None:
        record = build_release_candidate({"version":"0.1.0","sourceSha":"a"*40,"bundleDigest":"b"*64,"evidenceDigest":"c"*64,"traceability":self.traceability,"layers":["L0","L1","L2","L3","L4"],"sandboxRepository":"github.com/KNaiFen/gkd-sandbox"})
        self.assertEqual(promotion_request(record)["targetSha"], "a" * 40)
        record["bundleDigest"] = "d" * 64
        with self.assertRaisesRegex(TaskError, "RELEASE_RECORD_TAMPERED"):
            promotion_request(record)
