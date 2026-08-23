from __future__ import annotations

import json
from pathlib import Path
import unittest

from gkd_release.core import build_release_candidate, promotion_request, validate_traceability
from gkd_task.canonical import digest_object
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

    def test_generic_or_reused_evidence_ids_are_rejected(self) -> None:
        self.traceability["decisions"][1]["positive"] = self.traceability["decisions"][0]["positive"]
        with self.assertRaisesRegex(TaskError, "TRACEABILITY_EVIDENCE_MISMATCH"):
            validate_traceability(self.traceability)

    def test_every_traceability_reference_is_a_runnable_versioned_contract(self) -> None:
        root = Path(__file__).resolve().parents[2]
        suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py", top_level_dir=str(root))

        def flatten(value):
            for item in value:
                if isinstance(item, unittest.TestSuite):
                    yield from flatten(item)
                else:
                    yield item

        available = {item.id() for item in flatten(suite)}
        for entry in self.traceability["decisions"]:
            for identifier in (*entry["positive"], *entry["negative"], entry["mutation"]):
                with self.subTest(decision=entry["decisionId"], identifier=identifier):
                    self.assertIn(identifier, available)

    def test_exact_sha_sandbox_and_provenance_bind_promotion(self) -> None:
        record = build_release_candidate({"version":"0.1.1","sourceSha":"a"*40,"bundleDigest":"b"*64,"evidenceDigest":"c"*64,"traceability":self.traceability,"layers":["L0","L1","L2","L3","L4"],"sandboxRepository":"github.com/KNaiFen/gkd-sandbox"})
        self.assertEqual(promotion_request(record)["targetSha"], "a" * 40)
        self.assertEqual("v0.1.1", promotion_request(record)["tagName"])
        record["bundleDigest"] = "d" * 64
        with self.assertRaisesRegex(TaskError, "RELEASE_RECORD_TAMPERED"):
            promotion_request(record)

    def test_stable_version_propagates_and_nonstable_versions_fail_closed(self) -> None:
        candidate = {"version":"0.1.4","sourceSha":"a"*40,"bundleDigest":"b"*64,"evidenceDigest":"c"*64,"traceability":self.traceability,"layers":["L0","L1","L2","L3","L4"],"sandboxRepository":"github.com/KNaiFen/gkd-sandbox"}
        self.assertEqual("v0.1.4", promotion_request(build_release_candidate(candidate))["tagName"])
        for version in ("0.1", "0.01.4", "0.1.4-rc.1", "v0.1.4", ""):
            with self.subTest(version=version):
                invalid = dict(candidate, version=version)
                with self.assertRaisesRegex(TaskError, "INVALID_RELEASE_CANDIDATE"):
                    build_release_candidate(invalid)

    def test_version_mutation_cannot_change_promotion_tag(self) -> None:
        candidate = {"version":"0.1.4","sourceSha":"a"*40,"bundleDigest":"b"*64,"evidenceDigest":"c"*64,"traceability":self.traceability,"layers":["L0","L1","L2","L3","L4"],"sandboxRepository":"github.com/KNaiFen/gkd-sandbox"}
        record = build_release_candidate(candidate)
        record["version"] = "0.1.4-rc.1"
        unsigned = dict(record)
        unsigned.pop("recordDigest")
        record["recordDigest"] = digest_object(unsigned)
        with self.assertRaisesRegex(TaskError, "INVALID_RELEASE_CANDIDATE"):
            promotion_request(record)
