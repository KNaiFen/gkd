from __future__ import annotations

import json
import subprocess
import sys
import unittest
from copy import deepcopy

from gkd_review.adapter import adapter_digest, validate_adapter
from gkd_review.core import approve_partial, begin_review, recover_review, recommend_review, resume_review, validate_recommendation, validate_review_state
from gkd_review.remediation import approve_remediation, begin_remediation, recover_remediation, resume_remediation, validate_remediation
from gkd_task.errors import TaskError
from tests.review_core.helpers import ROOT, adapter, state


class ReviewCoreContracts(unittest.TestCase):
    def test_explicit_target_is_recommended_and_ambiguous_intent_stays_clarification(self) -> None:
        explicit = recommend_review("review change", "alpha")
        validate_recommendation(explicit)
        self.assertEqual("recommended", explicit["status"])
        ambiguous = recommend_review("please help", None)
        self.assertEqual("clarify", ambiguous["status"])
        self.assertNotIn("approved", ambiguous)

    def test_targeted_guided_and_recon_entry_contracts(self) -> None:
        value = adapter()
        self.assertEqual("alpha", begin_review("targeted", value, target="alpha", intent="review change")["target"])
        self.assertEqual("guided", recommend_review("review", None)["entryPoint"])
        self.assertEqual("recon", recommend_review(None, None)["entryPoint"])
        with self.assertRaisesRegex(TaskError, "REVIEW_TARGET_REQUIRED"):
            begin_review("targeted", value, intent="review change")

    def test_partial_approval_resume_and_recovery_preserve_machine_facts(self) -> None:
        original = state()
        partial = approve_partial(original, ["review"])
        self.assertEqual("partially-approved", partial["status"])
        self.assertEqual(original["machineFacts"], partial["machineFacts"])
        with self.assertRaisesRegex(TaskError, "CONTINUATION_REQUIRED"):
            resume_review(partial, {"continue": False})
        resumed = resume_review(partial, {"continue": True})
        self.assertEqual("resumed", resumed["status"])
        recovered = recover_review(partial)
        validate_review_state(recovered)
        self.assertEqual(partial["reviewId"], recovered["reviewId"])
        self.assertEqual(partial["cursor"] + 0, recovered["cursor"])

    def test_review_state_rejects_digest_and_machine_path_mutations(self) -> None:
        mutated = deepcopy(state())
        mutated["machineFacts"]["headSha"] = "/Users/private/head"
        with self.assertRaisesRegex(TaskError, "REVIEW_STATE_INVALID"):
            validate_review_state(mutated)
        mutated = state()
        mutated["stateDigest"] = "0" * 64
        with self.assertRaisesRegex(TaskError, "REVIEW_STATE_INVALID"):
            validate_review_state(mutated)

    def test_adapter_supports_multiple_repositories_and_is_digest_bound(self) -> None:
        value = adapter()
        validate_adapter(value)
        self.assertEqual({"alpha", "beta"}, {item["id"] for item in value["repositories"]})
        self.assertEqual(value["adapterDigest"], adapter_digest(value))
        mutated = deepcopy(value)
        mutated["repositories"][0]["identity"] = "example-org/other"
        with self.assertRaisesRegex(TaskError, "ADAPTER_INVALID"):
            validate_adapter(mutated)

    def test_remediation_requires_explicit_partial_approval_and_resume(self) -> None:
        review = state()
        value = begin_remediation(review, [{"id": "F-001", "severity": "high", "summary": "required check is blocked"}, {"id": "F-002", "severity": "low", "summary": "documentation is incomplete"}])
        partial = approve_remediation(value, ["F-001"])
        self.assertEqual(["F-002"], partial["pendingFindings"])
        with self.assertRaisesRegex(TaskError, "REMEDIATION_APPROVAL_REQUIRED"):
            resume_remediation(value, {"continue": True})
        resumed = resume_remediation(partial, {"continue": True})
        validate_remediation(resumed)
        self.assertEqual([], resumed["pendingFindings"])
        self.assertEqual("recovered", recover_remediation(partial)["status"])

    def test_credential_shaped_findings_are_terminally_rejected(self) -> None:
        with self.assertRaisesRegex(TaskError, "REMEDIATION_FINDING_INVALID"):
            begin_remediation(state(), [{"id": "F-001", "severity": "high", "summary": "token=ghp_abcdefghijklmnopqrstuvwxyz0123456789"}])

    def test_cli_returns_one_canonical_machine_result(self) -> None:
        result = subprocess.run(
            (sys.executable, "-B", "-m", "gkd_review.cli", "recommend", "--intent", "review change", "--target", "alpha"),
            cwd=ROOT,
            env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "canonical" / "payload" / "lib")},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual("recommended", value["status"])
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
