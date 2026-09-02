from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.foundation.helpers import copy_source, gkd_bundle


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
        self.assertEqual(111, len(current_lock["installFiles"]))
        self.assertEqual(["ci-advice", "legacy-automatic", "review-remediation"], [item["name"] for item in current_manifest["packs"]])

        source = self._future_source("all-packs")
        verified_source = gkd_bundle.verify_bundle_root(source / "payload")
        self.assertEqual(["ci-advice", "legacy-automatic", "review-remediation"], verified_source["availablePacks"])
        lock = json.loads((source / "manifest.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(2, lock["schemaVersion"])
        self.assertEqual(["ci-advice", "legacy-automatic", "review-remediation"], [item["name"] for item in lock["packs"]])
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
