from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tests.foundation.helpers import copy_source, gkd_bundle


class ManifestContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = copy_source(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _lock(self) -> dict:
        return json.loads((self.source / "manifest.lock.json").read_text(encoding="utf-8"))

    def test_schema_manifest_lock_and_canonical_sort_are_valid(self) -> None:
        schema = json.loads((self.source / "manifest.schema.json").read_text(encoding="utf-8"))
        manifest = json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))
        _, validated_manifest, lock = gkd_bundle._validated_source(self.source)
        self.assertEqual(schema["schemaVersion"], 1)
        self.assertEqual(manifest, validated_manifest)
        self.assertEqual(manifest["bundleVersion"], "0.1.1")
        self.assertEqual(manifest["releaseStatus"], "release-candidate")
        self.assertEqual(
            [item["name"] for item in manifest["components"]],
            sorted(item["name"] for item in manifest["components"]),
        )
        self.assertEqual(lock["digestInputs"], sorted(lock["digestInputs"], key=lambda item: item["path"]))
        self.assertEqual(lock["installFiles"], sorted(lock["installFiles"], key=lambda item: item["source"]))

    def test_manifest_schema_shape_mutation_is_rejected(self) -> None:
        path = self.source / "manifest.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["required"].remove("components")
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_MANIFEST_SCHEMA"):
            gkd_bundle.generate(self.source)

    def test_repeated_generation_is_byte_identical(self) -> None:
        before = {
            name: (self.source / name).read_bytes()
            for name in ("manifest.json", "manifest.lock.json")
        }
        gkd_bundle.generate(self.source)
        first = {name: (self.source / name).read_bytes() for name in before}
        gkd_bundle.generate(self.source)
        second = {name: (self.source / name).read_bytes() for name in before}
        self.assertEqual(before, first)
        self.assertEqual(first, second)

    def test_bundle_content_change_changes_digest(self) -> None:
        before = self._lock()["contentDigest"]
        library = self.source / "payload/lib/gkd_bundle.py"
        library.write_bytes(library.read_bytes() + b"\n")
        gkd_bundle.generate(self.source)
        self.assertNotEqual(before, self._lock()["contentDigest"])

    def test_bundle_path_change_changes_digest(self) -> None:
        before = self._lock()["contentDigest"]
        old_path = self.source / "payload/lib/gkd_bundle.py"
        new_path = self.source / "payload/lib/foundation_bundle.py"
        old_path.rename(new_path)
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace("payload/lib/gkd_bundle.py", "payload/lib/foundation_bundle.py")
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        gkd_bundle.generate(self.source)
        self.assertNotEqual(before, self._lock()["contentDigest"])

    def test_ordinary_repo_wording_does_not_change_manifest_state(self) -> None:
        before = {
            name: (self.source / name).read_bytes()
            for name in ("manifest.json", "manifest.lock.json")
        }
        (self.root / "README.md").write_text("ordinary wording\n", encoding="utf-8")
        gkd_bundle.generate(self.source)
        after = {name: (self.source / name).read_bytes() for name in before}
        self.assertEqual(before, after)

    def test_unknown_payload_file_is_rejected(self) -> None:
        (self.source / "payload/unknown.txt").write_text("unknown\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "UNDECLARED_OR_MISSING_PAYLOAD"):
            gkd_bundle.generate(self.source)

    def test_missing_payload_file_is_rejected(self) -> None:
        (self.source / "payload/bin/gkd-bundle").unlink()
        with self.assertRaisesRegex(gkd_bundle.BundleError, "UNDECLARED_OR_MISSING_PAYLOAD"):
            gkd_bundle.generate(self.source)

    def test_source_symlink_is_rejected(self) -> None:
        launcher = self.source / "payload/bin/gkd-bundle"
        launcher.unlink()
        launcher.symlink_to("../lib/gkd_bundle.py")
        with self.assertRaises(gkd_bundle.BundleError) as raised:
            gkd_bundle.generate(self.source)
        self.assertIn(raised.exception.code, {"INVALID_PAYLOAD_TYPE", "UNDECLARED_OR_MISSING_PAYLOAD"})

    def test_source_mode_change_is_rejected(self) -> None:
        os.chmod(self.source / "payload/bin/gkd-bundle", 0o644)
        with self.assertRaisesRegex(gkd_bundle.BundleError, "SOURCE_MODE_MISMATCH"):
            gkd_bundle.generate(self.source)

    def test_metadata_mode_mutations_are_rejected_before_generation(self) -> None:
        for name in ("manifest.schema.json", "manifest.json", "manifest.lock.json"):
            with self.subTest(name=name):
                path = self.source / name
                os.chmod(path, 0o755)
                with self.assertRaisesRegex(
                    gkd_bundle.BundleError, "SOURCE_METADATA_MODE_MISMATCH"
                ):
                    gkd_bundle.generate(self.source)
                os.chmod(path, 0o644)

    def test_source_path_traversal_is_rejected(self) -> None:
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace("payload/lib/gkd_bundle.py", "payload/../source.toml")
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_SOURCE_PATH"):
            gkd_bundle.generate(self.source)

    def test_absolute_install_target_is_rejected(self) -> None:
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace("gkd/bin/gkd-bundle", "/tmp/gkd-bundle")
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_TARGET_PATH"):
            gkd_bundle.generate(self.source)

    def test_windows_absolute_install_target_is_rejected(self) -> None:
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace(
            'target = "gkd/bin/gkd-bundle"',
            r"target = 'gkd/C:\temp\gkd-bundle'",
        )
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_TARGET_PATH"):
            gkd_bundle.generate(self.source)

    def test_project_specific_install_target_is_deferred_to_repository_scan(self) -> None:
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace("gkd/bin/gkd-bundle", "gkd/aio/gkd-bundle")
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        gkd_bundle.generate(self.source)
        with self.assertRaisesRegex(
            gkd_bundle.BundleError, "PROJECT_SPECIFIC_SOURCE_CONTENT"
        ):
            gkd_bundle._validate_project_contamination(self.source)

    def test_unrelated_aio_substring_is_allowed_by_generic_manifest(self) -> None:
        declaration = (self.source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace('name = "foundation-cli"', 'name = "maio-cli"')
        (self.source / "source.toml").write_text(declaration, encoding="utf-8")
        gkd_bundle.generate(self.source)

    def test_mutation_manual_manifest_edit_is_rejected(self) -> None:
        path = self.source / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["bundleVersion"] = "0.0.0-dev.99"
        path.write_bytes(gkd_bundle.canonical_bytes(manifest))
        with self.assertRaisesRegex(gkd_bundle.BundleError, "MANIFEST_MISMATCH"):
            gkd_bundle._validated_source(self.source)

    def test_mutation_manual_lock_edit_is_rejected(self) -> None:
        path = self.source / "manifest.lock.json"
        lock = json.loads(path.read_text(encoding="utf-8"))
        lock["contentDigest"] = "0" * 64
        path.write_bytes(gkd_bundle.canonical_bytes(lock))
        with self.assertRaisesRegex(gkd_bundle.BundleError, "LOCK_OR_DIGEST_MISMATCH"):
            gkd_bundle._validated_source(self.source)

    def test_mutation_content_tamper_without_digest_update_is_rejected(self) -> None:
        library = self.source / "payload/lib/gkd_bundle.py"
        library.write_bytes(library.read_bytes() + b"\n")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "LOCK_OR_DIGEST_MISMATCH"):
            gkd_bundle._validated_source(self.source)

    def test_machine_specific_source_content_is_rejected(self) -> None:
        library = self.source / "payload/lib/gkd_bundle.py"
        original = library.read_bytes()
        mutations = (
            b"\n# /Users/example/worktree\n",
            b"\n# /tmp/example\n",
            b"\n# C:\\Users\\example\\worktree\n",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                library.write_bytes(original + mutation)
                with self.assertRaisesRegex(gkd_bundle.BundleError, "FORBIDDEN_SOURCE_CONTENT"):
                    gkd_bundle.generate(self.source)
        library.write_bytes(original)

    def test_bare_usernames_and_unrelated_aio_substrings_are_portable(self) -> None:
        self.assertFalse(
            gkd_bundle._contains_project_marker(b"unrelated_aio_substrings maio payload")
        )
        self.assertTrue(gkd_bundle._contains_project_marker(b"gkd/aio/specialized"))
        for user_name in ("bin", "lib", "gkd"):
            with self.subTest(user_name=user_name), mock.patch.object(
                gkd_bundle.Path,
                "home",
                return_value=Path(f"/Users/{user_name}"),
            ):
                self.assertFalse(
                    gkd_bundle._forbidden_content(f"{user_name} binary maio payload".encode())
                )
                self.assertTrue(
                    gkd_bundle._forbidden_content(
                        f"/Users/{user_name}/workspace/project".encode()
                    )
                )


if __name__ == "__main__":
    unittest.main()
