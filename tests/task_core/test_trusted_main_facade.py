from __future__ import annotations

from pathlib import Path
import unittest

from gkd_bundle import verify_bundle_root
from gkd_ci.github import GitHubObservation
from gkd_main.orchestrator import TrustedMainCIFacade, TrustedMainOrchestrator
from gkd_role.project import stage_project
from gkd_task.acceptance import make_review
from gkd_task.errors import TaskError
from gkd_task.orchestrator import resolve_trusted_task_context
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import (
    CONFIG_DIGEST,
    FUTURE_TIME,
    REVIEWER_DIGEST,
    ROLE_DIGEST,
    FakeGitHub,
    TaskRepo,
    github_snapshot,
)


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = ROOT / "canonical" / "payload"


class _DiscoveringGitHub(FakeGitHub):
    def __init__(self, snapshot: dict[str, object], pull_requests: list[int]) -> None:
        super().__init__(snapshot)
        self.pull_requests = pull_requests

    def find_open_pull_requests(self, repository: str, head_branch: str) -> list[int]:
        self.calls.append(("pulls", repository, head_branch))
        return list(self.pull_requests)


class _MonitorGitHub:
    def __init__(self, expected_head: str, base_branch: str, repository: str) -> None:
        self.expected_head = expected_head
        self.base_branch = base_branch
        self.repository = repository

    def observe(self, repository: str, pull_request: int, expected_head: str, required_checks: tuple[str, ...]):
        del pull_request, required_checks
        return GitHubObservation(
            base_branch=self.base_branch,
            checks=(("contract", "success"),),
            head_branch="task/task-alpha",
            head_sha=expected_head,
            pull_request=7,
            repository=repository,
            state="open",
        )


class TrustedMainFacadeContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()
        digest = verify_bundle_root(BUNDLE_ROOT)["contentDigest"]
        stage_project(BUNDLE_ROOT, digest, self.repo.main, self.repo.production)
        self.service = self.repo.ready_and_authorized()
        self.service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        envelope = self.service.handoff()["envelopeId"]
        self.service.claim(*self.repo.cas(), envelope)
        self.repo.prepare_delivery_document()
        self.context = resolve_trusted_task_context(
            self.repo.candidate,
            BUNDLE_ROOT,
            runtime=RuntimeStore(self.repo.runtime_root),
        )

    def tearDown(self) -> None:
        self.repo.close()

    def test_delivery_derives_document_and_claim_facts(self) -> None:
        result = TrustedMainOrchestrator(self.context).deliver()
        self.assertEqual("delivered", result["status"])
        self.assertEqual("delivered", self.repo.state()["lifecycle"]["phase"])

    def test_accept_derives_unique_pr_and_keeps_merge_explicit(self) -> None:
        TrustedMainOrchestrator(self.context).deliver()
        candidate_head = self.repo.head()
        orchestrator = TrustedMainOrchestrator(
            self.context,
            _DiscoveringGitHub(github_snapshot(self.repo, candidate_head), [7]),
        )
        review = make_review(self.repo.task_id, candidate_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        result = orchestrator.accept(review)
        self.assertFalse(result["merged"])

    def test_multiple_prs_fail_before_snapshot_or_write(self) -> None:
        adapter = _DiscoveringGitHub(github_snapshot(self.repo, self.repo.head()), [7, 8])
        orchestrator = TrustedMainOrchestrator(self.context, adapter)
        orchestrator.deliver()
        candidate_head = self.repo.head()
        review = make_review(self.repo.task_id, candidate_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        with self.assertRaisesRegex(TaskError, "PR_NOT_UNIQUE"):
            orchestrator.accept(review)
        self.assertEqual(["pulls"], [call[0] for call in adapter.calls])

    def test_ci_derives_repository_and_relative_policy(self) -> None:
        expected_head = self.repo.head()
        result = TrustedMainCIFacade(
            self.repo.main,
            _MonitorGitHub(expected_head, self.repo.base_branch, self.repo.identity),
        ).monitor(7, expected_head, timeout_seconds=1, poll_interval_seconds=1)
        self.assertEqual("success", result["outcome"])


if __name__ == "__main__":
    unittest.main()
