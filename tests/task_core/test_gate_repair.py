from __future__ import annotations

from copy import deepcopy
import unittest

from gkd_task.canonical import FixedClock, sha256_bytes
from gkd_task.errors import TaskError
from gkd_task.model import advance_state, finalize_state, validate_state
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo, planning_documents, run


class GateRepairContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_logical_order_survives_wall_clock_rollback_and_tamper_is_rejected(self) -> None:
        state = self.repo.state()
        first = advance_state(state, "requirements_ready", FUTURE_TIME, self.repo.base_sha, {})
        second = advance_state(first, "plan_proposed", FIXED_TIME, self.repo.base_sha, {})
        self.assertEqual([0, 1, 2], [event["logicalOrder"] for event in second["history"]])
        validate_state(second)
        tampered = deepcopy(second)
        tampered["history"][2]["logicalOrder"] = 1
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(finalize_state(tampered))

    def test_planning_refresh_rebinds_documents_and_is_fail_closed_after_claim(self) -> None:
        package = planning_documents(notes="Refreshed planning package.")
        for name, content in package.items():
            (self.repo.task_root / name).write_text(content, encoding="utf-8")
        run("git", "add", self.repo.task_path, cwd=self.repo.candidate)
        run("git", "commit", "-m", "edit planning documents", "--", self.repo.task_path, cwd=self.repo.candidate)
        service = TaskService(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            FixedClock(FIXED_TIME),
            allow_document_drift=True,
        )
        result = service.refresh_planning(self.repo.head(), 0)
        self.assertEqual("planning_refreshed", result["status"])
        self.assertEqual("draft", self.repo.state()["documents"]["requirements"]["status"])
        self.repo.offer_and_claim()
        (self.repo.task_root / "implementation.md").write_text("# drift\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "DOCUMENT_DIGEST_DRIFT|INVALID_PLANNING_DOCUMENT"):
            self.repo.state()

    def test_automatic_delivery_rejects_missing_manifest_without_state_write(self) -> None:
        from tests.runtime_bridge.helpers import ready_bridge, spawn_result
        bridge, prepared = ready_bridge(self.repo)
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "manifest-test")
        path = self.repo.task_root / "delivery.md"
        path.write_text("# Delivery\n", encoding="utf-8")
        relative = f"{self.repo.task_path}/delivery.md"
        run("git", "add", relative, cwd=self.repo.candidate)
        run("git", "commit", "-m", "delivery without manifest", "--", relative, cwd=self.repo.candidate)
        before = self.repo.cas()
        with self.assertRaisesRegex(TaskError, "RESULT_MANIFEST_REQUIRED"):
            TaskService(
                self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root)
            ).deliver(*before, claimed["claimId"], "d" * 64, relative, sha256_bytes(path.read_bytes()))
        self.assertEqual(before, self.repo.cas())
