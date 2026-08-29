from __future__ import annotations

from copy import deepcopy
import json
import unittest

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_role.project import stage_project
from gkd_task.canonical import FixedClock, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.model import advance_state, finalize_state, read_state, validate_state
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.runtime_bridge.helpers import BUNDLE_ROOT, automatic_decision, bundle_digest, spawn_result
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo, planning_documents, run


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

    def _manifest(self, **overrides: str) -> dict[str, str | int]:
        state = self.repo.state()
        value: dict[str, str | int] = {
            "schemaVersion": 1,
            "kind": "automatic-delivery-result-manifest",
            "taskId": state["taskId"],
            "repository": state["repository"]["identity"],
            "taskBranch": state["repository"]["taskBranch"],
            "taskPath": state["repository"]["taskPath"],
            "baseSha": state["repository"]["baseSha"],
            "implementationHead": self.repo.head(),
            "candidateOutputBundleDigest": OUTPUT_BUNDLE_DIGEST,
            "verifierResultDigest": "a" * 64,
            "evidenceDigest": "b" * 64,
        }
        value.update(overrides)
        value["manifestDigest"] = digest_object(value)
        return value

    def _commit_manifest(self, value: dict[str, str | int], canonical: bool = True) -> None:
        path = self.repo.task_root / "result-manifest.json"
        raw = canonical_bytes(value) if canonical else json.dumps(value, sort_keys=True, indent=2).encode("utf-8")
        path.write_bytes(raw)
        relative = f"{self.repo.task_path}/result-manifest.json"
        run("git", "add", relative, cwd=self.repo.candidate)
        run("git", "commit", "-m", "prepare result manifest", "--", relative, cwd=self.repo.candidate)

    def test_history_revision_orders_rollback_and_integrity_rejects_tampering(self) -> None:
        first = advance_state(self.repo.state(), "requirements_ready", FUTURE_TIME, self.repo.base_sha, {})
        second = advance_state(first, "plan_proposed", FIXED_TIME, self.repo.base_sha, {})
        validate_state(second)
        self.assertEqual([0, 1, 2], [event["revision"] for event in second["history"]])

        for field, value in (("revision", 1), ("head", "e" * 40), ("recordDigest", "e" * 64)):
            with self.subTest(field=field):
                tampered = deepcopy(second)
                tampered["history"][-1][field] = value
                with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE|TASK_STATE_TAMPERED"):
                    validate_state(tampered)

    def test_planning_refresh_rebinds_documents_and_refuses_post_claim_drift(self) -> None:
        package = planning_documents({"Scope": "Changed material contract."}, notes="Refreshed planning notes.")
        package["requirements.md"] = package["requirements.md"].replace("deterministic fixture", "refreshed fixture")
        package["implementation.md"] = package["implementation.md"].replace("standard-library components", "refreshed standard-library components")
        for name, content in package.items():
            (self.repo.task_root / name).write_text(content, encoding="utf-8")
        run("git", "add", self.repo.task_path, cwd=self.repo.candidate)
        run("git", "commit", "-m", "refresh planning sources", "--", self.repo.task_path, cwd=self.repo.candidate)

        raw_state = read_state(self.repo.task_root / "task.json")
        service = TaskService(
            self.repo.candidate,
            self.repo.task_path,
            RuntimeStore(self.repo.runtime_root),
            FixedClock(FIXED_TIME),
            allow_document_drift=True,
        )
        result = service.refresh_planning(self.repo.head(), raw_state["revision"])
        self.assertEqual("planning_refreshed", result["status"])
        refreshed = self.repo.state()
        self.assertEqual("draft", refreshed["documents"]["requirements"]["status"])
        self.assertEqual("proposed", refreshed["documents"]["plan"]["status"])
        self.assertEqual([2, 2, 2], [refreshed["documents"][name]["documentRevision"] for name in ("requirements", "plan", "implementation")])

        self.repo.offer_and_claim()
        package["plan.md"] = package["plan.md"].replace("Changed material contract.", "Late planning drift.")
        (self.repo.task_root / "plan.md").write_text(package["plan.md"], encoding="utf-8")
        run("git", "add", f"{self.repo.task_path}/plan.md", cwd=self.repo.candidate)
        run("git", "commit", "-m", "late planning drift", "--", f"{self.repo.task_path}/plan.md", cwd=self.repo.candidate)
        raw_state = read_state(self.repo.task_root / "task.json")
        before = self.repo.head()
        with self.assertRaisesRegex(TaskError, "INVALID_TRANSITION"):
            service.refresh_planning(before, raw_state["revision"])
        self.assertEqual(before, self.repo.head())

    def test_automatic_delivery_requires_canonical_precommitted_bound_sidecar(self) -> None:
        service, claim_id = self._automatic_claim()
        document_path, document_digest = self.repo.prepare_delivery_document()
        revision = self.repo.state()["revision"]
        with self.assertRaisesRegex(TaskError, "RESULT_MANIFEST_REQUIRED"):
            service.deliver(*self.repo.cas(), claim_id, OUTPUT_BUNDLE_DIGEST, document_path, document_digest)
        self.assertEqual(revision, self.repo.state()["revision"])

    def test_automatic_delivery_rejects_sidecar_binding_and_integrity_drift(self) -> None:
        mutations = {
            "taskId": "TASK-OTHER",
            "taskPath": "tasks/other",
            "baseSha": "e" * 40,
            "implementationHead": "e" * 40,
            "candidateOutputBundleDigest": "e" * 64,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                repo = TaskRepo()
                try:
                    self.repo, previous = repo, self.repo
                    service, claim_id = self._automatic_claim()
                    self._commit_manifest(self._manifest(**{field: value}))
                    document_path, document_digest = self.repo.prepare_delivery_document()
                    revision = self.repo.state()["revision"]
                    with self.assertRaisesRegex(TaskError, "RESULT_MANIFEST_BINDING_MISMATCH"):
                        service.deliver(*self.repo.cas(), claim_id, OUTPUT_BUNDLE_DIGEST, document_path, document_digest)
                    self.assertEqual(revision, self.repo.state()["revision"])
                finally:
                    self.repo = previous
                    repo.close()

        service, claim_id = self._automatic_claim()
        invalid = self._manifest()
        invalid["evidenceDigest"] = "e" * 64
        self._commit_manifest(invalid)
        document_path, document_digest = self.repo.prepare_delivery_document()
        with self.assertRaisesRegex(TaskError, "INVALID_RESULT_MANIFEST"):
            service.deliver(*self.repo.cas(), claim_id, OUTPUT_BUNDLE_DIGEST, document_path, document_digest)

        repo = TaskRepo()
        previous = self.repo
        self.repo = repo
        try:
            service, claim_id = self._automatic_claim()
            self._commit_manifest(self._manifest(), canonical=False)
            document_path, document_digest = self.repo.prepare_delivery_document()
            with self.assertRaisesRegex(TaskError, "INVALID_RESULT_MANIFEST"):
                service.deliver(*self.repo.cas(), claim_id, OUTPUT_BUNDLE_DIGEST, document_path, document_digest)
        finally:
            self.repo = previous
            repo.close()

    def test_automatic_delivery_keeps_delivery_record_compatible_and_acceptance_revalidates(self) -> None:
        service, claim_id = self._automatic_claim()
        delivered = self.repo.deliver(service, claim_id, OUTPUT_BUNDLE_DIGEST)
        delivery = self.repo.state()["lifecycle"]["delivery"]
        self.assertEqual(
            {"implementationHead", "deliveryDocumentCommit", "deliveryDocumentPath", "deliveryDocumentDigest", "claimId", "deliveredAt", "executionBundleDigest", "candidateOutputBundleDigest", "routeDecisionDigest"},
            set(delivery),
        )
        self.assertEqual(delivery["implementationHead"], run("git", "rev-parse", f"{delivery['deliveryDocumentCommit']}^^", cwd=self.repo.candidate))
        self.assertEqual(delivered["head"], self.repo.head())
        from gkd_task.acceptance import _validate_fixed_candidate

        _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], RuntimeStore(self.repo.runtime_root))


if __name__ == "__main__":
    unittest.main()
