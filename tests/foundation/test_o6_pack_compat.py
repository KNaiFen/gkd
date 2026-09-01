from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.foundation.helpers import copy_source, gkd_bundle, run_cli


class O6PackCompatibilityContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _future_source(self, name: str = "future") -> Path:
        destination = self.root / name
        destination.mkdir()
        source = copy_source(destination)
        gkd_bundle.generate(source)
        return source

    def _legacy_source(self, name: str = "legacy") -> Path:
        source = self._future_source(name)
        declaration_path = source / "source.toml"
        declaration = declaration_path.read_text(encoding="utf-8")
        declaration = declaration.replace("schema_version = 2", "schema_version = 1", 1)
        declaration = declaration.replace('[[packs]]\nname = "ci-advice"\n\n', "", 1)
        declaration = declaration.replace('[[packs]]\nname = "review-remediation"\n\n', "", 1)
        declaration = declaration.replace('pack = "ci-advice"\n', "")
        declaration = declaration.replace('pack = "review-remediation"\n', "")
        declaration_path.write_text(declaration, encoding="utf-8")
        schema_path = source / "manifest.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["schemaVersion"] = 1
        schema["required"].remove("packs")
        schema["properties"].pop("packs")
        schema["properties"]["schemaVersion"] = {"const": 1}
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        return source

    def test_v1_source_cli_generate_and_verify_remain_supported(self) -> None:
        source = self._legacy_source()
        generated = run_cli("generate", "--source-root", str(source))
        self.assertEqual(0, generated.returncode, generated.stderr)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        lock = json.loads((source / "manifest.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["schemaVersion"])
        self.assertNotIn("packs", manifest)
        self.assertNotIn("packs", lock)
        self.assertNotIn("coreDigest", lock)
        verified = gkd_bundle.verify_bundle_root(source / "payload")
        self.assertEqual("verified", verified["status"])
        self.assertEqual([], verified["availablePacks"])

    def test_v1_source_rejects_pack_declarations(self) -> None:
        source = self._future_source("v1-packs")
        declaration_path = source / "source.toml"
        declaration_path.write_text(
            declaration_path.read_text(encoding="utf-8").replace("schema_version = 2", "schema_version = 1", 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_SOURCE_DECLARATION"):
            gkd_bundle.generate(source)

    def test_v2_producer_and_consumer_bind_declared_packs(self) -> None:
        current_root = self.root / "current"
        current_root.mkdir()
        current = copy_source(current_root)
        current_manifest = json.loads((current / "manifest.json").read_text(encoding="utf-8"))
        current_lock = json.loads((current / "manifest.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(2, current_manifest["schemaVersion"])
        self.assertEqual(112, len(current_lock["installFiles"]))
        self.assertEqual(["ci-advice", "review-remediation"], [item["name"] for item in current_manifest["packs"]])

        source = self._future_source("all-packs")
        verified_source = gkd_bundle.verify_bundle_root(source / "payload")
        self.assertEqual(["ci-advice", "review-remediation"], verified_source["availablePacks"])
        lock = json.loads((source / "manifest.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(2, lock["schemaVersion"])
        self.assertEqual(["ci-advice", "review-remediation"], [item["name"] for item in lock["packs"]])
        self.assertRegex(lock["coreDigest"], r"^[0-9a-f]{64}$")

        target = self.root / "target"
        target.mkdir()
        installed = gkd_bundle.install(
            source,
            self.root,
            target,
            ("ci-advice", "review-remediation"),
        )
        self.assertEqual(["ci-advice", "review-remediation"], installed["installedPacks"])
        verified = gkd_bundle.verify(self.root, target)
        self.assertEqual(installed["coreDigest"], verified["coreDigest"])
        self.assertEqual(installed["installedPacks"], verified["installedPacks"])

    def test_v2_core_install_and_pack_drift_fail_closed(self) -> None:
        source = self._future_source("core")
        target = self.root / "target"
        target.mkdir()
        gkd_bundle.install(source, self.root, target)
        self.assertEqual([], gkd_bundle.verify(self.root, target)["installedPacks"])

        manifest_path = target / "gkd/.bundle/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packs"][0]["components"] = []
        manifest_path.write_bytes(gkd_bundle.canonical_bytes(manifest))
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INSTALLED_MANIFEST_INVALID"):
            gkd_bundle.verify(self.root, target)

    def test_v2_unknown_owner_and_symlinked_payload_are_rejected(self) -> None:
        source = self._future_source("unknown-owner")
        declaration_path = source / "source.toml"
        declaration = declaration_path.read_text(encoding="utf-8")
        declaration_path.write_text(
            declaration.replace('pack = "ci-advice"', 'pack = "unknown"', 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_COMPONENT"):
            gkd_bundle.generate(source)

        source = self._future_source("symlink")
        payload = source / "payload/bin/gkd-resource-scanner"
        payload.unlink()
        payload.symlink_to("gkd-bundle")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_PAYLOAD_TYPE"):
            gkd_bundle.generate(source)

    def test_v2_installed_extra_and_content_drift_are_rejected(self) -> None:
        source = self._future_source("content")
        target = self.root / "target"
        target.mkdir()
        gkd_bundle.install(source, self.root, target, ("ci-advice",))
        scanner = target / "gkd/bin/gkd-resource-scanner"
        scanner.write_bytes(scanner.read_bytes() + b"\n")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_CONTENT"):
            gkd_bundle.verify(self.root, target)

        target = self.root / "extra"
        target.mkdir()
        gkd_bundle.install(source, self.root, target, ("ci-advice",))
        os.symlink("gkd-resource-scanner", target / "gkd/bin/linked")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_TYPE"):
            gkd_bundle.verify(self.root, target)


if __name__ == "__main__":
    unittest.main()
