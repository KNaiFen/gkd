from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import threading
import unittest

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_task.acceptance import accept_candidate, make_review, rework_candidate, validate_review
from gkd_task.canonical import FixedClock, FixedNonce, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.model import finalize_state, validate_state
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.runtime_bridge.helpers import BUNDLE_ROOT, automatic_decision, bundle_digest, spawn_result
from tests.task_core.helpers import CONFIG_DIGEST, FIXED_TIME, FUTURE_TIME, REVIEWER_DIGEST, ROLE_DIGEST, SESSION_DIGEST, FakeGitHub, TaskRepo, github_snapshot, run


OUTPUT_BUNDLE_DIGEST = "d" * 64


class ReworkContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _review(self, candidate_head: str, **changes):
        values = {
            "task_id": self.repo.task_id,
            "candidate_head": candidate_head,
            "reviewer_role": "acceptor",
            "reviewer_digest": REVIEWER_DIGEST,
            "outcome": "rejected",
            "findings": ["fixed-head-contract-failed"],
        }
        values.update(changes)
        return make_review(**values)

    def _rework(self, candidate_head: str, adapter: FakeGitHub | None = None, review=None, role: str = "acceptor", failure_hook=None):
        return rework_candidate(
            self.repo.main,
            self.repo.candidate,
            self.repo.task_path,
            self.repo.identity,
            7,
            candidate_head,
            review or self._review(candidate_head),
            adapter or FakeGitHub(github_snapshot(self.repo, candidate_head)),
            role,
            runtime=RuntimeStore(self.repo.runtime_root),
            clock=FixedClock(FIXED_TIME),
            failure_hook=failure_hook,
        )

    def _automatic_delivery(self) -> tuple[dict[str, object], dict[str, object], str]:
        self.repo.ready_and_authorized()
        digest = bundle_digest()
        bridge = TrustedMainRuntimeBridge(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            BUNDLE_ROOT,
            digest,
            FixedClock(FIXED_TIME),
            FixedNonce(["c" * 48, *[f"automatic-nonce-{index}" for index in range(20)]]),
        )
        prepared = bridge.prepare(*self.repo.cas(), automatic_decision(digest), FUTURE_TIME)
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "automatic-activation")
        service = TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root), FixedClock(FIXED_TIME))
        self.repo.deliver(service, claimed["claimId"], OUTPUT_BUNDLE_DIGEST)
        return prepared, claimed, self.repo.head()

    def test_rework_preserves_exact_attempt_and_only_commits_coordination_files(self) -> None:
        service, candidate_head = self.repo.delivered()
        before = self.repo.state()
        self.assertEqual(1, before["schemaVersion"])
        authorization = (self.repo.task_root / "authorization.json").read_bytes()
        documents = {name: (self.repo.task_root / name).read_bytes() for name in ("requirements.md", "plan.md", "implementation.md")}
        main_head = run("git", "rev-parse", "HEAD", cwd=self.repo.main)
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        result = self._rework(candidate_head, adapter)

        state = self.repo.state()
        attempt = state["lifecycle"]["rejectedAttempts"][0]
        self.assertEqual("reworked", result["status"])
        self.assertEqual(2, state["schemaVersion"])
        self.assertEqual("planning", state["lifecycle"]["phase"])
        self.assertEqual(before["lifecycle"]["epoch"] + 1, state["lifecycle"]["epoch"])
        self.assertEqual(before["lifecycle"]["claim"], attempt["claim"])
        self.assertEqual(before["lifecycle"]["delivery"], attempt["delivery"])
        self.assertEqual(candidate_head, attempt["candidateHead"])
        self.assertEqual(7, attempt["prNumber"])
        self.assertEqual(before["approval"], state["approval"])
        self.assertEqual(before["implementationAuthorization"], state["implementationAuthorization"])
        self.assertEqual(before["actionAuthorizationDigest"], state["actionAuthorizationDigest"])
        self.assertEqual("revoked", json.loads((self.repo.task_root / "offer.json").read_bytes())["status"])
        self.assertEqual(
            sorted((f"{self.repo.task_path}/offer.json", f"{self.repo.task_path}/task.json")),
            sorted(run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=self.repo.candidate).splitlines()),
        )
        self.assertEqual(authorization, (self.repo.task_root / "authorization.json").read_bytes())
        self.assertEqual(documents, {name: (self.repo.task_root / name).read_bytes() for name in documents})
        self.assertEqual(main_head, run("git", "rev-parse", "HEAD", cwd=self.repo.main))
        self.assertEqual(["snapshot", "snapshot"], [call[0] for call in adapter.calls])
        self.assertEqual("", run("git", "status", "--porcelain", cwd=self.repo.candidate))
        self.assertIsNotNone(service.runtime.read_claim_receipt(attempt["claim"]["claimId"]))

    def test_automatic_attempt_preserves_route_bundle_and_receipt_digests(self) -> None:
        prepared, claimed, candidate_head = self._automatic_delivery()
        runtime = RuntimeStore(self.repo.runtime_root)
        claim_receipt = runtime.read_claim_receipt(claimed["claimId"])
        activation_receipt = runtime.read_claim_activation_receipt(claimed["claimId"])
        self._rework(candidate_head)
        attempt = self.repo.state()["lifecycle"]["rejectedAttempts"][0]
        self.assertEqual(prepared["executionBundleDigest"], attempt["claim"]["executionBundleDigest"])
        self.assertEqual(prepared["routeDecisionDigest"], attempt["claim"]["routeDecisionDigest"])
        self.assertEqual(OUTPUT_BUNDLE_DIGEST, attempt["delivery"]["candidateOutputBundleDigest"])
        self.assertEqual(claim_receipt["receiptDigest"], attempt["claimReceiptDigest"])
        self.assertEqual(activation_receipt["receiptDigest"], attempt["activationReceiptDigest"])

    def test_fresh_automatic_attempt_uses_new_epoch_offer_claim_and_can_be_accepted(self) -> None:
        _, _, old_head = self._automatic_delivery()
        old_state = deepcopy(self.repo.state())
        self._rework(old_head)
        runtime = RuntimeStore(self.repo.runtime_root)
        with self.assertRaises(TaskError):
            runtime.read_capability(old_state["lifecycle"]["claim"]["offerId"])
        with self.assertRaises(TaskError):
            runtime.read_envelope(old_state["lifecycle"]["claim"]["envelopeId"])
        with self.assertRaisesRegex(TaskError, "CLAIM_MISMATCH"):
            TaskService(self.repo.candidate, self.repo.task_path, runtime, FixedClock(FIXED_TIME)).deliver(
                *self.repo.cas(), old_state["lifecycle"]["claim"]["claimId"], OUTPUT_BUNDLE_DIGEST
            )
        with self.assertRaisesRegex(TaskError, "candidate_head_changed"):
            accept_candidate(
                self.repo.main,
                self.repo.candidate,
                self.repo.task_path,
                self.repo.identity,
                7,
                old_head,
                ["contract"],
                make_review(self.repo.task_id, old_head, "acceptor", REVIEWER_DIGEST, "accepted", []),
                FakeGitHub(github_snapshot(self.repo, old_head)),
                "acceptor",
                True,
                runtime=RuntimeStore(self.repo.runtime_root),
            )
        digest = bundle_digest()
        bridge = TrustedMainRuntimeBridge(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            BUNDLE_ROOT,
            digest,
            FixedClock(FIXED_TIME),
            FixedNonce(["e" * 48, *[f"repair-nonce-{index}" for index in range(20)]]),
        )
        prepared = bridge.prepare(*self.repo.cas(), automatic_decision(digest), FUTURE_TIME)
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared, agentId="repair-agent", threadDigest="b" * 64), "repair-activation")
        self.assertNotEqual(old_state["lifecycle"]["offer"]["offerId"], claimed["offerId"])
        self.assertNotEqual(old_state["lifecycle"]["claim"]["claimId"], claimed["claimId"])
        self.assertNotEqual(old_state["lifecycle"]["claim"]["envelopeId"], claimed["envelopeId"])
        self.assertNotEqual(old_state["lifecycle"]["claim"]["activationId"], self.repo.state()["lifecycle"]["claim"]["activationId"])
        self.assertEqual(1, self.repo.state()["lifecycle"]["claim"]["epoch"])
        service = TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root), FixedClock(FIXED_TIME))
        self.repo.deliver(service, claimed["claimId"], "e" * 64)
        repaired_head = self.repo.head()
        accepted_review = make_review(self.repo.task_id, repaired_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        accepted = accept_candidate(
            self.repo.main,
            self.repo.candidate,
            self.repo.task_path,
            self.repo.identity,
            7,
            repaired_head,
            ["contract"],
            accepted_review,
            FakeGitHub(github_snapshot(self.repo, repaired_head)),
            "acceptor",
            True,
            runtime=RuntimeStore(self.repo.runtime_root),
        )
        self.assertTrue(accepted["merged"])

    def test_executor_and_non_repair_authorization_fail_before_external_or_tracked_write(self) -> None:
        candidate_head = self.repo.delivered()[1]
        adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "EXECUTOR_REWORK_FORBIDDEN"):
            self._rework(candidate_head, adapter, role="executor")
        self.assertEqual([], adapter.calls)

        other = TaskRepo()
        try:
            service = other.service()
            service.requirements_ready(*other.cas())
            service.approve_plan(*other.cas(), "decision-plan")
            service.authorize(
                *other.cas(),
                "decision-implementation",
                "implement_and_merge_on_acceptance",
                ["commit", "conditional_merge", "pr_update", "push", "ready_for_review"],
            )
            service.offer(*other.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
            envelope = service.handoff()["envelopeId"]
            claimed = service.claim(*other.cas(), envelope)
            other.deliver(service, claimed["claimId"])
            other_head = other.head()
            adapter = FakeGitHub(github_snapshot(other, other_head))
            review = make_review(other.task_id, other_head, "acceptor", REVIEWER_DIGEST, "rejected", ["repair-required"])
            with self.assertRaisesRegex(TaskError, "authorization_mismatch"):
                rework_candidate(
                    other.main,
                    other.candidate,
                    other.task_path,
                    other.identity,
                    7,
                    other_head,
                    review,
                    adapter,
                    "acceptor",
                    runtime=RuntimeStore(other.runtime_root),
                    clock=FixedClock(FIXED_TIME),
                )
            self.assertEqual([], adapter.calls)
        finally:
            other.close()

    def test_state_v1_and_v2_shapes_are_strict_and_attempt_relationships_are_bound(self) -> None:
        candidate_head = self.repo.delivered()[1]
        legacy = deepcopy(self.repo.state())
        legacy["lifecycle"]["rejectedAttempts"] = []
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(finalize_state(legacy))

        self._rework(candidate_head)
        state = deepcopy(self.repo.state())
        missing = deepcopy(state)
        missing["lifecycle"].pop("rejectedAttempts")
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(finalize_state(missing))
        mismatched = deepcopy(state)
        mismatched["lifecycle"]["rejectedAttempts"][0]["claim"]["claimId"] = "0" * 64
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(finalize_state(mismatched))
        wrong_task = deepcopy(state)
        wrong_task["lifecycle"]["rejectedAttempts"][0]["taskId"] = "TASK-OTHER"
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(finalize_state(wrong_task))

    def test_rejected_review_must_be_independent_exact_nonempty_unique_and_credential_free(self) -> None:
        candidate_head = self.repo.delivered()[1]
        original_head = self.repo.head()
        invalid = (
            self._review(candidate_head, reviewer_digest=SESSION_DIGEST),
            self._review(self.repo.base_sha),
            self._review(candidate_head, outcome="accepted", findings=[]),
            self._review(candidate_head, findings=[]),
            self._review(candidate_head, task_id="TASK-OTHER"),
        )
        for review in invalid:
            with self.subTest(review=review["reviewDigest"]):
                adapter = FakeGitHub(github_snapshot(self.repo, candidate_head))
                with self.assertRaisesRegex(TaskError, "INDEPENDENT_REJECTION_REQUIRED"):
                    self._rework(candidate_head, adapter, review=review)
                self.assertEqual([], adapter.calls)
                self.assertEqual(original_head, self.repo.head())
        for findings in (["duplicate", "duplicate"], ["Bearer fixture-secret"]):
            review = self._review(candidate_head)
            review["findings"] = findings
            unsigned = dict(review); unsigned.pop("reviewDigest")
            review["reviewDigest"] = digest_object(unsigned)
            with self.assertRaisesRegex(TaskError, "INVALID_REVIEW"):
                validate_review(review)

    def test_pr_identity_state_draft_merged_and_observation_drift_write_nothing(self) -> None:
        candidate_head = self.repo.delivered()[1]
        original = (self.repo.task_root / "task.json").read_bytes()
        mutations = {
            "repository": "example.test/other/repository",
            "prNumber": 8,
            "baseBranch": "other-base",
            "headBranch": "other-task",
            "headSha": self.repo.base_sha,
            "state": "closed",
            "draft": True,
            "mergedHead": self.repo.base_sha,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                snapshot = github_snapshot(self.repo, candidate_head)
                snapshot[field] = value
                with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
                    self._rework(candidate_head, FakeGitHub(snapshot))
                self.assertEqual(original, (self.repo.task_root / "task.json").read_bytes())

        class DriftAdapter(FakeGitHub):
            def snapshot(self, repository: str, pr_number: int):
                value = super().snapshot(repository, pr_number)
                if len(self.calls) == 2:
                    value["checks"] = []
                return value

        with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
            self._rework(candidate_head, DriftAdapter(github_snapshot(self.repo, candidate_head)))
        self.assertEqual(original, (self.repo.task_root / "task.json").read_bytes())

    def test_dirty_candidate_and_replay_are_rejected(self) -> None:
        candidate_head = self.repo.delivered()[1]
        dirty = self.repo.candidate / "dirty.txt"
        dirty.write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "candidate_head_changed"):
            self._rework(candidate_head)
        dirty.unlink()
        self._rework(candidate_head)
        commits = self.repo.commits()
        with self.assertRaisesRegex(TaskError, "candidate_head_changed"):
            self._rework(candidate_head)
        self.assertEqual(commits, self.repo.commits())

    def test_concurrent_rework_has_exactly_one_winner(self) -> None:
        candidate_head = self.repo.delivered()[1]
        barrier = threading.Barrier(2)
        outcomes: list[str] = []

        class BarrierAdapter(FakeGitHub):
            def snapshot(self, repository: str, pr_number: int):
                if not self.calls:
                    barrier.wait(timeout=10)
                return super().snapshot(repository, pr_number)

        def worker() -> None:
            try:
                result = self._rework(candidate_head, BarrierAdapter(github_snapshot(self.repo, candidate_head)))
                outcomes.append(result["status"])
            except TaskError as error:
                outcomes.append(error.code)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertEqual(1, outcomes.count("reworked"), outcomes)
        self.assertEqual(1, len(self.repo.state()["lifecycle"]["rejectedAttempts"]))

    def test_precommit_failure_recovers_exact_bytes_and_committed_failure_does_not_duplicate(self) -> None:
        candidate_head = self.repo.delivered()[1]
        task_before = (self.repo.task_root / "task.json").read_bytes()
        offer_before = (self.repo.task_root / "offer.json").read_bytes()

        def fail_written(phase: str) -> None:
            if phase == "written":
                raise RuntimeError("injected-written")

        with self.assertRaisesRegex(RuntimeError, "injected-written"):
            self._rework(candidate_head, failure_hook=fail_written)
        recovered = TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root), FixedClock(FIXED_TIME)).recover()
        self.assertEqual("recovered_rolled_back", recovered["status"])
        self.assertEqual(task_before, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(offer_before, (self.repo.task_root / "offer.json").read_bytes())

        def fail_committed(phase: str) -> None:
            if phase == "committed":
                raise RuntimeError("injected-committed")

        with self.assertRaisesRegex(RuntimeError, "injected-committed"):
            self._rework(candidate_head, failure_hook=fail_committed)
        recovered = TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root), FixedClock(FIXED_TIME)).recover()
        self.assertEqual("recovered_committed", recovered["status"])
        self.assertEqual(1, len(self.repo.state()["lifecycle"]["rejectedAttempts"]))

    def test_cli_uses_external_fake_github_and_returns_path_free_machine_result(self) -> None:
        candidate_head = self.repo.delivered()[1]
        review_path = self.repo.root / "review.json"
        review_path.write_bytes(canonical_bytes(self._review(candidate_head)))
        adapter_path = self.repo.root / "fake-github"
        snapshot = github_snapshot(self.repo, candidate_head)
        adapter_path.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            f"value = {snapshot!r}\n"
            "sys.stdout.write(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\\n')\n",
            encoding="utf-8",
        )
        adapter_path.chmod(0o755)
        command = [
            str(Path("canonical/payload/bin/gkd-task").resolve()),
            "rework",
            "--trusted-root", str(self.repo.main),
            "--candidate-root", str(self.repo.candidate),
            "--task-path", self.repo.task_path,
            "--repository", self.repo.identity,
            "--pr", "7",
            "--candidate-head", candidate_head,
            "--review-file", str(review_path),
            "--adapter-command", str(adapter_path),
            "--runtime-root", str(self.repo.runtime_root),
            "--actor-role", "main",
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        machine = json.loads(result.stdout)
        self.assertEqual("reworked", machine["status"])
        self.assertNotIn(str(self.repo.root), result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
