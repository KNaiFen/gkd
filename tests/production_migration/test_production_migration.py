from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gkd_role.production_migration import (
    RECOVERY_DIRECTORY,
    apply_production_migration,
    doctor_production_migration,
    production_migration_plan,
    recover_production_migration,
    rollback_production_migration,
)
from gkd_task.errors import TaskError

from tests.role_routing.helpers import BUNDLE_ROOT, build_migration_home, bundle_digest


def snapshot(root: Path) -> dict[str, tuple[str, bytes | None]]:
    records = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            records[relative] = ("file", path.read_bytes())
        elif path.is_dir():
            records[relative] = ("directory", None)
        else:
            records[relative] = ("other", None)
    return records


class ProductionMigrationContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-production-migration-")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        build_migration_home(self.home)
        self.bundle = bundle_digest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_plan_apply_and_doctor_manage_only_declared_surfaces(self) -> None:
        unrelated = self.home / ".codex" / "skills" / "unrelated-skill" / "SKILL.md"
        duplicate = self.home / ".agents" / "skills" / "code-review-and-quality" / "SKILL.md"
        before = (unrelated.read_bytes(), duplicate.read_bytes())
        before_home = snapshot(self.home)

        plan = production_migration_plan(BUNDLE_ROOT, self.home, self.bundle)
        self.assertTrue(plan["productionTarget"])
        self.assertEqual(RECOVERY_DIRECTORY, plan["recoverySurface"])
        self.assertEqual(sorted(plan["managedTargets"]), plan["managedTargets"])

        applied = apply_production_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual("production_migration_applied", applied["status"])
        self.assertFalse((self.home / RECOVERY_DIRECTORY).exists())
        self.assertEqual(before, (unrelated.read_bytes(), duplicate.read_bytes()))
        after_home = snapshot(self.home)
        changed = {
            path
            for path in set(before_home) | set(after_home)
            if before_home.get(path) != after_home.get(path)
        }
        self.assertTrue(
            all(
                any(path == target or path.startswith(target + "/") for target in plan["managedTargets"])
                for path in changed
            )
        )

        doctor = doctor_production_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual("production_migration_healthy", doctor["status"])
        self.assertEqual(applied["inventoryDigest"], doctor["inventoryDigest"])
        self.assertEqual(applied["managedSurfaceDigest"], doctor["managedSurfaceDigest"])

    def test_interruption_retains_exact_preimage_until_explicit_rollback(self) -> None:
        before = snapshot(self.home)

        def interrupt(phase: str, _path: Path) -> None:
            if phase == "target-mutated":
                raise RuntimeError("injected-interruption")

        with self.assertRaisesRegex(RuntimeError, "injected-interruption"):
            apply_production_migration(BUNDLE_ROOT, self.home, self.bundle, interrupt)
        with self.assertRaisesRegex(TaskError, "PRODUCTION_RECOVERY_REQUIRED"):
            apply_production_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual(
            "production_recovery_required",
            doctor_production_migration(BUNDLE_ROOT, self.home, self.bundle)["status"],
        )

        result = rollback_production_migration(self.home)
        self.assertEqual("production_migration_rolled_back", result["status"])
        self.assertEqual(before, snapshot(self.home))

    def test_recover_restores_exact_preimage_after_failure(self) -> None:
        before = snapshot(self.home)

        def interrupt(phase: str, _path: Path) -> None:
            if phase == "recovery-recorded":
                raise RuntimeError("injected-after-record")

        with self.assertRaisesRegex(RuntimeError, "injected-after-record"):
            apply_production_migration(BUNDLE_ROOT, self.home, self.bundle, interrupt)
        result = recover_production_migration(self.home)
        self.assertEqual("production_migration_recovered", result["status"])
        self.assertEqual(before, snapshot(self.home))

    def test_symlink_malformed_config_and_invalid_recovery_state_are_rejected(self) -> None:
        linked = self.root / "linked-home"
        linked.symlink_to(self.home, target_is_directory=True)
        with self.assertRaisesRegex(TaskError, "INVALID_PRODUCTION_HOME"):
            production_migration_plan(BUNDLE_ROOT, linked, self.bundle)

        config = self.home / ".codex" / "config.toml"
        config.unlink()
        config.symlink_to(self.root / "other-config")
        with self.assertRaisesRegex(TaskError, "PRODUCTION_SYMLINK_REJECTED"):
            production_migration_plan(BUNDLE_ROOT, self.home, self.bundle)
        config.unlink()
        config.write_text("[broken\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "INVALID_PRODUCTION_CONFIG"):
            production_migration_plan(BUNDLE_ROOT, self.home, self.bundle)
        config.write_text('model = "gpt-5.6-sol"\n', encoding="utf-8")
        recovery = self.home / RECOVERY_DIRECTORY
        recovery.mkdir(parents=True)
        with self.assertRaisesRegex(TaskError, "INVALID_PRODUCTION_RECOVERY_STATE"):
            production_migration_plan(BUNDLE_ROOT, self.home, self.bundle)

    def test_tampered_staged_content_is_rejected_before_recovery_record_or_home_write(self) -> None:
        before = snapshot(self.home)

        def tamper(phase: str, stage: Path) -> None:
            if phase == "staged":
                (stage / ".codex" / "agents" / "gkd_executor.toml").write_text("tampered\n", encoding="utf-8")

        with self.assertRaisesRegex(TaskError, "STAGED_CONTENT_TAMPERED"):
            apply_production_migration(BUNDLE_ROOT, self.home, self.bundle, tamper)
        self.assertEqual(before, snapshot(self.home))
        self.assertFalse((self.home / RECOVERY_DIRECTORY).exists())

    def test_machine_output_never_contains_home_path_or_config_contents(self) -> None:
        secret = "machine-private-config-value"
        config = self.home / ".codex" / "config.toml"
        config.write_text(f'custom = "{secret}"\n', encoding="utf-8")
        command = [
            sys.executable,
            "canonical/payload/bin/gkd-role",
            "production-migration-plan",
            "--bundle-root",
            os.fspath(BUNDLE_ROOT),
            "--bundle-digest",
            self.bundle,
            "--home-root",
            os.fspath(self.home),
        ]
        completed = subprocess.run(command, cwd=Path(__file__).resolve().parents[2], capture_output=True, check=False)
        self.assertEqual(0, completed.returncode, completed.stderr.decode("utf-8"))
        parsed = json.loads(completed.stdout)
        self.assertEqual("production-migration", parsed["operation"])
        self.assertNotIn(secret.encode("utf-8"), completed.stdout)
        self.assertNotIn(os.fspath(self.home).encode("utf-8"), completed.stdout)


if __name__ == "__main__":
    unittest.main()
