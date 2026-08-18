from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from gkd_task.canonical import canonical_bytes
from gkd_task.documents import PLAN_MATERIAL_SECTIONS, inspect_package, parse_sections
from gkd_task.errors import TaskError
from gkd_task.model import finalize_state, read_state, validate_state
from tests.task_core.helpers import TaskRepo, planning_documents


class PlanningContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_bootstrap_keeps_main_clean_and_writes_only_candidate(self) -> None:
        self.assertEqual("", __import__("subprocess").check_output(["git", "-C", str(self.repo.main), "status", "--porcelain"], text=True))
        self.assertFalse((self.repo.main / self.repo.task_path).exists())
        self.assertTrue((self.repo.task_root / "task.json").is_file())

    def test_initial_gates_are_three_separate_facts(self) -> None:
        state = self.repo.state()
        self.assertEqual("draft", state["documents"]["requirements"]["status"])
        self.assertEqual("proposed", state["documents"]["plan"]["status"])
        self.assertIsNone(state["approval"])
        self.assertIsNone(state["implementationAuthorization"])

    def test_requirements_ready_does_not_approve_or_authorize(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        state = self.repo.state()
        self.assertEqual("ready", state["documents"]["requirements"]["status"])
        self.assertIsNone(state["approval"])
        self.assertIsNone(state["implementationAuthorization"])

    def test_plan_approval_requires_requirements_ready(self) -> None:
        with self.assertRaisesRegex(TaskError, "REQUIREMENTS_NOT_READY"):
            self.repo.service().approve_plan(*self.repo.cas(), "decision")

    def test_plan_only_approval_leaves_implementation_unauthorized(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        service.approve_plan(*self.repo.cas(), "decision")
        state = self.repo.state()
        self.assertIsNotNone(state["approval"])
        self.assertIsNone(state["implementationAuthorization"])

    def test_combined_explicit_decision_can_approve_and_authorize(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        actions = ["commit", "ready_for_review"]
        result = service.approve_plan(
            *self.repo.cas(),
            "combined-decision",
            authorize_implementation=True,
            mode="implement_only",
            allowed_actions=actions,
        )
        self.assertTrue(result["authorizedTogether"])
        self.assertIsNotNone(self.repo.state()["implementationAuthorization"])

    def test_nonmaterial_notes_change_retains_approval_and_plan_version(self) -> None:
        service = self.repo.ready_and_authorized()
        before = self.repo.state()
        values = planning_documents(notes="Changed internal note only.")
        plan_file = self.repo.root / "new-plan.md"
        plan_file.write_text(values["plan.md"], encoding="utf-8")
        service.propose_plan(*self.repo.cas(), plan_file)
        after = self.repo.state()
        self.assertEqual(before["documents"]["plan"]["version"], after["documents"]["plan"]["version"])
        self.assertNotEqual(before["documents"]["plan"]["digest"], after["documents"]["plan"]["digest"])
        self.assertEqual(before["documents"]["plan"]["materialDigest"], after["documents"]["plan"]["materialDigest"])
        self.assertIsNotNone(after["approval"])
        self.assertIsNotNone(after["implementationAuthorization"])

    def test_every_material_section_invalidates_approval_and_authorization(self) -> None:
        for section in PLAN_MATERIAL_SECTIONS:
            with self.subTest(section=section):
                repo = TaskRepo(identity=f"example.test/team/{section.lower().replace(' ', '-')}")
                try:
                    service = repo.ready_and_authorized()
                    values = planning_documents({section: f"Changed {section}."})
                    plan_file = repo.root / "changed-plan.md"
                    plan_file.write_text(values["plan.md"], encoding="utf-8")
                    service.propose_plan(*repo.cas(), plan_file)
                    state = repo.state()
                    self.assertEqual("proposed", state["documents"]["plan"]["status"])
                    self.assertIsNone(state["approval"])
                    self.assertIsNone(state["implementationAuthorization"])
                    self.assertIsNone(state["actionAuthorizationDigest"])
                    self.assertFalse((repo.task_root / "authorization.json").exists())
                finally:
                    repo.close()

    def test_direct_state_tamper_is_rejected(self) -> None:
        path = self.repo.task_root / "task.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["revision"] += 1
        path.write_bytes(canonical_bytes(value))
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE|TASK_STATE_TAMPERED"):
            read_state(path, self.repo.task_root)

    def test_noncanonical_state_bytes_are_rejected(self) -> None:
        path = self.repo.task_root / "task.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            read_state(path, self.repo.task_root)

    def test_unknown_state_field_is_rejected(self) -> None:
        value = self.repo.state()
        value["unknown"] = True
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(value)

    def test_phase_matrix_rejects_delivered_fields_relabelled_as_planning(self) -> None:
        self.repo.delivered()
        value = deepcopy(self.repo.state())
        value["lifecycle"]["phase"] = "planning"
        value = finalize_state(value)
        with self.assertRaisesRegex(TaskError, "INVALID_TASK_STATE"):
            validate_state(value)

    def test_credential_shaped_decision_reference_is_rejected(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        with self.assertRaisesRegex(TaskError, "INVALID_DECISION_REF"):
            service.approve_plan(*self.repo.cas(), "ghp_" + "A" * 32)

    def test_document_digest_drift_is_rejected(self) -> None:
        (self.repo.task_root / "implementation.md").write_text("# changed\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "INVALID_PLANNING_DOCUMENT|DOCUMENT_DIGEST_DRIFT"):
            read_state(self.repo.task_root / "task.json", self.repo.task_root)

    def test_fixed_head_and_revision_cas_reject_stale_values(self) -> None:
        service = self.repo.service()
        stale_head, stale_revision = self.repo.cas()
        service.requirements_ready(stale_head, stale_revision)
        with self.assertRaisesRegex(TaskError, "HEAD_MISMATCH|REVISION_MISMATCH"):
            service.approve_plan(stale_head, stale_revision, "stale")

    def test_current_head_with_stale_revision_is_rejected(self) -> None:
        service = self.repo.service()
        _, stale_revision = self.repo.cas()
        service.requirements_ready(*self.repo.cas())
        with self.assertRaisesRegex(TaskError, "REVISION_MISMATCH"):
            service.approve_plan(self.repo.head(), stale_revision, "stale-revision")

    def test_stale_head_with_current_revision_is_rejected(self) -> None:
        service = self.repo.service()
        stale_head, _ = self.repo.cas()
        service.requirements_ready(*self.repo.cas())
        current_revision = self.repo.state()["revision"]
        with self.assertRaisesRegex(TaskError, "HEAD_MISMATCH"):
            service.approve_plan(stale_head, current_revision, "stale-head")

    def test_implementation_only_cannot_authorize_merge(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        service.approve_plan(*self.repo.cas(), "decision")
        with self.assertRaisesRegex(TaskError, "INVALID_AUTHORIZATION"):
            service.authorize(
                *self.repo.cas(),
                "decision",
                "implement_only",
                ["commit", "conditional_merge"],
            )

    def test_action_list_must_be_canonical_and_known(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        service.approve_plan(*self.repo.cas(), "decision")
        with self.assertRaisesRegex(TaskError, "INVALID_AUTHORIZATION"):
            service.authorize(*self.repo.cas(), "decision", "implement_only", ["ready_for_review", "commit"])
        with self.assertRaisesRegex(TaskError, "INVALID_AUTHORIZATION"):
            service.authorize(*self.repo.cas(), "decision", "implement_only", ["unknown"])


if __name__ == "__main__":
    unittest.main()
