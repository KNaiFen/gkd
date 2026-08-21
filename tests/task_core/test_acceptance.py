from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from gkd_task.acceptance import MergeIndeterminate, accept_candidate, make_review
from gkd_task.canonical import canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.model import finalize_state
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import (
    CONFIG_DIGEST,
    FUTURE_TIME,
    REVIEWER_DIGEST,
    ROLE_DIGEST,
    SESSION_DIGEST,
    FakeGitHub,
    TaskRepo,
    github_snapshot,
    run,
)


class AcceptanceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _delivered(self, mode: str = "implement_and_merge_on_acceptance") -> str:
        if mode == "implement_and_merge_on_acceptance":
            _, candidate_head = self.repo.delivered()
            return candidate_head
        service = self.repo.ready_and_authorized(mode=mode)
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        envelope = service.handoff()["envelopeId"]
        claim = service.claim(*self.repo.cas(), envelope)
        self.repo.deliver(service, claim["claimId"])
        return self.repo.head()

    def _review(self, candidate_head: str, **changes):
        values = {
            "task_id": self.repo.task_id,
            "candidate_head": candidate_head,
            "reviewer_role": "acceptor",
            "reviewer_digest": REVIEWER_DIGEST,
            "outcome": "accepted",
            "findings": [],
        }
        values.update(changes)
        return make_review(**values)

    def _accept(self, candidate_head: str, adapter: FakeGitHub, review=None, merge: bool = True, checks=None, role: str = "acceptor"):
        return accept_candidate(
            self.repo.main,
            self.repo.candidate,
            self.repo.task_path,
            self.repo.identity,
            7,
            candidate_head,
            checks if checks is not None else ["contract"],
            review or self._review(candidate_head),
            adapter,
            role,
            merge,
            runtime=RuntimeStore(self.repo.runtime_root),
        )

    def test_exact_head_acceptance_performs_two_reads_and_one_merge(self) -> None:
        candidate_head = self._delivered()
        delivery = self.repo.state()["lifecycle"]["delivery"]
        self.assertEqual(
            delivery["deliveryDocumentCommit"],
            run("git", "rev-parse", f"{candidate_head}^", cwd=self.repo.candidate),
        )
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        result = self._accept(candidate_head, adapter)
        self.assertTrue(result["merged"])
        self.assertEqual(["snapshot", "snapshot", "merge"], [call[0] for call in adapter.calls])
        self.assertEqual(candidate_head, adapter.calls[-1][-1])

    def test_legacy_delivery_without_document_binding_is_readable_but_not_acceptable(self) -> None:
        candidate_head = self._delivered()
        state = self.repo.state()
        delivery = state["lifecycle"]["delivery"]
        for field in ("deliveryDocumentCommit", "deliveryDocumentPath", "deliveryDocumentDigest"):
            delivery.pop(field)
        state["history"][-1]["recordDigest"] = digest_object(delivery)
        state = finalize_state(state)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(state))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "legacy delivery state", cwd=self.repo.candidate)
        legacy_head = self.repo.head()
        adapter = FakeGitHub(github_snapshot(self.repo, legacy_head))
        with self.assertRaisesRegex(TaskError, "DELIVERY_DOCUMENT_BINDING_REQUIRED"):
            self._accept(legacy_head, adapter)
        self.assertEqual([], adapter.calls)

    def test_post_delivery_document_commit_is_not_a_fixed_candidate(self) -> None:
        candidate_head = self._delivered()
        path = self.repo.task_root / "delivery.md"
        path.write_text(path.read_text(encoding="utf-8") + "late edit\n", encoding="utf-8")
        run("git", "add", f"{self.repo.task_path}/delivery.md", cwd=self.repo.candidate)
        run("git", "commit", "-m", "late delivery document edit", cwd=self.repo.candidate)
        late_head = self.repo.head()
        adapter = FakeGitHub(github_snapshot(self.repo, late_head))
        with self.assertRaisesRegex(TaskError, "CANDIDATE_INVALID"):
            self._accept(late_head, adapter)
        self.assertNotEqual(candidate_head, late_head)
        self.assertEqual([], adapter.calls)

    def test_acceptance_requires_external_claim_receipt(self) -> None:
        candidate_head = self._delivered()
        claim_id = self.repo.state()["lifecycle"]["claim"]["claimId"]
        RuntimeStore(self.repo.runtime_root).delete_claim_receipt(claim_id)
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "CLAIM_RECEIPT_UNAVAILABLE"):
            self._accept(candidate_head, adapter)
        self.assertEqual([], adapter.calls)

    def test_acceptance_rejects_explicit_symlink_candidate(self) -> None:
        candidate_head = self._delivered()
        candidate_link = self.repo.root / "candidate-link"
        candidate_link.symlink_to(self.repo.candidate, target_is_directory=True)
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "CANDIDATE_SYMLINK"):
            accept_candidate(
                self.repo.main,
                candidate_link,
                self.repo.task_path,
                self.repo.identity,
                7,
                candidate_head,
                ["contract"],
                self._review(candidate_head),
                adapter,
                "acceptor",
                True,
                runtime=RuntimeStore(self.repo.runtime_root),
            )
        self.assertEqual([], adapter.calls)

    def test_executor_can_never_accept_or_merge(self) -> None:
        candidate_head = self._delivered()
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "EXECUTOR_ACCEPTANCE_FORBIDDEN"):
            self._accept(candidate_head, adapter, role="executor")
        self.assertEqual([], adapter.calls)

    def test_implement_only_refusal_is_one_authorization_mismatch_and_zero_calls(self) -> None:
        candidate_head = self._delivered("implement_only")
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "^authorization_mismatch$"):
            self._accept(candidate_head, adapter, merge=True)
        self.assertEqual([], adapter.calls)

    def test_implement_only_can_record_acceptance_without_merge(self) -> None:
        candidate_head = self._delivered("implement_only")
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        result = self._accept(candidate_head, adapter, merge=False)
        self.assertFalse(result["merged"])
        self.assertEqual(["snapshot"], [call[0] for call in adapter.calls])

    def test_wrong_repo_base_pr_or_head_is_rejected(self) -> None:
        candidate_head = self._delivered()
        mutations = {
            "repository": "example.test/other/repo",
            "baseBranch": "other-base",
            "prNumber": 8,
            "headSha": self.repo.base_sha,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                snapshot = github_snapshot(self.repo, candidate_head)
                snapshot[field] = value
                adapter = FakeGitHub(snapshot)
                with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
                    self._accept(candidate_head, adapter)
                self.assertNotIn("merge", [call[0] for call in adapter.calls])

    def test_missing_failed_or_pending_required_check_is_rejected(self) -> None:
        candidate_head = self._delivered()
        cases = (
            [],
            [{"name": "contract", "status": "failure"}],
            [{"name": "contract", "status": "pending"}],
        )
        for checks in cases:
            with self.subTest(checks=checks):
                adapter = FakeGitHub(github_snapshot(self.repo, candidate_head, checks))
                with self.assertRaisesRegex(TaskError, "REQUIRED_CHECK_FAILURE"):
                    self._accept(candidate_head, adapter)
                self.assertNotIn("merge", [call[0] for call in adapter.calls])

    def test_draft_or_unmergeable_pr_is_rejected(self) -> None:
        candidate_head = self._delivered()
        for field, value in (("draft", True), ("mergeable", False)):
            with self.subTest(field=field):
                snapshot = github_snapshot(self.repo, candidate_head)
                snapshot[field] = value
                adapter = FakeGitHub(snapshot)
                with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
                    self._accept(candidate_head, adapter)

    def test_independent_review_must_match_head_and_have_no_findings(self) -> None:
        candidate_head = self._delivered()
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        reviews = (
            self._review(candidate_head, reviewer_digest=SESSION_DIGEST),
            self._review(self.repo.base_sha),
            self._review(candidate_head, outcome="rejected"),
            self._review(candidate_head, findings=["blocking"]),
        )
        for review in reviews:
            with self.subTest(review=review["reviewDigest"]):
                with self.assertRaisesRegex(TaskError, "INDEPENDENT_REVIEW_REQUIRED"):
                    self._accept(candidate_head, adapter, review=review)
        self.assertEqual([], adapter.calls)

    def test_candidate_module_is_never_imported_or_executed(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        malicious = self.repo.candidate / "gkd_task" / "acceptance.py"
        malicious.parent.mkdir()
        marker = self.repo.root / "candidate-code-executed"
        malicious.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\nraise RuntimeError('candidate code executed')\n", encoding="utf-8")
        run("git", "add", "gkd_task/acceptance.py", cwd=self.repo.candidate)
        run("git", "commit", "-m", "candidate implementation", cwd=self.repo.candidate)
        self.repo.deliver(service, claim_id)
        candidate_head = self.repo.head()
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        self._accept(candidate_head, adapter)
        self.assertFalse(marker.exists())

    def test_local_candidate_drift_between_revalidations_blocks_merge(self) -> None:
        candidate_head = self._delivered()
        repo = self.repo

        class DriftAdapter(FakeGitHub):
            def snapshot(self, repository: str, pr_number: int):
                result = super().snapshot(repository, pr_number)
                if len(self.calls) == 1:
                    path = repo.candidate / "late-drift.txt"
                    path.write_text("drift\n", encoding="utf-8")
                    run("git", "add", "late-drift.txt", cwd=repo.candidate)
                    run("git", "commit", "-m", "drift", cwd=repo.candidate)
                return result

        adapter = DriftAdapter(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "candidate_head_changed"):
            self._accept(candidate_head, adapter)
        self.assertNotIn("merge", [call[0] for call in adapter.calls])

    def test_remote_head_change_on_second_snapshot_blocks_merge(self) -> None:
        candidate_head = self._delivered()

        class HeadDriftAdapter(FakeGitHub):
            def snapshot(self, repository: str, pr_number: int):
                result = super().snapshot(repository, pr_number)
                if len(self.calls) == 2:
                    result["headSha"] = "0" * 40
                return result

        adapter = HeadDriftAdapter(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
            self._accept(candidate_head, adapter)
        self.assertNotIn("merge", [call[0] for call in adapter.calls])

    def test_trusted_main_must_equal_synchronized_origin_base(self) -> None:
        candidate_head = self._delivered()
        path = self.repo.main / "local-only.txt"
        path.write_text("ahead\n", encoding="utf-8")
        run("git", "add", "local-only.txt", cwd=self.repo.main)
        run("git", "commit", "-m", "local ahead", cwd=self.repo.main)
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "TRUSTED_CONTEXT_INVALID"):
            self._accept(candidate_head, adapter)
        self.assertEqual([], adapter.calls)

    def test_delivery_commit_with_extra_path_is_rejected_before_external_call(self) -> None:
        candidate_head = self._delivered()
        extra = self.repo.candidate / "extra-delivery-path.txt"
        extra.write_text("unexpected\n", encoding="utf-8")
        run("git", "add", "extra-delivery-path.txt", cwd=self.repo.candidate)
        run("git", "commit", "--amend", "--no-edit", cwd=self.repo.candidate)
        amended_head = self.repo.head()
        self.assertNotEqual(candidate_head, amended_head)
        adapter = FakeGitHub(github_snapshot(self.repo, amended_head))
        with self.assertRaisesRegex(TaskError, "CANDIDATE_INVALID"):
            self._accept(amended_head, adapter)
        self.assertEqual([], adapter.calls)

    def test_indeterminate_merge_reconciles_exact_head_without_replay(self) -> None:
        candidate_head = self._delivered()
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head), MergeIndeterminate())
        result = self._accept(candidate_head, adapter)
        self.assertTrue(result["merged"])
        self.assertEqual(1, [call[0] for call in adapter.calls].count("merge"))
        self.assertEqual(3, [call[0] for call in adapter.calls].count("snapshot"))

    def test_indeterminate_wrong_head_never_replays_merge(self) -> None:
        candidate_head = self._delivered()

        class WrongReconcile(FakeGitHub):
            def merge(self, repository: str, pr_number: int, expected_head: str):
                self.calls.append(("merge", repository, pr_number, expected_head))
                self.current["state"] = "merged"
                self.current["mergedHead"] = self.repo_base
                raise MergeIndeterminate()

        adapter = WrongReconcile(github_snapshot(self.repo, candidate_head))
        adapter.repo_base = self.repo.base_sha
        with self.assertRaisesRegex(TaskError, "MERGE_INDETERMINATE"):
            self._accept(candidate_head, adapter)
        self.assertEqual(1, [call[0] for call in adapter.calls].count("merge"))

    def test_merge_rejection_is_terminal_and_not_retried(self) -> None:
        candidate_head = self._delivered()
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head), {"status": "rejected", "mergedHead": None})
        with self.assertRaisesRegex(TaskError, "MERGE_REJECTED"):
            self._accept(candidate_head, adapter)
        self.assertEqual(1, [call[0] for call in adapter.calls].count("merge"))

    def test_required_check_policy_is_input_not_canonical_constant(self) -> None:
        candidate_head = self._delivered()
        checks = [{"name": "alpha", "status": "success"}, {"name": "beta", "status": "success"}]
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head, checks))
        result = self._accept(candidate_head, adapter, checks=["alpha", "beta"])
        self.assertTrue(result["merged"])

    def test_required_check_name_allows_spaces(self) -> None:
        candidate_head = self._delivered()
        checks = [{"name": "GKD Verify", "status": "success"}]
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head, checks))
        result = self._accept(candidate_head, adapter, checks=["GKD Verify"])
        self.assertTrue(result["merged"])


if __name__ == "__main__":
    unittest.main()
