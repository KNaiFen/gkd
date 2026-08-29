from __future__ import annotations

from copy import deepcopy
import json
import unittest

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_role.project import stage_project
from gkd_task.acceptance import _validate_fixed_candidate, accept_candidate, make_review
from gkd_task.canonical import FixedClock, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.gitops import changed_paths
from gkd_task.model import advance_state, finalize_state, read_state, validate_state
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.runtime_bridge.helpers import BUNDLE_ROOT, automatic_decision, bundle_digest, spawn_result
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, REVIEWER_DIGEST, FakeGitHub, TaskRepo, github_snapshot, planning_documents, run


OUTPUT_BUNDLE_DIGEST = "d" * 64


class GateRepairContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _automatic_claim(self) -> tuple[TaskService, str]:
        self.repo.ready_and_authorized()
        digest = bundle_digest()
        stage_project(BUNDLE_ROOT, digest, self.repo.main, self.repo.production)
        bridge = TrustedMainRuntimeBridge(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            BUNDLE_ROOT,
            digest,
            FixedClock(FIXED_TIME),
        )
        prepared = bridge.prepare(
            *self.repo.cas(),
            automatic_decision(digest, self.repo.state()["repository"]["policy"]),
            FUTURE_TIME,
            self.repo.main,
            self.repo.production,
        )
        claim = bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "gate-repair")
        return TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root)), claim["claimId"]

    def test_history_uses_revisions_for_order_and_rejects_fixed_record_drift(self) -> None:
        first = advance_state(self.repo.state(), "requirements_ready", FUTURE_TIME, self.repo.base_sha, {})
        second = advance_state(first, "plan_proposed", FIXED_TIME, self.repo.base_sha, {})
        validate_state(second)
        self.assertEqual([0, 1, 2], [event["revision"] for event in second["history"]])

        self.repo.ready_and_authorized()
        state = deepcopy(self.repo.state())
        state["history"][-1]["recordDigest"] = "e" * 64
        state = finalize_state(state)
        (self.repo.task_root / "task.json").write_bytes(canonical_bytes(state))
        run("git", "add", f"{self.repo.task_path}/task.json", cwd=self.repo.candidate)
        run("git", "commit", "-m", "tamper history record", cwd=self.repo.candidate)
        with self.assertRaisesRegex(TaskError, "TASK_HISTORY_DRIFT"):
            read_state(self.repo.task_root / "task.json", self.repo.task_root)

        other = TaskRepo()
        try:
            other.ready_and_authorized()
            state = deepcopy(other.state())
            state["history"][-1]["head"] = other.base_sha
            state = finalize_state(state)
            (other.task_root / "task.json").write_bytes(canonical_bytes(state))
            run("git", "add", f"{other.task_path}/task.json", cwd=other.candidate)
            run("git", "commit", "-m", "tamper history head", cwd=other.candidate)
            with self.assertRaisesRegex(TaskError, "TASK_HISTORY_DRIFT"):
                read_state(other.task_root / "task.json", other.task_root)
        finally:
            other.close()

    def test_planning_refresh_rebinds_documents_and_invalidates_stale_inputs(self) -> None:
        service, _ = self.repo.offer_and_claim()
        service.revoke(*self.repo.cas(), "refresh-planning")
        package = planning_documents({"Scope": "Changed material contract."}, notes="Refreshed planning notes.")
        package["requirements.md"] = package["requirements.md"].replace("deterministic fixture", "refreshed fixture")
        package["implementation.md"] = package["implementation.md"].replace("standard-library components", "refreshed standard-library components")
        for name, content in package.items():
            (self.repo.task_root / name).write_text(content, encoding="utf-8")
        run("git", "add", self.repo.task_path, cwd=self.repo.candidate)
        run("git", "commit", "-m", "refresh planning sources", "--", self.repo.task_path, cwd=self.repo.candidate)

        raw_state = read_state(self.repo.task_root / "task.json")
        refresh = TaskService(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            FixedClock(FIXED_TIME),
            allow_document_drift=True,
        )
        refreshed = refresh.refresh_planning(self.repo.head(), raw_state["revision"])
        self.assertEqual("planning_refreshed", refreshed["status"])
        state = self.repo.state()
        self.assertEqual("draft", state["documents"]["requirements"]["status"])
        self.assertEqual("proposed", state["documents"]["plan"]["status"])
        self.assertEqual([2, 2, 2], [state["documents"][name]["documentRevision"] for name in ("requirements", "plan", "implementation")])
        self.assertIsNone(state["approval"])
        self.assertIsNone(state["implementationAuthorization"])
        self.assertFalse((self.repo.task_root / "authorization.json").exists())
        self.assertFalse((self.repo.task_root / "offer.json").exists())
        with self.assertRaisesRegex(TaskError, "PLANNING_REFRESH_NOT_NEEDED"):
            refresh.refresh_planning(*self.repo.cas())

    def test_automatic_delivery_binds_fixed_tree_artifacts_for_acceptance(self) -> None:
        service, claim_id = self._automatic_claim()
        result = self.repo.deliver(service, claim_id, OUTPUT_BUNDLE_DIGEST)
        state = self.repo.state()
        delivery = state["lifecycle"]["delivery"]
        implementation_head = delivery["implementationHead"]
        document_commit = delivery["deliveryDocumentCommit"]
        artifact_paths = {
            f"{self.repo.task_path}/result-manifest.json",
            f"{self.repo.task_path}/verification-results.json",
            f"{self.repo.task_path}/verification-evidence.json",
        }
        self.assertTrue(artifact_paths.issubset(changed_paths(self.repo.candidate, implementation_head)))
        self.assertEqual([f"{self.repo.task_path}/delivery.md"], changed_paths(self.repo.candidate, document_commit))
        self.assertEqual([f"{self.repo.task_path}/task.json"], changed_paths(self.repo.candidate, result["head"]))
        self.assertEqual(implementation_head, run("git", "rev-parse", f"{document_commit}^", cwd=self.repo.candidate))
        sidecar = json.loads((self.repo.task_root / "result-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("implementationHead", sidecar)
        self.assertEqual(OUTPUT_BUNDLE_DIGEST, sidecar["candidateOutputBundleDigest"])
        runtime = RuntimeStore(self.repo.runtime_root)
        _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, result["head"], runtime)
        review = make_review(self.repo.task_id, result["head"], "acceptor", REVIEWER_DIGEST, "accepted", [])
        accepted = accept_candidate(
            self.repo.main,
            self.repo.candidate,
            self.repo.task_path,
            self.repo.identity,
            7,
            result["head"],
            ["contract"],
            review,
            FakeGitHub(github_snapshot(self.repo, result["head"])),
            "acceptor",
            False,
            runtime,
        )
        self.assertEqual("accepted", accepted["status"])

    def test_automatic_delivery_rejects_result_drift_without_state_write(self) -> None:
        service, claim_id = self._automatic_claim()
        self.repo.prepare_automatic_artifacts(OUTPUT_BUNDLE_DIGEST)
        results_path = self.repo.task_root / "verification-results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        results["baseSha"] = "e" * 40
        results_path.write_bytes(canonical_bytes(results))
        run("git", "add", f"{self.repo.task_path}/verification-results.json", cwd=self.repo.candidate)
        run("git", "commit", "--amend", "--no-edit", cwd=self.repo.candidate)
        document_path, document_digest = self.repo.prepare_delivery_document()
        before = self.repo.state()["revision"]
        with self.assertRaisesRegex(TaskError, "INVALID_VERIFIER_RESULTS"):
            service.deliver(
                *self.repo.cas(),
                claim_id,
                OUTPUT_BUNDLE_DIGEST,
                document_path,
                document_digest,
                f"{self.repo.task_path}/verification-results.json",
                f"{self.repo.task_path}/verification-evidence.json",
            )
        self.assertEqual(before, self.repo.state()["revision"])

    def test_automatic_delivery_rejects_lane_profile_drift_without_state_write(self) -> None:
        service, claim_id = self._automatic_claim()
        self.repo.prepare_automatic_artifacts(OUTPUT_BUNDLE_DIGEST)
        manifest_path = self.repo.task_root / "result-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["profile"] = "watcher"
        manifest["manifestDigest"] = digest_object({key: value for key, value in manifest.items() if key != "manifestDigest"})
        manifest_path.write_bytes(canonical_bytes(manifest))
        run("git", "add", f"{self.repo.task_path}/result-manifest.json", cwd=self.repo.candidate)
        run("git", "commit", "--amend", "--no-edit", cwd=self.repo.candidate)
        document_path, document_digest = self.repo.prepare_delivery_document()
        before = self.repo.state()["revision"]
        with self.assertRaisesRegex(TaskError, "INVALID_RESULT_MANIFEST"):
            service.deliver(
                *self.repo.cas(),
                claim_id,
                OUTPUT_BUNDLE_DIGEST,
                document_path,
                document_digest,
                f"{self.repo.task_path}/verification-results.json",
                f"{self.repo.task_path}/verification-evidence.json",
            )
        self.assertEqual(before, self.repo.state()["revision"])

    def test_automatic_delivery_requires_artifacts_in_the_implementation_commit(self) -> None:
        service, claim_id = self._automatic_claim()
        document_path, document_digest = self.repo.prepare_delivery_document()
        before = self.repo.state()["revision"]
        with self.assertRaisesRegex(TaskError, "AUTOMATIC_DELIVERY_ARTIFACT_REQUIRED"):
            service.deliver(
                *self.repo.cas(),
                claim_id,
                OUTPUT_BUNDLE_DIGEST,
                document_path,
                document_digest,
                f"{self.repo.task_path}/verification-results.json",
                f"{self.repo.task_path}/verification-evidence.json",
            )
        self.assertEqual(before, self.repo.state()["revision"])


if __name__ == "__main__":
    unittest.main()
