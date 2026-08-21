from __future__ import annotations

import unittest

from gkd_task.acceptance import accept_candidate, make_review
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import REVIEWER_DIGEST, FakeGitHub, TaskRepo, github_snapshot, run


class FinalizationAcceptanceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_synchronized_main_is_revalidated_between_fixed_head_snapshots(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        self.repo.deliver(service, claim_id)
        candidate_head = self.repo.head()
        review = make_review(self.repo.task_id, candidate_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        repo = self.repo

        class MainDriftAdapter(FakeGitHub):
            def snapshot(self, repository: str, pr_number: int):
                result = super().snapshot(repository, pr_number)
                if len(self.calls) == 1:
                    path = repo.main / "late-main-drift.txt"
                    path.write_text("drift\n", encoding="utf-8")
                    run("git", "add", "late-main-drift.txt", cwd=repo.main)
                    run("git", "commit", "-m", "late main drift", cwd=repo.main)
                return result

        adapter = MainDriftAdapter(github_snapshot(self.repo, candidate_head))
        with self.assertRaisesRegex(TaskError, "TRUSTED_CONTEXT_INVALID"):
            accept_candidate(
                self.repo.main,
                self.repo.candidate,
                self.repo.task_path,
                self.repo.identity,
                7,
                candidate_head,
                ["contract"],
                review,
                adapter,
                "acceptor",
                True,
                runtime=RuntimeStore(self.repo.runtime_root),
            )
        self.assertNotIn("merge", [call[0] for call in adapter.calls])


if __name__ == "__main__":
    unittest.main()
