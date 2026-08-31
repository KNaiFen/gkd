from __future__ import annotations

import json
from pathlib import Path
import time
import unittest
from unittest import mock

from gkd_task.canonical import FixedClock, SystemNonce, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.locator import resolve_candidate
from gkd_task.migration import migrate_v1
from gkd_task.model import record_acceptance_state, record_completion_state
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import FIXED_TIME, REVIEWER_DIGEST, TaskRepo, make_legacy_v1, run


class RuntimeTransactionContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _failing(self, phase: str):
        def hook(current: str) -> None:
            if current == phase:
                raise RuntimeError(f"injected-{phase}")

        return self.repo.service(failure_hook=hook)

    def test_prepared_failure_recovers_exact_preimage_without_commit(self) -> None:
        service = self._failing("prepared")
        original = (self.repo.task_root / "task.json").read_bytes()
        count = self.repo.commits()
        with self.assertRaisesRegex(RuntimeError, "injected-prepared"):
            service.requirements_ready(*self.repo.cas())
        result = service.recover()
        self.assertEqual("recovered_rolled_back", result["status"])
        self.assertEqual(original, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(count, self.repo.commits())
        self.assertEqual("", run("git", "status", "--porcelain", cwd=self.repo.candidate))

    def test_written_failure_restores_exact_preimage_and_index(self) -> None:
        service = self._failing("written")
        original = (self.repo.task_root / "task.json").read_bytes()
        with self.assertRaisesRegex(RuntimeError, "injected-written"):
            service.requirements_ready(*self.repo.cas())
        self.assertNotEqual(original, (self.repo.task_root / "task.json").read_bytes())
        result = service.recover()
        self.assertEqual("recovered_rolled_back", result["status"])
        self.assertEqual(original, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual("", run("git", "status", "--porcelain", cwd=self.repo.candidate))

    def test_committed_failure_completes_without_replaying_commit(self) -> None:
        service = self._failing("committed")
        count = self.repo.commits()
        with self.assertRaisesRegex(RuntimeError, "injected-committed"):
            service.requirements_ready(*self.repo.cas())
        self.assertEqual(count + 1, self.repo.commits())
        result = service.recover()
        self.assertEqual("recovered_committed", result["status"])
        self.assertEqual(count + 1, self.repo.commits())

    def test_unprovable_bytes_create_doubt_marker_and_freeze(self) -> None:
        service = self._failing("written")
        with self.assertRaises(RuntimeError):
            service.requirements_ready(*self.repo.cas())
        (self.repo.task_root / "task.json").write_bytes(b"not-canonical\n")
        with self.assertRaisesRegex(TaskError, "transaction_in_doubt"):
            service.recover()
        self.assertTrue(service.runtime.doubt_path(service.key).is_file())
        with self.assertRaisesRegex(TaskError, "transaction_in_doubt"):
            service.transactions.ensure_safe()

    def test_recovery_preserves_unrelated_committed_file(self) -> None:
        unrelated = self.repo.candidate / "unrelated.txt"
        unrelated.write_text("keep\n", encoding="utf-8")
        run("git", "add", "unrelated.txt", cwd=self.repo.candidate)
        run("git", "commit", "-m", "unrelated", cwd=self.repo.candidate)
        service = self._failing("written")
        with self.assertRaises(RuntimeError):
            service.requirements_ready(*self.repo.cas())
        service.recover()
        self.assertEqual("keep\n", unrelated.read_text(encoding="utf-8"))
        self.assertEqual("", run("git", "status", "--porcelain", cwd=self.repo.candidate))

    def test_dirty_or_staged_unrelated_file_blocks_before_journal(self) -> None:
        path = self.repo.candidate / "unrelated.txt"
        path.write_text("dirty\n", encoding="utf-8")
        run("git", "add", "unrelated.txt", cwd=self.repo.candidate)
        service = self.repo.service()
        with self.assertRaisesRegex(TaskError, "WORKTREE_NOT_CLEAN"):
            service.requirements_ready(*self.repo.cas())
        self.assertIsNone(service.transactions._current_active())

    def test_lock_is_not_removed_merely_because_time_passes(self) -> None:
        runtime = RuntimeStore(self.repo.runtime_root)
        key = digest_object({"lock": "fixture"})
        with runtime.lock(key, digest_object({"owner": "first"}), timeout_seconds=0.1):
            started = time.monotonic()
            with self.assertRaisesRegex(TaskError, "LOCK_TIMEOUT"):
                with runtime.lock(key, digest_object({"owner": "second"}), timeout_seconds=0.05):
                    self.fail("second lock unexpectedly acquired")
            self.assertGreaterEqual(time.monotonic() - started, 0.04)

    def test_lock_owner_mismatch_fails_closed(self) -> None:
        runtime = RuntimeStore(self.repo.runtime_root)
        key = digest_object({"lock": "owner-loss"})
        lock_path = runtime.root / "locks" / f"{key}.lock" / "owner"
        with self.assertRaisesRegex(TaskError, "LOCK_OWNERSHIP_LOST"):
            with runtime.lock(key, digest_object({"owner": "first"}), timeout_seconds=0.1):
                lock_path.write_text("0" * 64 + "\n", encoding="ascii")


class LocatorAndMigrationContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()
        self.runtime = RuntimeStore(self.repo.runtime_root)

    def tearDown(self) -> None:
        self.repo.close()

    def _resolve(self, explicit: Path | None, current: Path | None) -> Path:
        return resolve_candidate(
            self.repo.identity,
            self.repo.task_id,
            self.repo.task_branch,
            self.repo.task_path,
            self.runtime,
            explicit,
            current,
        )

    def test_locator_prefers_and_validates_explicit_candidate(self) -> None:
        self.assertEqual(self.repo.candidate.resolve(), self._resolve(self.repo.candidate, self.repo.main))
        with self.assertRaisesRegex(TaskError, "CANDIDATE_IDENTITY_MISMATCH"):
            resolve_candidate("example.test/other/repo", self.repo.task_id, self.repo.task_branch, self.repo.task_path, self.runtime, self.repo.candidate, None)

    def test_locator_uses_current_git_root(self) -> None:
        nested = self.repo.candidate / "nested"
        nested.mkdir()
        self.assertEqual(self.repo.candidate.resolve(), self._resolve(None, nested))

    def test_locator_uses_unique_same_common_dir_full_branch(self) -> None:
        self.assertEqual(self.repo.candidate.resolve(), self._resolve(None, self.repo.main))

    def test_locator_falls_back_to_runtime_attachment(self) -> None:
        self.assertEqual(self.repo.candidate.resolve(), self._resolve(None, self.repo.root))

    def test_locator_zero_result_is_stable_worktree_missing(self) -> None:
        empty = RuntimeStore(self.repo.root / "empty-runtime")
        with self.assertRaisesRegex(TaskError, "worktree_missing"):
            resolve_candidate(self.repo.identity, self.repo.task_id, self.repo.task_branch, self.repo.task_path, empty, None, self.repo.root)

    def test_locator_multi_result_is_stable_worktree_ambiguous(self) -> None:
        with mock.patch("gkd_task.locator.unique_branch_worktree", side_effect=TaskError("worktree_ambiguous")):
            with self.assertRaisesRegex(TaskError, "worktree_ambiguous"):
                self._resolve(None, self.repo.main)

    def test_locator_rejects_symlinked_task_path(self) -> None:
        (self.repo.candidate / "alias").symlink_to("tasks", target_is_directory=True)
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_PATH"):
            resolve_candidate(self.repo.identity, self.repo.task_id, self.repo.task_branch, "alias/task-alpha", self.runtime, self.repo.candidate, None)

    def test_locator_rejects_explicit_symlink_candidate(self) -> None:
        candidate_link = self.repo.root / "candidate-link"
        candidate_link.symlink_to(self.repo.candidate, target_is_directory=True)
        with self.assertRaisesRegex(TaskError, "CANDIDATE_SYMLINK"):
            self._resolve(candidate_link, None)

    def test_live_doctor_checks_attachment_and_transaction_state(self) -> None:
        result = self.repo.service().doctor("live")
        self.assertEqual({"status": "valid", "mode": "live", "taskId": self.repo.task_id, "phase": "planning", "revision": 0}, result)

    def test_historical_doctor_rejects_active_state(self) -> None:
        with self.assertRaisesRegex(TaskError, "HISTORICAL_STATE_INCOMPLETE"):
            self.repo.service().doctor("historical")

    def test_active_v1_migration_creates_attachment_and_is_idempotent(self) -> None:
        state = self.repo.state()
        legacy = make_legacy_v1(state, str(self.repo.candidate.resolve()), False)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(legacy))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "legacy", cwd=self.repo.candidate)
        result = migrate_v1(
            self.repo.candidate,
            self.repo.task_path,
            self.runtime,
            self.repo.head(),
            state["revision"],
            FixedClock(FIXED_TIME),
            SystemNonce(),
        )
        self.assertEqual("migrated_v1", result["status"])
        count = self.repo.commits()
        repeated = migrate_v1(
            self.repo.candidate,
            self.repo.task_path,
            self.runtime,
            self.repo.head(),
            self.repo.state()["revision"],
            FixedClock(FIXED_TIME),
            SystemNonce(),
        )
        self.assertEqual("already_migrated", repeated["status"])
        self.assertEqual(count, self.repo.commits())
        attachment = self.runtime.read_attachment(self.repo.identity, self.repo.task_id, self.repo.task_branch)
        self.assertEqual(str(self.repo.candidate.resolve()), attachment["candidateRoot"])

    def test_attachment_write_failure_leaves_migration_retryable_without_commit(self) -> None:
        state = self.repo.state()
        legacy = make_legacy_v1(state, str(self.repo.candidate.resolve()), False)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(legacy))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "legacy", cwd=self.repo.candidate)
        before_head = self.repo.head()
        before_commits = self.repo.commits()
        with mock.patch.object(self.runtime, "write_attachment", side_effect=TaskError("RUNTIME_ATTACHMENT_WRITE_FAILED")):
            with self.assertRaisesRegex(TaskError, "RUNTIME_ATTACHMENT_WRITE_FAILED"):
                migrate_v1(
                    self.repo.candidate,
                    self.repo.task_path,
                    self.runtime,
                    before_head,
                    state["revision"],
                    FixedClock(FIXED_TIME),
                    SystemNonce(),
                )
        self.assertEqual(before_head, self.repo.head())
        self.assertEqual(before_commits, self.repo.commits())
        result = migrate_v1(
            self.repo.candidate,
            self.repo.task_path,
            self.runtime,
            before_head,
            state["revision"],
            FixedClock(FIXED_TIME),
            SystemNonce(),
        )
        self.assertEqual("migrated_v1", result["status"])

    def test_stale_migration_cas_preserves_runtime_bytes_and_remains_retryable(self) -> None:
        state = self.repo.state()
        legacy = make_legacy_v1(state, str(self.repo.candidate.resolve()), False)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(legacy))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "legacy", cwd=self.repo.candidate)
        current_head = self.repo.head()
        stale_head = run("git", "rev-parse", "HEAD^", cwd=self.repo.candidate)
        self.runtime.delete_attachment(self.repo.identity, self.repo.task_id, self.repo.task_branch)

        def runtime_bytes() -> dict[str, bytes]:
            return {
                str(path.relative_to(self.runtime.root)): path.read_bytes()
                for path in sorted(self.runtime.root.rglob("*"))
                if path.is_file()
            }

        before = runtime_bytes()
        with self.assertRaisesRegex(TaskError, "HEAD_MISMATCH"):
            migrate_v1(
                self.repo.candidate,
                self.repo.task_path,
                self.runtime,
                stale_head,
                state["revision"],
                FixedClock(FIXED_TIME),
                SystemNonce(),
            )
        self.assertEqual(current_head, self.repo.head())
        self.assertEqual(before, runtime_bytes())

        with self.assertRaisesRegex(TaskError, "REVISION_MISMATCH"):
            migrate_v1(
                self.repo.candidate,
                self.repo.task_path,
                self.runtime,
                current_head,
                state["revision"] + 1,
                FixedClock(FIXED_TIME),
                SystemNonce(),
            )
        self.assertEqual(current_head, self.repo.head())
        self.assertEqual(before, runtime_bytes())

        result = migrate_v1(
            self.repo.candidate,
            self.repo.task_path,
            self.runtime,
            current_head,
            state["revision"],
            FixedClock(FIXED_TIME),
            SystemNonce(),
        )
        self.assertEqual("migrated_v1", result["status"])

    def test_active_v1_missing_worktree_fails_closed(self) -> None:
        state = self.repo.state()
        legacy = make_legacy_v1(state, str(self.repo.root / "missing"), False)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(legacy))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "legacy", cwd=self.repo.candidate)
        with self.assertRaisesRegex(TaskError, "worktree_missing"):
            migrate_v1(self.repo.candidate, self.repo.task_path, self.runtime, self.repo.head(), state["revision"], FixedClock(FIXED_TIME), SystemNonce())

if __name__ == "__main__":
    unittest.main()
