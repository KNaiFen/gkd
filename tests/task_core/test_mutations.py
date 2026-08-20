from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path("canonical/payload/lib/gkd_task")


class MutationContracts(unittest.TestCase):
    def _killed(self, files: dict[str, list[tuple[str, str]]], test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-task-mutant-") as temporary:
            package = Path(temporary) / "gkd_task"
            shutil.copytree(SOURCE, package)
            for relative, replacements in files.items():
                path = package / relative
                text = path.read_text(encoding="utf-8")
                for old, new in replacements:
                    self.assertIn(old, text, f"mutation anchor missing: {relative}: {old!r}")
                    text = text.replace(old, new, 1)
                path.write_text(text, encoding="utf-8")
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = f"{temporary}:canonical/payload/lib:."
            result = subprocess.run(
                [sys.executable, "-m", "unittest", test_name, "-q"],
                cwd=Path.cwd(),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=90,
            )
            self.assertNotEqual(0, result.returncode, f"mutant survived {test_name}\n{result.stdout}\n{result.stderr}")

    def test_mutation_material_invalidation_is_killed(self) -> None:
        self._killed(
            {"service.py": [("            if material_changed:\n", "            if False and material_changed:\n"), ("            if material_changed:\n", "            if False and material_changed:\n")]},
            "tests.task_core.test_planning.PlanningContracts.test_every_material_section_invalidates_approval_and_authorization",
        )

    def test_mutation_revision_cas_is_killed(self) -> None:
        self._killed(
            {"transaction.py": [("            if state[\"revision\"] != expected_revision:\n", "            if False and state[\"revision\"] != expected_revision:\n")]},
            "tests.task_core.test_planning.PlanningContracts.test_current_head_with_stale_revision_is_rejected",
        )

    def test_mutation_exact_head_cas_is_killed(self) -> None:
        self._killed(
            {"transaction.py": [("            if head(self.candidate_root) != expected_head:\n", "            if False and head(self.candidate_root) != expected_head:\n")]},
            "tests.task_core.test_planning.PlanningContracts.test_stale_head_with_current_revision_is_rejected",
        )

    def test_mutation_task_lock_is_killed(self) -> None:
        self._killed(
            {"runtime.py": [("        lock_path = lock_root / f\"{key}.lock\"\n", "        lock_path = lock_root / f\"{key}.{time.monotonic_ns()}.lock\"\n")]},
            "tests.task_core.test_runtime_and_migration.RuntimeTransactionContracts.test_lock_is_not_removed_merely_because_time_passes",
        )

    def test_mutation_capability_consumption_is_killed(self) -> None:
        self._killed(
            {
                "service.py": [
                    ("            if state[\"lifecycle\"][\"phase\"] != \"awaiting_claim\":\n                raise TaskError(\"OFFER_CONFLICT\")\n            offer = self._offer()\n", "            if False and state[\"lifecycle\"][\"phase\"] != \"awaiting_claim\":\n                raise TaskError(\"OFFER_CONFLICT\")\n            offer = self._offer()\n"),
                    ("                offer[\"status\"] != \"active\"\n                or offer[\"offerId\"] != envelope[\"offerId\"]\n", "                False\n                or offer[\"offerId\"] != envelope[\"offerId\"]\n"),
                ]
            },
            "tests.task_core.test_lifecycle.LifecycleContracts.test_late_executor_with_stale_envelope_remains_rejected",
        )

    def test_mutation_candidate_code_isolation_is_killed(self) -> None:
        self._killed(
            {
                "acceptance.py": [
                    (
                        "    state = _fixed_json(candidate_root, candidate_head, f\"{task_path}/task.json\", \"CANDIDATE_INVALID\")\n",
                        "    candidate_code = read_tree_file(candidate_root, candidate_head, \"gkd_task/acceptance.py\")\n    exec(compile(candidate_code.decode(\"utf-8\"), \"candidate-acceptance.py\", \"exec\"), {})\n    state = _fixed_json(candidate_root, candidate_head, f\"{task_path}/task.json\", \"CANDIDATE_INVALID\")\n",
                    )
                ]
            },
            "tests.task_core.test_acceptance.AcceptanceContracts.test_candidate_module_is_never_imported_or_executed",
        )

    def test_mutation_action_scope_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("    _authorization_preflight(state, authorization, repository, candidate_head, \"conditional_merge\" if merge else \"ready_for_review\")\n", "    # mutated action-scope check removed\n")]},
            "tests.task_core.test_acceptance.AcceptanceContracts.test_implement_only_refusal_is_one_authorization_mismatch_and_zero_calls",
        )

    def test_mutation_merge_head_check_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("        or snapshot[\"headSha\"] != candidate_head\n", "        or False\n")]},
            "tests.task_core.test_acceptance.AcceptanceContracts.test_wrong_repo_base_pr_or_head_is_rejected",
        )

    def test_mutation_no_retry_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("    if result != {\"status\": \"merged\", \"mergedHead\": candidate_head}:\n        raise TaskError(\"MERGE_REJECTED\")\n", "    if result != {\"status\": \"merged\", \"mergedHead\": candidate_head}:\n        result = adapter.merge(repository, pr_number, candidate_head)\n        raise TaskError(\"MERGE_REJECTED\")\n")]},
            "tests.task_core.test_acceptance.AcceptanceContracts.test_merge_rejection_is_terminal_and_not_retried",
        )

    def test_mutation_rework_actor_gate_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("    if actor_role not in {\"acceptor\", \"main\"}:\n        raise TaskError(\"EXECUTOR_REWORK_FORBIDDEN\")\n", "    if False and actor_role not in {\"acceptor\", \"main\"}:\n        raise TaskError(\"EXECUTOR_REWORK_FORBIDDEN\")\n")]},
            "tests.task_core.test_rework.ReworkContracts.test_executor_and_non_repair_authorization_fail_before_external_or_tracked_write",
        )

    def test_mutation_rework_authorization_gate_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("    _authorization_preflight(state, authorization, repository, candidate_head, \"ci_repair\")\n", "    # mutated rework authorization check removed\n")]},
            "tests.task_core.test_rework.ReworkContracts.test_executor_and_non_repair_authorization_fail_before_external_or_tracked_write",
        )

    def test_mutation_rework_epoch_fence_is_killed(self) -> None:
        self._killed(
            {"acceptance.py": [("        updated[\"lifecycle\"][\"epoch\"] += 1\n", "        updated[\"lifecycle\"][\"epoch\"] += 0\n")]},
            "tests.task_core.test_rework.ReworkContracts.test_rework_preserves_exact_attempt_and_only_commits_coordination_files",
        )


if __name__ == "__main__":
    unittest.main()
