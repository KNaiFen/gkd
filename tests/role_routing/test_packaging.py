from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import gkd_toml as tomllib

import gkd_bundle
from gkd_role.roles import role_files

from tests.role_routing.helpers import BUNDLE_ROOT, SOURCE_ROOT, bundle_digest


class PackagingContracts(unittest.TestCase):
    def test_manifest_declares_every_role_routing_payload_and_mode(self) -> None:
        manifest = json.loads((SOURCE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        lock = json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))
        names = {component["name"] for component in manifest["components"]}
        self.assertTrue({"role-routing-cli", "role-routing-library", "role-routing-source", "role-routing-schemas", "workflow-core-skills"}.issubset(names))
        self.assertEqual(
            len([path for path in (SOURCE_ROOT / "payload").rglob("*") if path.is_file()]),
            len(lock["installFiles"]),
        )
        self.assertEqual(bundle_digest(), lock["contentDigest"])
        payload_text = "\n".join(path.read_text(encoding="utf-8") for path in (BUNDLE_ROOT / "lib").rglob("*.py"))
        self.assertNotIn("FixtureEvidenceProvider", payload_text)
        self.assertNotIn("make_fixture_evidence", payload_text)
        self.assertIn("TrustedMainActivationAuthority", payload_text)

    def test_role_and_task_schemas_are_versioned_and_strict(self) -> None:
        role_schemas = {path.name for path in (BUNDLE_ROOT / "schema" / "role").iterdir()}
        self.assertEqual({"activation.schema.json", "context.schema.json", "migration.schema.json", "production-migration.schema.json", "project.schema.json", "route-decision.schema.json", "route.schema.json", "spawn-result.schema.json", "wait.schema.json"}, role_schemas)
        for path in (BUNDLE_ROOT / "schema").rglob("*.schema.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", value["$schema"])
            if value.get("type") == "object":
                self.assertFalse(value["additionalProperties"])
        runtime = json.loads((BUNDLE_ROOT / "schema" / "task" / "runtime.schema.json").read_text(encoding="utf-8"))
        self.assertTrue({"activation", "activationReceipt", "envelopeV2", "envelopeV3"}.issubset(runtime["$defs"]))

    def test_install_exercises_role_cli_and_has_exact_inventory_modes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-role-install-") as root_name:
            temporary = Path(root_name)
            target = temporary / "target"
            target.mkdir()
            installed = gkd_bundle.install(SOURCE_ROOT, temporary, target)
            lock = json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))
            executable = target / "gkd" / "bin" / "gkd-role"
            result = subprocess.run([sys.executable, str(executable), "roles", "--bundle-root", str(target / "gkd"), "--bundle-digest", bundle_digest()], cwd=target, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(3, len(json.loads(result.stdout)["roles"]))
            self.assertEqual("0755", oct(executable.stat().st_mode & 0o777).removeprefix("0o").zfill(4))
            core_files = [item for item in lock["installFiles"] if item["pack"] is None]
            self.assertEqual(len(core_files) + 4, installed["files"])
            self.assertEqual([], installed["installedPacks"])
            self.assertFalse((target / "gkd" / "bin" / "gkd-resource-scanner").exists())
            self.assertFalse((target / "gkd" / "bin" / "gkd-review").exists())
            inventory = json.loads((target / "gkd" / ".bundle" / "install.json").read_text(encoding="utf-8"))
            inventory_text = json.dumps(inventory, sort_keys=True)
            self.assertNotIn("FixtureEvidenceProvider", inventory_text)
            self.assertNotIn("make_fixture_evidence", inventory_text)
            installed_text = "\n".join(path.read_text(encoding="utf-8") for path in (target / "gkd" / "lib").rglob("*.py"))
            self.assertNotIn("FixtureEvidenceProvider", installed_text)
            self.assertNotIn("make_fixture_evidence", installed_text)
            self.assertIn("TrustedMainActivationAuthority", installed_text)

    def test_installed_role_files_follow_current_custom_agent_schema(self) -> None:
        for name, raw in role_files(BUNDLE_ROOT, bundle_digest()).items():
            role = tomllib.loads(raw.decode("utf-8"))
            self.assertTrue({"name", "description", "developer_instructions"}.issubset(role))
            self.assertIn(role["sandbox_mode"], {"read-only", "workspace-write"})
            self.assertTrue(all(item["path"].startswith("../skills/") and item["path"].endswith("/SKILL.md") for item in role["skills"]["config"]))

    def test_installed_optional_pack_enables_explicit_role_context(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-role-pack-") as root_name:
            temporary = Path(root_name)
            target = temporary / "target"
            target.mkdir()
            gkd_bundle.install(SOURCE_ROOT, temporary, target)
            executable = target / "gkd" / "bin" / "gkd-role"
            missing = subprocess.run(
                [sys.executable, str(executable), "context", "--bundle-root", str(target / "gkd"), "--bundle-digest", bundle_digest(), "--role", "gkd_executor", "--pack", "ci-advice"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(2, missing.returncode)
            gkd_bundle.stage_packs(SOURCE_ROOT, temporary, target, ("ci-advice",))
            completed = subprocess.run(
                [sys.executable, str(executable), "context", "--bundle-root", str(target / "gkd"), "--bundle-digest", bundle_digest(), "--role", "gkd_executor", "--pack", "ci-advice"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            context = json.loads(completed.stdout)
            self.assertEqual(["ci-advice"], context["optionalPacks"])
            self.assertIn("gkd-optimize-ci", {item["name"] for item in context["skills"]})

    def test_workflow_skills_have_progressive_disclosure_shape_and_generic_mechanism(self) -> None:
        for root in sorted((BUNDLE_ROOT / "skills").iterdir()):
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: "))
            self.assertIn("\ndescription: ", text.split("---\n", 2)[1])
            self.assertTrue((root / "agents" / "openai.yaml").is_file())
            lowered = text.lower()
            for forbidden in ("knai", "aio-coding-hub", "/users/", ".trellis", "ci-gate", "pr-title"):
                self.assertNotIn(forbidden, lowered)

    def test_payload_and_machine_outputs_contain_no_production_path_or_plain_runtime_identity(self) -> None:
        markers = (b"/Users/knaifen", b"KNaiFen", b"aio-coding-hub", b"fixture-secret-capability")
        for path in BUNDLE_ROOT.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                for marker in markers:
                    self.assertNotIn(marker, data)

    def test_legacy_offer_and_envelope_validators_remain_readable(self) -> None:
        offer_schema = json.loads((BUNDLE_ROOT / "schema" / "task" / "offer.schema.json").read_text(encoding="utf-8"))
        self.assertEqual({"v1", "v2", "v3", "v4", "base", "sha1", "sha256", "gates", "policy"}, set(offer_schema["$defs"]))
        self.assertEqual(4, len(offer_schema["oneOf"]))


if __name__ == "__main__":
    unittest.main()
