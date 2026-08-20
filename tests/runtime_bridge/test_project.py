from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from gkd_role.project import remove_project, stage_project, verify_project
from gkd_task.errors import TaskError
from tests.runtime_bridge.helpers import BUNDLE_ROOT, bundle_digest, init_repo, run


class ProjectStagingContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-m2c-project-")
        self.root = Path(self.temporary.name)
        self.production = self.root / "production-codex"
        self.production.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _project(self, name: str) -> Path:
        project = self.root / name
        init_repo(project)
        return project

    def test_two_project_roots_are_byte_identical_and_candidate_stays_clean(self) -> None:
        first = self._project("project-a")
        second = self._project("project-b")
        candidate = self._project("candidate")
        before = run("git", "status", "--porcelain=v1", cwd=candidate)
        one = stage_project(BUNDLE_ROOT, bundle_digest(), first, self.production)
        two = stage_project(BUNDLE_ROOT, bundle_digest(), second, self.production)
        self.assertEqual(one, two)
        self.assertEqual(
            (first / ".gkd" / "runtime-project.json").read_bytes(),
            (second / ".gkd" / "runtime-project.json").read_bytes(),
        )
        self.assertTrue((first / ".codex" / "agents" / "gkd_executor.toml").is_file())
        self.assertTrue((first / ".agents" / "skills" / "gkd-main" / "SKILL.md").is_file())
        for name in ("gkd-execute", "gkd-local-verify", "gkd-ci-monitor"):
            self.assertTrue((first / ".codex" / "skills" / name / "SKILL.md").is_file())
        self.assertEqual(before, run("git", "status", "--porcelain=v1", cwd=candidate))
        self.assertEqual("verified", verify_project(BUNDLE_ROOT, bundle_digest(), first, self.production)["status"])
        unknown = first / ".codex" / "unexpected.toml"
        unknown.write_text("unexpected = true\n", encoding="utf-8")
        with self.assertRaises(TaskError) as raised:
            verify_project(BUNDLE_ROOT, bundle_digest(), first, self.production)
        self.assertEqual("PROJECT_STAGE_DRIFT", raised.exception.code)
        unknown.unlink()
        self.assertEqual("already_staged", stage_project(BUNDLE_ROOT, bundle_digest(), first, self.production)["status"])
        role_file = first / ".codex" / "agents" / "gkd_executor.toml"
        role_file.chmod(0o600)
        with self.assertRaises(TaskError) as raised:
            remove_project(first, self.production)
        self.assertEqual("PROJECT_STAGE_DRIFT", raised.exception.code)
        inventory = json.loads(
            (first / ".gkd" / "runtime-project.json").read_text(encoding="utf-8")
        )
        self.assertTrue(all((first / record["path"]).is_file() for record in inventory["files"]))
        role_file.chmod(0o644)
        self.assertEqual("removed", remove_project(first, self.production)["status"])
        self.assertFalse((first / ".gkd" / "runtime-project.json").exists())

    def test_boundary_conflicts_fail_before_mutation(self) -> None:
        non_git = self.root / "not-git"
        non_git.mkdir()
        cases = ((non_git, "PROJECT_NOT_GIT_ROOT"), (self.production, "PRODUCTION_PROJECT_FORBIDDEN"))
        for project, code in cases:
            with self.subTest(code=code), self.assertRaises(TaskError) as raised:
                stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
            self.assertEqual(code, raised.exception.code)
        project = self._project("conflict")
        (project / ".codex").mkdir()
        (project / ".codex" / "config.toml").write_text("unknown = true\n", encoding="utf-8")
        before = (project / ".codex" / "config.toml").read_bytes()
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        self.assertEqual("PROJECT_CONFIG_CONFLICT", raised.exception.code)
        self.assertEqual(before, (project / ".codex" / "config.toml").read_bytes())
        self.assertFalse((project / ".gkd" / "runtime-project.json").exists())

    def test_tampered_bundle_and_symlink_ancestors_fail_before_project_write(self) -> None:
        tampered_source = self.root / "tampered-canonical"
        shutil.copytree(Path("canonical"), tampered_source)
        skill = tampered_source / "payload" / "skills" / "gkd-main" / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"\n# tampered\n")
        project = self._project("tampered-target")
        with self.assertRaises(TaskError) as raised:
            stage_project(tampered_source / "payload", bundle_digest(), project, self.production)
        self.assertEqual("BUNDLE_CONTENT_MISMATCH", raised.exception.code)
        self.assertFalse((project / ".codex").exists())
        self.assertFalse((project / ".agents").exists())
        self.assertFalse((project / ".gkd").exists())

        project_parent = self.root / "project-parent"
        project_parent.mkdir()
        ancestor_project = project_parent / "project"
        init_repo(ancestor_project)
        project_alias = self.root / "project-parent-alias"
        project_alias.symlink_to(project_parent, target_is_directory=True)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), project_alias / "project", self.production)
        self.assertEqual("PROJECT_ROOT_SYMLINK", raised.exception.code)
        self.assertFalse((ancestor_project / ".gkd").exists())

        source_parent = self.root / "source-parent"
        source_parent.mkdir()
        copied_source = source_parent / "canonical"
        shutil.copytree(Path("canonical"), copied_source)
        source_alias = self.root / "source-parent-alias"
        source_alias.symlink_to(source_parent, target_is_directory=True)
        bundle_target = self._project("bundle-ancestor-target")
        with self.assertRaises(TaskError) as raised:
            stage_project(source_alias / "canonical" / "payload", bundle_digest(), bundle_target, self.production)
        self.assertEqual("PROJECT_SOURCE_SYMLINK", raised.exception.code)
        self.assertFalse((bundle_target / ".gkd").exists())

    def test_source_declaration_symlink_fails_before_project_write(self) -> None:
        copied_source = self.root / "source-toml-symlink"
        shutil.copytree(Path("canonical"), copied_source)
        declaration = copied_source / "source.toml"
        external = self.root / "external-source.toml"
        external.write_bytes(declaration.read_bytes())
        declaration.unlink()
        declaration.symlink_to(external)
        project = self._project("source-toml-target")
        with self.assertRaises(TaskError) as raised:
            stage_project(copied_source / "payload", bundle_digest(), project, self.production)
        self.assertEqual("BUNDLE_CONTENT_MISMATCH", raised.exception.code)
        self.assertFalse((project / ".codex").exists())
        self.assertFalse((project / ".agents").exists())
        self.assertFalse((project / ".gkd").exists())

    def test_default_python_does_not_create_bundle_bytecode_before_staging(self) -> None:
        copied_source = self.root / "default-python-canonical"
        shutil.copytree(
            Path("canonical"),
            copied_source,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        project = self._project("default-python-project")
        environment = dict(os.environ)
        environment.pop("PYTHONDONTWRITEBYTECODE", None)
        environment["PYTHONPATH"] = str(copied_source / "payload" / "lib")
        imported = subprocess.run(
            [sys.executable, "-c", "from gkd_role.bridge import TrustedMainRuntimeBridge; from gkd_role.project import stage_project"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, imported.returncode, imported.stderr)
        staged = subprocess.run(
            [
                str(copied_source / "payload" / "bin" / "gkd-role"),
                "project-stage",
                "--bundle-root", str(copied_source / "payload"),
                "--bundle-digest", json.loads(
                    (copied_source / "manifest.lock.json").read_text(encoding="utf-8")
                )["contentDigest"],
                "--project-root", str(project),
                "--production-root", str(self.production),
            ],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, staged.returncode, staged.stderr)
        self.assertEqual([], list((copied_source / "payload").rglob("*.pyc")))
        self.assertEqual([], list((copied_source / "payload").rglob("__pycache__")))

    def test_symlink_traversal_overlap_and_bundle_drift_fail_closed(self) -> None:
        project = self._project("project")
        link = self.root / "project-link"
        link.symlink_to(project, target_is_directory=True)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), link, self.production)
        self.assertEqual("PROJECT_ROOT_SYMLINK", raised.exception.code)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), project / ".." / "project", self.production)
        self.assertEqual("PROJECT_PATH_TRAVERSAL", raised.exception.code)
        with self.assertRaises(TaskError) as raised:
            stage_project(project, bundle_digest(), project, self.production)
        self.assertEqual("PROJECT_SOURCE_OVERLAP", raised.exception.code)
        source_link = self.root / "source-link"
        source_link.symlink_to(BUNDLE_ROOT.resolve(), target_is_directory=True)
        with self.assertRaises(TaskError) as raised:
            stage_project(source_link, bundle_digest(), self._project("source-symlink"), self.production)
        self.assertEqual("PROJECT_SOURCE_SYMLINK", raised.exception.code)
        linked_parent = self._project("linked-parent")
        external = self.root / "external-skills"
        external.mkdir()
        (linked_parent / ".agents").mkdir()
        (linked_parent / ".agents" / "skills").symlink_to(external, target_is_directory=True)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), linked_parent, self.production)
        self.assertEqual("PROJECT_STAGE_SYMLINK", raised.exception.code)
        self.assertEqual([], list(external.iterdir()))
        stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        config = project / ".codex" / "config.toml"
        config.write_bytes(config.read_bytes() + b"# drift\n")
        with self.assertRaises(TaskError) as raised:
            verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        self.assertEqual("PROJECT_STAGE_DRIFT", raised.exception.code)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, "f" * 64, self._project("drifted-bundle"), self.production)
        self.assertEqual("BUNDLE_DIGEST_MISMATCH", raised.exception.code)

    def test_write_failure_restores_exact_empty_preimage(self) -> None:
        project = self._project("rollback")

        def fail_after_second(index: int, _: Path) -> None:
            if index == 2:
                raise OSError("synthetic stage failure")

        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production, fail_after_second)
        self.assertEqual("PROJECT_STAGE_FAILED", raised.exception.code)
        self.assertEqual(["README.md"], sorted(path.name for path in project.iterdir() if path.name != ".git"))

    def test_project_remove_retries_after_managed_file_was_deleted(self) -> None:
        project = self._project("remove-retry")
        stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        managed = project / ".codex" / "agents" / "gkd_executor.toml"
        managed.unlink()
        self.assertEqual("removed", remove_project(project, self.production)["status"])
        self.assertFalse((project / ".gkd" / "runtime-project.json").exists())

    def test_project_cli_stages_verifies_and_removes_owned_files(self) -> None:
        project = self._project("cli-project")
        cli = str(Path("canonical/payload/bin/gkd-role").resolve())
        common = (
            "--project-root", str(project),
            "--production-root", str(self.production),
        )
        staged = run(cli, "project-stage", "--bundle-root", str(BUNDLE_ROOT.resolve()), "--bundle-digest", bundle_digest(), *common, cwd=Path.cwd())
        self.assertEqual("staged", __import__("json").loads(staged)["status"])
        verified = run(cli, "project-verify", "--bundle-root", str(BUNDLE_ROOT.resolve()), "--bundle-digest", bundle_digest(), *common, cwd=Path.cwd())
        self.assertEqual("verified", __import__("json").loads(verified)["status"])
        removed = run(cli, "project-remove", *common, cwd=Path.cwd())
        self.assertEqual("removed", __import__("json").loads(removed)["status"])


if __name__ == "__main__":
    unittest.main()
