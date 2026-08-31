from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import gkd_bundle
import gkd_toml as tomllib
from gkd_role.project import remove_project, stage_project, verify_project
from gkd_role.roles import role_catalog, role_record
from gkd_task.canonical import canonical_bytes
from gkd_task.canonical import sha256_bytes
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
        self.assertEqual(
            json.loads((first / ".gkd" / "policy.json").read_text(encoding="utf-8"))["repository"],
            one["policy"]["repository"],
        )
        for name in ("gkd-execute", "gkd-local-verify", "gkd-ci-monitor"):
            self.assertTrue((first / ".codex" / "skills" / name / "SKILL.md").is_file())
        for name in ("gkd-optimize-ci", "gkd-review-remediation"):
            self.assertFalse((first / ".codex" / "skills" / name).exists())
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

    def test_optional_packs_are_explicit_and_inventory_bound(self) -> None:
        project = self._project("optional-packs")
        packs = ("ci-advice", "review-remediation")
        staged = stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs=packs)
        self.assertEqual(["ci-advice", "review-remediation"], staged["optionalPacks"])
        self.assertEqual({"ci-advice", "review-remediation"}, set(staged["packDigests"]))
        for name in ("gkd-optimize-ci", "gkd-review-remediation"):
            self.assertTrue((project / ".codex" / "skills" / name / "SKILL.md").is_file())
        verified = verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs)
        self.assertEqual(staged["inventoryDigest"], verified["inventoryDigest"])
        with self.assertRaisesRegex(TaskError, "PROJECT_STAGE_DRIFT"):
            verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        skill = project / ".codex" / "skills" / "gkd-optimize-ci" / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"\n")
        with self.assertRaisesRegex(TaskError, "PROJECT_STAGE_DRIFT"):
            verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs)
        skill.write_bytes(skill.read_bytes().rstrip(b"\n") + b"\n")
        self.assertEqual("removed", remove_project(project, self.production)["status"])
        self.assertFalse((project / ".codex").exists())

    def test_project_stage_renders_pack_aware_executor_toml_and_rejects_extra_skill(self) -> None:
        executor_skills = ("gkd-ci-monitor", "gkd-execute", "gkd-local-verify")
        core_config = (
            "gkd-accept",
            "gkd-ci-monitor",
            "gkd-execute",
            "gkd-local-verify",
            "gkd-main",
        )
        cases = (
            ("core", (), executor_skills),
            ("ci-advice", ("ci-advice",), (*executor_skills, "gkd-optimize-ci")),
            ("review-remediation", ("review-remediation",), (*executor_skills, "gkd-review-remediation")),
            (
                "combined",
                ("ci-advice", "review-remediation"),
                (*executor_skills, "gkd-optimize-ci", "gkd-review-remediation"),
            ),
        )
        for name, packs, skills in cases:
            with self.subTest(name=name):
                project = self._project(f"pack-role-{name}")
                staged = stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs=packs)
                role_bytes = (project / ".codex" / "agents" / "gkd_executor.toml").read_bytes()
                role = tomllib.loads(role_bytes.decode("utf-8"))
                expected = [
                    {"path": f"../skills/{skill}/SKILL.md", "enabled": skill in skills}
                    for skill in (*core_config, *(skill for skill in skills if skill not in core_config))
                ]
                self.assertEqual(expected, role["skills"]["config"])
                if not packs:
                    self.assertEqual(
                        [],
                        [
                            entry
                            for entry in role["skills"]["config"]
                            if entry["path"].endswith("gkd-optimize-ci/SKILL.md")
                            or entry["path"].endswith("gkd-review-remediation/SKILL.md")
                        ],
                    )
                catalog = role_catalog(BUNDLE_ROOT, bundle_digest(), packs)
                expected_role = role_record(catalog, "gkd_executor")
                self.assertEqual(expected_role["roleDigest"], staged["roleDigest"])
                self.assertEqual(expected_role["configDigest"], staged["configDigest"])
                self.assertEqual(sha256_bytes(role_bytes), staged["configDigest"])
                self.assertEqual("verified", verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs)["status"])

        project = self._project("pack-role-extra")
        stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production, packs=("ci-advice",))
        role_file = project / ".codex" / "agents" / "gkd_executor.toml"
        role_file.write_bytes(
            role_file.read_bytes()
            + b'\n[[skills.config]]\npath = "../skills/gkd-review-remediation/SKILL.md"\nenabled = true\n'
        )
        with self.assertRaisesRegex(TaskError, "PROJECT_STAGE_DRIFT"):
            verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production, ("ci-advice",))

    def test_policy_is_required_and_staged_inventory_rejects_live_drift(self) -> None:
        missing = self._project("missing-policy")
        (missing / ".gkd" / "policy.json").unlink()
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), missing, self.production)
        self.assertEqual("POLICY_INVALID", raised.exception.code)
        self.assertFalse((missing / ".gkd" / "runtime-project.json").exists())

        project = self._project("policy-drift")
        stage_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        policy_path = project / ".gkd" / "policy.json"
        policy = json.loads(policy_path.read_bytes())
        policy["requiredChecks"] = ["alternate-contract"]
        policy_path.write_bytes(canonical_bytes(policy))
        with self.assertRaises(TaskError) as raised:
            verify_project(BUNDLE_ROOT, bundle_digest(), project, self.production)
        self.assertEqual("PROJECT_STAGE_DRIFT", raised.exception.code)

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
        self.assertFalse((project / ".gkd" / "runtime-project.json").exists())

        project_parent = self.root / "project-parent"
        project_parent.mkdir()
        ancestor_project = project_parent / "project"
        init_repo(ancestor_project)
        project_alias = self.root / "project-parent-alias"
        project_alias.symlink_to(project_parent, target_is_directory=True)
        with self.assertRaises(TaskError) as raised:
            stage_project(BUNDLE_ROOT, bundle_digest(), project_alias / "project", self.production)
        self.assertEqual("PROJECT_ROOT_SYMLINK", raised.exception.code)
        self.assertFalse((ancestor_project / ".gkd" / "runtime-project.json").exists())

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
        self.assertFalse((bundle_target / ".gkd" / "runtime-project.json").exists())

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
        self.assertFalse((project / ".gkd" / "runtime-project.json").exists())

    def test_supported_python_does_not_create_bundle_bytecode_before_staging(self) -> None:
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
                sys.executable,
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

    def test_installed_bridge_prepare_preserves_verified_inventory(self) -> None:
        temporary_root = self.root / "installed-bridge-root"
        target = temporary_root / "target"
        temporary_root.mkdir()
        target.mkdir()
        installed = gkd_bundle.install(Path("canonical"), temporary_root, target)
        code = """
import sys
from pathlib import Path
import gkd_role
from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_role.project import stage_project
from gkd_role.routing import decide_route
from gkd_task.canonical import FixedClock, FixedNonce
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo

bundle = Path(sys.argv[1])
digest = sys.argv[2]
repo = TaskRepo()
try:
    repo.ready_and_authorized()
    stage_project(bundle, digest, repo.main, repo.production)
    decision = decide_route({
        "schemaVersion": 2,
        "requestedRoute": "automatic",
        "bundleDigest": digest,
        "projectPolicy": repo.state()["repository"]["policy"],
        "gates": {
            "activationProviderReady": True,
            "bundleFixed": True,
            "offerClaimReady": True,
            "roleAvailable": True,
            "roleConfigFixed": True,
            "waitGateReady": True,
        },
    })
    bridge = TrustedMainRuntimeBridge(
        repo.candidate,
        repo.task_path,
        RuntimeStore(repo.runtime_root),
        bundle,
        digest,
        FixedClock(FIXED_TIME),
        FixedNonce(["c" * 48, *[f"installed-bridge-nonce-{index}" for index in range(12)]]),
    )
    bridge.prepare(*repo.cas(), decision, FUTURE_TIME, repo.main, repo.production)
finally:
    repo.close()
"""
        environment = dict(os.environ)
        environment.pop("PYTHONDONTWRITEBYTECODE", None)
        environment["PYTHONPATH"] = os.pathsep.join((str(target / "gkd" / "lib"), str(Path.cwd())))
        prepared = subprocess.run(
            [sys.executable, "-B", "-c", code, str(target / "gkd"), installed["contentDigest"]],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, prepared.returncode, prepared.stderr)
        self.assertEqual(installed["contentDigest"], gkd_bundle.verify(temporary_root, target)["contentDigest"])
        self.assertEqual([], list((target / "gkd").rglob("*.pyc")))
        self.assertEqual([], list((target / "gkd").rglob("__pycache__")))

    def test_project_optional_pack_requires_the_installed_pack_surface(self) -> None:
        temporary_root = self.root / "installed-pack-root"
        target = temporary_root / "target"
        temporary_root.mkdir()
        target.mkdir()
        installed = gkd_bundle.install(Path("canonical"), temporary_root, target)
        project = self._project("installed-pack-project")
        with self.assertRaisesRegex(TaskError, "OPTIONAL_PACK_NOT_INSTALLED"):
            stage_project(target / "gkd", installed["contentDigest"], project, self.production, packs=("ci-advice",))
        self.assertFalse((project / ".codex").exists())
        gkd_bundle.stage_packs(Path("canonical"), temporary_root, target, ("ci-advice",))
        staged = stage_project(target / "gkd", installed["contentDigest"], project, self.production, packs=("ci-advice",))
        self.assertEqual(["ci-advice"], staged["optionalPacks"])

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
        self.assertEqual([".gkd", "README.md"], sorted(path.name for path in project.iterdir() if path.name != ".git"))

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
