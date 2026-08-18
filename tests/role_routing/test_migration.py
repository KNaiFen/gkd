from __future__ import annotations

import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from gkd_role.migration import apply_migration, migration_plan, verify_migration
from gkd_task.errors import TaskError

from tests.role_routing.helpers import BUNDLE_ROOT, DUPLICATES, build_migration_home, bundle_digest, duplicate_bytes


class MigrationContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-role-migration-")
        self.home = Path(self.temporary.name) / "home"
        build_migration_home(self.home)
        self.bundle = bundle_digest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_atomic_migration_installs_exact_roles_and_skills_and_removes_legacy_role(self) -> None:
        result = apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        agents = self.home / ".codex" / "agents"
        self.assertEqual({"gkd_acceptor.toml", "gkd_ci_reviewer.toml", "gkd_executor.toml"}, {path.name for path in agents.iterdir()})
        self.assertFalse((agents / "ci-reviewer.toml").exists())
        for name in ("gkd-main", "gkd-execute", "gkd-accept", "gkd-local-verify", "gkd-ci-monitor"):
            self.assertTrue((self.home / ".codex" / "skills" / name / "SKILL.md").is_file())
        self.assertEqual("migration_applied", result["status"])

    def test_six_duplicate_paths_are_disabled_without_deleting_or_changing_bytes(self) -> None:
        before = duplicate_bytes(self.home)
        apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual(before, duplicate_bytes(self.home))
        config = tomllib.loads((self.home / ".codex" / "config.toml").read_text(encoding="utf-8"))
        disabled = {Path(item["path"]).parent.name for item in config["skills"]["config"] if item["enabled"] is False}
        self.assertEqual(set(DUPLICATES), disabled)

    def test_unrelated_skills_and_agents_hard_rules_are_byte_unchanged(self) -> None:
        unrelated = self.home / ".codex" / "skills" / "unrelated-skill" / "SKILL.md"
        agents = self.home / ".codex" / "AGENTS.md"
        before = (unrelated.read_bytes(), agents.read_bytes())
        apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual(before, (unrelated.read_bytes(), agents.read_bytes()))

    def test_security_skill_trigger_is_narrowed_and_broken_reference_removed(self) -> None:
        apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        text = (self.home / ".codex" / "skills" / "security-and-hardening" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("explicitly requests a security review", text)
        self.assertNotIn("references/security-checklist.md", text)
        self.assertNotIn("interacts with third-party services", text)

    def test_repeated_migration_is_idempotent(self) -> None:
        first = apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        second = apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        self.assertEqual(first["planDigest"], second["planDigest"])
        self.assertEqual(first["afterDigest"], second["afterDigest"])
        self.assertEqual(first["inventoryDigest"], second["inventoryDigest"])
        self.assertEqual(second["beforeDigest"], second["afterDigest"])

    def test_two_disjoint_temporary_homes_have_identical_normalized_migration_output(self) -> None:
        other = Path(self.temporary.name) / "other-home"
        build_migration_home(other)
        first = apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        second = apply_migration(BUNDLE_ROOT, other, self.bundle)
        self.assertEqual({name: first[name] for name in ("planDigest", "afterDigest", "inventoryDigest")}, {name: second[name] for name in ("planDigest", "afterDigest", "inventoryDigest")})

    def test_staging_and_swap_failures_restore_exact_preimage(self) -> None:
        before = duplicate_bytes(self.home)
        config_before = (self.home / ".codex" / "config.toml").read_bytes()
        for phase in ("staged", "old_moved"):
            with self.subTest(phase=phase):
                def fail(value):
                    if value == phase:
                        raise RuntimeError(f"injected-{phase}")
                with self.assertRaisesRegex(RuntimeError, f"injected-{phase}"):
                    apply_migration(BUNDLE_ROOT, self.home, self.bundle, fail)
                self.assertEqual(before, duplicate_bytes(self.home))
                self.assertEqual(config_before, (self.home / ".codex" / "config.toml").read_bytes())

    def test_production_home_symlink_invalid_config_and_legacy_ambiguity_fail_closed(self) -> None:
        with self.assertRaisesRegex(TaskError, "MIGRATION_PRODUCTION_FORBIDDEN"):
            migration_plan(BUNDLE_ROOT, Path("/Users"), self.bundle)
        (self.home / ".codex" / "config.toml").write_text("[broken\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "INVALID_CODEX_CONFIG"):
            apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        (self.home / ".codex" / "config.toml").write_text("", encoding="utf-8")
        (self.home / ".codex" / "agents" / "ci_reviewer.toml").write_text('name = "ci_reviewer"\n', encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "LEGACY_ROLE_AMBIGUOUS"):
            migration_plan(BUNDLE_ROOT, self.home, self.bundle)

    def test_verify_detects_role_and_duplicate_config_drift(self) -> None:
        apply_migration(BUNDLE_ROOT, self.home, self.bundle)
        role = self.home / ".codex" / "agents" / "gkd_executor.toml"
        role.write_text(role.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "ROLE_INSTALL_MISMATCH"):
            verify_migration(BUNDLE_ROOT, self.home, self.bundle)


if __name__ == "__main__":
    unittest.main()
