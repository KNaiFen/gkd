from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

import gkd_bundle
from gkd_role.project import stage_project
from gkd_task.gitops import common_dir
from gkd_task.orchestrator import (
    PlanningPackageStore,
    resolve_trusted_task_context,
    resolve_trusted_task_context_from_runtime,
)
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import TaskRepo, planning_documents


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = ROOT / "canonical" / "payload"


def _files(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _main_cli(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(BUNDLE_ROOT / "bin" / "gkd-main"), *arguments),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class TrustedTaskContextContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()
        verified = gkd_bundle.verify_bundle_root(BUNDLE_ROOT)
        stage_project(
            BUNDLE_ROOT,
            verified["contentDigest"],
            self.repo.main,
            self.repo.production,
        )
        self.runtime = RuntimeStore(self.repo.runtime_root)
        attachment = self.runtime.read_attachment(
            self.repo.identity,
            self.repo.task_id,
            self.repo.task_branch,
        )
        self.default_runtime = RuntimeStore(common_dir(self.repo.candidate) / "gkd-runtime")
        self.default_runtime.write_attachment(attachment)

    def tearDown(self) -> None:
        self.repo.close()

    def test_candidate_main_and_runtime_paths_resolve_the_same_context_without_writes(self) -> None:
        before_runtime = _files(self.repo.runtime_root)
        before_candidate = self.repo.head()
        candidate = resolve_trusted_task_context(self.repo.candidate, BUNDLE_ROOT, runtime=self.runtime)
        trusted_main = resolve_trusted_task_context(
            self.repo.main,
            BUNDLE_ROOT,
            self.repo.task_id,
            runtime=self.runtime,
        )
        attachment = resolve_trusted_task_context_from_runtime(
            self.runtime,
            BUNDLE_ROOT,
            self.repo.task_id,
        )
        self.assertEqual(candidate.inspect(), trusted_main.inspect())
        self.assertEqual(candidate.inspect(), attachment.inspect())
        self.assertEqual(before_candidate, self.repo.head())
        self.assertEqual(before_runtime, _files(self.repo.runtime_root))
        self.assertNotIn("candidateRoot", candidate.inspect())
        self.assertNotIn("repository", candidate.inspect())
        self.assertNotIn("taskPath", candidate.inspect())

    def test_project_inventory_and_policy_drift_fail_closed(self) -> None:
        inventory = self.repo.main / ".gkd" / "runtime-project.json"
        inventory.write_bytes(inventory.read_bytes() + b"\n")
        with self.assertRaisesRegex(Exception, "INVALID_PROJECT_INVENTORY|PROJECT_STAGE_DRIFT"):
            resolve_trusted_task_context(self.repo.candidate, BUNDLE_ROOT, runtime=self.runtime)

    def test_planning_store_publishes_only_valid_documents_and_hides_human_content(self) -> None:
        store = PlanningPackageStore(self.runtime)
        created = store.create(planning_documents())
        inspected = store.inspect(created["packageSelector"])
        self.assertEqual("created", created["status"])
        self.assertEqual("ready", inspected["status"])
        self.assertEqual([], inspected["missingHumanInputs"])
        self.assertNotIn("Fixture Requirements", json.dumps(inspected))
        self.assertEqual("already_created", store.create(planning_documents())["status"])

    def test_invalid_planning_documents_do_not_create_a_runtime_package(self) -> None:
        before = _files(self.repo.runtime_root)
        with self.assertRaisesRegex(Exception, "INVALID_PLANNING_DOCUMENT"):
            PlanningPackageStore(self.runtime).create(
                {
                    "requirements.md": "# Invalid\n",
                    "plan.md": "# Invalid\n",
                    "implementation.md": "# Invalid\n",
                }
            )
        self.assertEqual(before, _files(self.repo.runtime_root))

    def test_cli_uses_no_root_or_package_path_arguments_and_redacts_machine_facts(self) -> None:
        inspected = _main_cli("inspect", cwd=self.repo.candidate)
        self.assertEqual(0, inspected.returncode, inspected.stderr)
        value = json.loads(inspected.stdout)
        self.assertEqual("ok", value["status"])
        rendered = inspected.stdout
        for forbidden in (
            str(self.repo.candidate),
            str(self.repo.main),
            str(self.repo.runtime_root),
            self.repo.identity,
            self.repo.task_branch,
            self.repo.task_path,
        ):
            self.assertNotIn(forbidden, rendered)
        documents = planning_documents()
        created = _main_cli(
            "planning",
            "create",
            "--requirements",
            documents["requirements.md"],
            "--plan",
            documents["plan.md"],
            "--implementation",
            documents["implementation.md"],
            cwd=self.repo.candidate,
        )
        self.assertEqual(0, created.returncode, created.stderr)
        selector = json.loads(created.stdout)["packageSelector"]
        package = _main_cli(
            "planning",
            "inspect",
            "--package-selector",
            selector,
            cwd=self.repo.candidate,
        )
        self.assertEqual(0, package.returncode, package.stderr)
        self.assertEqual("ready", json.loads(package.stdout)["status"])
        self.assertNotIn("Fixture Requirements", package.stdout)


if __name__ == "__main__":
    unittest.main()
