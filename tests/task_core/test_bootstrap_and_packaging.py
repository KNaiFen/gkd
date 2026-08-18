from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import gkd_bundle
from gkd_task.canonical import FixedClock
from gkd_task.errors import TaskError
from gkd_task.service import bootstrap_task
from tests.task_core.helpers import FIXED_TIME, TaskRepo


class BootstrapNegativeContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _bootstrap(self, candidate: Path, branch: str, base: str | None = None, identity: str | None = None):
        return bootstrap_task(
            self.repo.main,
            candidate,
            self.repo.package,
            "TASK-BETA",
            "tasks/task-beta",
            identity or self.repo.identity,
            self.repo.base_branch,
            base or self.repo.base_sha,
            branch,
            self.repo.root / "runtime-beta",
            FixedClock(FIXED_TIME),
        )

    def test_dirty_main_is_rejected_before_candidate_write(self) -> None:
        (self.repo.main / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "WORKTREE_NOT_CLEAN"):
            self._bootstrap(candidate, "task/beta")
        self.assertFalse(candidate.exists())

    def test_duplicate_branch_or_second_writable_fact_source_is_rejected(self) -> None:
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "TASK_BRANCH_EXISTS"):
            self._bootstrap(candidate, self.repo.task_branch)
        self.assertFalse(candidate.exists())

    def test_existing_candidate_and_main_as_candidate_are_rejected(self) -> None:
        existing = self.repo.root / "existing"
        existing.mkdir()
        with self.assertRaisesRegex(TaskError, "CANDIDATE_ALREADY_EXISTS"):
            self._bootstrap(existing, "task/beta")
        with self.assertRaisesRegex(TaskError, "CANDIDATE_ALREADY_EXISTS"):
            self._bootstrap(self.repo.main, "task/gamma")

    def test_nonexistent_or_unfetched_base_is_rejected(self) -> None:
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "GIT_OPERATION_FAILED|BASE_NOT_FETCHED"):
            self._bootstrap(candidate, "task/beta", base="0" * 40)
        self.assertFalse(candidate.exists())

    def test_repository_identity_mismatch_is_rejected(self) -> None:
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "INVALID_REPOSITORY_IDENTITY"):
            self._bootstrap(candidate, "task/beta", identity="example.test/other/repository")
        self.assertFalse(candidate.exists())

    def test_bootstrap_requires_independent_nonexistent_worktree(self) -> None:
        with self.assertRaisesRegex(TaskError, "CANDIDATE_ALREADY_EXISTS"):
            self._bootstrap(self.repo.candidate, "task/beta")

    def test_refspec_shaped_branch_is_rejected_before_write(self) -> None:
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "INVALID_GIT_BRANCH"):
            self._bootstrap(candidate, "+refs/heads/trunk:refs/heads/other")
        self.assertFalse(candidate.exists())

    def test_runtime_root_overlapping_future_candidate_is_rejected_before_write(self) -> None:
        candidate = self.repo.root / "candidate-beta"
        with self.assertRaisesRegex(TaskError, "RUNTIME_ROOT_OVERLAP"):
            bootstrap_task(
                self.repo.main,
                candidate,
                self.repo.package,
                "TASK-BETA",
                "tasks/task-beta",
                self.repo.identity,
                self.repo.base_branch,
                self.repo.base_sha,
                "task/beta",
                candidate / "runtime",
                FixedClock(FIXED_TIME),
            )
        self.assertFalse(candidate.exists())


class PackagingContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-task-package-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "canonical"
        shutil.copytree(Path("canonical"), self.source, copy_function=shutil.copy2)
        self.generated = gkd_bundle.generate(self.source)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_two_temporary_installs_have_same_version_digest_and_inventory(self) -> None:
        temporary_root = self.root / "install-root"
        first = temporary_root / "first"
        second = temporary_root / "second"
        temporary_root.mkdir()
        first.mkdir()
        second.mkdir()
        first_install = gkd_bundle.install(self.source, temporary_root, first)
        second_install = gkd_bundle.install(self.source, temporary_root, second)
        first_verify = gkd_bundle.verify(temporary_root, first)
        second_verify = gkd_bundle.verify(temporary_root, second)
        self.assertEqual(first_install["contentDigest"], second_install["contentDigest"])
        self.assertEqual(first_verify, second_verify)
        self.assertEqual("0.0.0-dev.0", first_install["bundleVersion"])
        self.assertGreaterEqual(first_install["files"], 24)

    def test_installed_gkd_task_is_executable_and_imports_installed_library(self) -> None:
        temporary_root = self.root / "install-root"
        target = temporary_root / "target"
        runtime = self.root / "runtime"
        temporary_root.mkdir()
        target.mkdir()
        runtime.mkdir()
        gkd_bundle.install(self.source, temporary_root, target)
        executable = target / "gkd" / "bin" / "gkd-task"
        help_result = subprocess.run([str(executable), "--help"], cwd=target, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("bootstrap", help_result.stdout)
        error = subprocess.run(
            [
                str(executable),
                "status",
                "--repository",
                "example.test/team/repository",
                "--task-id",
                "TASK-X",
                "--task-branch",
                "task/x",
                "--task-path",
                "tasks/x",
                "--runtime-root",
                str(runtime),
            ],
            cwd=target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(2, error.returncode)
        parsed = json.loads(error.stderr)
        self.assertEqual({"status": "error", "error": "worktree_missing"}, parsed)
        self.assertNotIn(str(self.root), error.stderr)

    def test_task_schemas_are_strict_versioned_and_installed(self) -> None:
        schema_root = self.source / "payload" / "schema" / "task"
        expected = {"task-state.schema.json", "offer.schema.json", "authorization.schema.json", "runtime.schema.json"}
        self.assertEqual(expected, {path.name for path in schema_root.iterdir()})
        for path in schema_root.iterdir():
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", value["$schema"])
            if value.get("type") == "object":
                self.assertFalse(value["additionalProperties"])

    def test_manifest_declares_separate_task_cli_library_and_schemas(self) -> None:
        manifest = json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))
        names = {component["name"] for component in manifest["components"]}
        self.assertTrue({"task-cli", "task-library", "task-schemas"}.issubset(names))
        lock = json.loads((self.source / "manifest.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(45, len(lock["installFiles"]))
        self.assertEqual(self.generated["contentDigest"], lock["contentDigest"])

    def test_payload_and_machine_output_contain_no_fixture_path_or_plain_capability(self) -> None:
        forbidden = (str(self.root).encode("utf-8"), b"fixture-secret-capability")
        for path in (self.source / "payload").rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                for marker in forbidden:
                    self.assertNotIn(marker, data)


if __name__ == "__main__":
    unittest.main()
