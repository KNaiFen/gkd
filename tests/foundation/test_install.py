from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from tests.foundation.helpers import copy_source, gkd_bundle, run_cli


class InstallationContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.boundary = Path(self.temporary.name)
        self.source = copy_source(self.boundary)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _target(self, name: str = "target") -> Path:
        target = self.boundary / name
        target.mkdir()
        return target

    def _installed(self, name: str = "target") -> Path:
        target = self._target(name)
        gkd_bundle.install(self.source, self.boundary, target)
        return target

    def test_two_clean_installs_match_and_repeat_is_idempotent(self) -> None:
        first = self._target("first")
        second = self._target("second")
        first_result = gkd_bundle.install(self.source, self.boundary, first)
        repeat_result = gkd_bundle.install(self.source, self.boundary, first)
        second_result = gkd_bundle.install(self.source, self.boundary, second)
        self.assertEqual(first_result["contentDigest"], second_result["contentDigest"])
        self.assertEqual(repeat_result["status"], "already_installed")
        self.assertEqual(gkd_bundle.verify(self.boundary, first), gkd_bundle.verify(self.boundary, second))
        self.assertEqual(gkd_bundle.version(self.boundary, first), gkd_bundle.version(self.boundary, second))

    def test_cli_has_no_default_target_or_temporary_root(self) -> None:
        result = run_cli("install", "--source-root", "canonical")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["error"], "INVALID_ARGUMENTS")

    def test_target_outside_system_temporary_boundary_is_rejected(self) -> None:
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_OUTSIDE_TEMPORARY_BOUNDARY"):
            gkd_bundle.install(self.source, Path.cwd(), Path.cwd())

    def test_target_symlink_is_rejected(self) -> None:
        real = self._target("real")
        linked = self.boundary / "linked"
        linked.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INVALID_TARGET"):
            gkd_bundle.install(self.source, self.boundary, linked)

    def test_unknown_target_content_is_not_overwritten(self) -> None:
        target = self._target()
        (target / "gkd").mkdir()
        (target / "gkd/unknown.txt").write_text("keep\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_NOT_CLEAN"):
            gkd_bundle.install(self.source, self.boundary, target)
        self.assertEqual((target / "gkd/unknown.txt").read_text(encoding="utf-8"), "keep\n")

    def test_target_owned_root_symlink_escape_is_rejected(self) -> None:
        target = self._target()
        outside = self._target("outside")
        (target / "gkd").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_NOT_CLEAN"):
            gkd_bundle.install(self.source, self.boundary, target)

    def test_verify_detects_content_drift(self) -> None:
        target = self._installed()
        library = target / "gkd/lib/gkd_bundle.py"
        library.write_bytes(library.read_bytes() + b"\n")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_CONTENT"):
            gkd_bundle.verify(self.boundary, target)

    def test_verify_detects_missing_file(self) -> None:
        target = self._installed()
        (target / "gkd/lib/gkd_bundle.py").unlink()
        with self.assertRaises(gkd_bundle.BundleError) as raised:
            gkd_bundle.verify(self.boundary, target)
        self.assertIn(raised.exception.code, {"TARGET_DRIFT_MISSING", "TARGET_DRIFT_EXTRA_OR_MISSING"})

    def test_verify_detects_extra_file(self) -> None:
        target = self._installed()
        (target / "gkd/extra.txt").write_text("extra\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_EXTRA_OR_MISSING"):
            gkd_bundle.verify(self.boundary, target)

    def test_verify_detects_extra_directory(self) -> None:
        target = self._installed()
        (target / "gkd/extra").mkdir()
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_DIRECTORY"):
            gkd_bundle.verify(self.boundary, target)

    def test_verify_detects_mode_drift(self) -> None:
        drift_cases = (("executable", "gkd/bin/gkd-bundle", 0o644),) + tuple(
            ("metadata", path, 0o755)
            for path in (
                gkd_bundle.SCHEMA_TARGET,
                gkd_bundle.MANIFEST_TARGET,
                gkd_bundle.LOCK_TARGET,
                gkd_bundle.INSTALL_TARGET,
            )
        )
        for index, (kind, relative_path, mode) in enumerate(drift_cases):
            with self.subTest(kind=kind, path=relative_path):
                target = self._installed(f"mode-drift-{index}")
                os.chmod(target / relative_path, mode)
                with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_MODE"):
                    gkd_bundle.verify(self.boundary, target)

    def test_verify_detects_symlink_drift(self) -> None:
        target = self._installed()
        library = target / "gkd/lib/gkd_bundle.py"
        library.unlink()
        library.symlink_to("../bin/gkd-bundle")
        with self.assertRaises(gkd_bundle.BundleError) as raised:
            gkd_bundle.verify(self.boundary, target)
        self.assertIn(raised.exception.code, {"TARGET_DRIFT_TYPE", "TARGET_DRIFT_SYMLINK"})

    def test_manifest_and_lock_are_installed_from_source(self) -> None:
        target = self._installed()
        self.assertEqual(
            (target / gkd_bundle.MANIFEST_TARGET).read_bytes(),
            (self.source / "manifest.json").read_bytes(),
        )
        self.assertEqual(
            (target / gkd_bundle.LOCK_TARGET).read_bytes(),
            (self.source / "manifest.lock.json").read_bytes(),
        )

    def test_explicit_inputs_are_not_installed_and_fixture_leak_fails_closed(self) -> None:
        target = self._installed()
        lock = json.loads((target / gkd_bundle.LOCK_TARGET).read_text(encoding="utf-8"))
        self.assertEqual(5, len(lock["inputFiles"]))
        self.assertFalse((target / "gkd/fixtures").exists())
        leaked = target / "gkd/fixtures/release/traceability.json"
        leaked.parent.mkdir(parents=True)
        leaked.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_EXTRA_OR_MISSING"):
            gkd_bundle.verify(self.boundary, target)

    def test_default_install_excludes_optional_pack_runtime_and_skills(self) -> None:
        target = self._installed()
        verified = gkd_bundle.verify(self.boundary, target)
        self.assertEqual([], verified["installedPacks"])
        for relative in (
            "gkd/bin/gkd-resource-scanner",
            "gkd/bin/gkd-review",
            "gkd/lib/gkd_review",
            "gkd/lib/gkd_ci/resources.py",
            "gkd/schema/review",
            "gkd/skills/gkd-optimize-ci",
            "gkd/skills/gkd-review-remediation",
        ):
            self.assertFalse((target / relative).exists(), relative)

    def test_optional_packs_stage_verify_and_remove_by_name(self) -> None:
        target = self._installed()
        names = ("ci-advice", "review-remediation")
        staged = gkd_bundle.stage_packs(self.source, self.boundary, target, names)
        self.assertEqual("staged", staged["status"])
        self.assertEqual(names, tuple(item["name"] for item in staged["packs"]))
        self.assertEqual(names, tuple(gkd_bundle.verify(self.boundary, target)["installedPacks"]))
        self.assertEqual("verified", gkd_bundle.verify_packs(self.boundary, target, names)["status"])
        self.assertTrue((target / "gkd/bin/gkd-resource-scanner").is_file())
        self.assertTrue((target / "gkd/bin/gkd-review").is_file())
        self.assertEqual("already_staged", gkd_bundle.stage_packs(self.source, self.boundary, target, names)["status"])
        self.assertEqual("removed", gkd_bundle.remove_packs(self.boundary, target, names)["status"])
        self.assertEqual([], gkd_bundle.verify(self.boundary, target)["installedPacks"])

    def test_optional_pack_unknown_tampered_and_wrong_surface_fail_closed(self) -> None:
        target = self._installed()
        before = (target / gkd_bundle.INSTALL_TARGET).read_bytes()
        with self.assertRaisesRegex(gkd_bundle.BundleError, "PACK_UNKNOWN"):
            gkd_bundle.stage_packs(self.source, self.boundary, target, ("unknown",))
        self.assertEqual(before, (target / gkd_bundle.INSTALL_TARGET).read_bytes())
        with self.assertRaisesRegex(gkd_bundle.BundleError, "PACK_NOT_STAGED"):
            gkd_bundle.verify_packs(self.boundary, target, ("ci-advice",))
        pack_file = self.source / "payload/lib/gkd_ci/resources.py"
        pack_file.write_bytes(pack_file.read_bytes() + b"\n")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "LOCK_OR_DIGEST_MISMATCH"):
            gkd_bundle.stage_packs(self.source, self.boundary, target, ("ci-advice",))
        self.assertEqual(before, (target / gkd_bundle.INSTALL_TARGET).read_bytes())

    def test_optional_pack_drift_is_detected_before_remove(self) -> None:
        target = self._installed()
        gkd_bundle.stage_packs(self.source, self.boundary, target, ("ci-advice",))
        resource = target / "gkd/lib/gkd_ci/resources.py"
        resource.write_bytes(resource.read_bytes() + b"\n")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_CONTENT"):
            gkd_bundle.verify_packs(self.boundary, target, ("ci-advice",))
        with self.assertRaisesRegex(gkd_bundle.BundleError, "TARGET_DRIFT_CONTENT"):
            gkd_bundle.remove_packs(self.boundary, target, ("ci-advice",))

    def test_optional_pack_cli_stages_verifies_and_removes(self) -> None:
        target = self._installed()
        common = ("--temporary-root", str(self.boundary), "--target", str(target), "--pack", "ci-advice")
        staged = run_cli("pack-stage", "--source-root", str(self.source), *common)
        self.assertEqual(0, staged.returncode, staged.stderr)
        self.assertEqual("staged", json.loads(staged.stdout)["status"])
        verified = run_cli("pack-verify", *common)
        self.assertEqual(0, verified.returncode, verified.stderr)
        self.assertEqual("verified", json.loads(verified.stdout)["status"])
        removed = run_cli("pack-remove", *common)
        self.assertEqual(0, removed.returncode, removed.stderr)
        self.assertEqual("removed", json.loads(removed.stdout)["status"])

    def test_installed_gkd_main_imports_its_installed_library(self) -> None:
        target = self._installed()
        command = [str(target / "gkd/bin/gkd-main"), "--help"]
        result = __import__("subprocess").run(command, text=True, stdout=__import__("subprocess").PIPE, stderr=__import__("subprocess").PIPE, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("planning", result.stdout)

    def test_legacy_schema_v1_full_install_remains_readable(self) -> None:
        target = self._target("legacy-v1")
        manifest = json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))
        manifest["schemaVersion"] = 1
        manifest.pop("packs")
        for component in manifest["components"]:
            component.pop("pack", None)
        schema = json.loads((self.source / "manifest.schema.json").read_text(encoding="utf-8"))
        schema["schemaVersion"] = 1
        schema["required"].remove("packs")
        schema["properties"].pop("packs")
        schema["properties"]["schemaVersion"] = {"const": 1}
        schema_bytes = (json.dumps(schema, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        manifest_bytes = gkd_bundle.canonical_bytes(manifest)
        current = json.loads((self.source / "manifest.lock.json").read_text(encoding="utf-8"))
        install_files = [{key: value for key, value in item.items() if key != "pack"} for item in current["installFiles"]]
        input_files = [{key: value for key, value in item.items() if key != "pack"} for item in current["inputFiles"]]
        digest_inputs = [
            gkd_bundle._digest_record("manifest.schema.json", "0644", schema_bytes),
            gkd_bundle._digest_record("manifest.json", "0644", manifest_bytes),
        ]
        for item in install_files:
            digest_inputs.append(gkd_bundle._digest_record(item["source"], item["mode"], (self.source / item["source"]).read_bytes()))
        for item in input_files:
            digest_inputs.append({key: item[key] for key in ("source", "type", "mode", "sha256")})
            digest_inputs[-1]["path"] = digest_inputs[-1].pop("source")
        digest_inputs.sort(key=lambda item: item["path"])
        lock = {
            "schemaVersion": 1,
            "bundleVersion": manifest["bundleVersion"],
            "releaseStatus": manifest["releaseStatus"],
            "schemaSha256": gkd_bundle.sha256_bytes(schema_bytes),
            "manifestSha256": gkd_bundle.sha256_bytes(manifest_bytes),
            "digestInputs": digest_inputs,
            "installFiles": install_files,
            "inputFiles": input_files,
            "contentDigest": gkd_bundle.sha256_bytes(b"".join(gkd_bundle.canonical_bytes(item) for item in digest_inputs)),
        }
        for item in install_files:
            destination = target / item["target"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.source / item["source"], destination)
            os.chmod(destination, int(item["mode"], 8))
        gkd_bundle._atomic_write(target / gkd_bundle.SCHEMA_TARGET, schema_bytes)
        gkd_bundle._atomic_write(target / gkd_bundle.MANIFEST_TARGET, manifest_bytes)
        gkd_bundle._atomic_write(target / gkd_bundle.LOCK_TARGET, gkd_bundle.canonical_bytes(lock))
        gkd_bundle._atomic_write(target / gkd_bundle.INSTALL_TARGET, gkd_bundle.canonical_bytes(gkd_bundle._install_record(manifest, lock)))
        verified = gkd_bundle.verify(self.boundary, target)
        self.assertEqual(lock["contentDigest"], verified["contentDigest"])
        self.assertEqual([], verified["installedPacks"])

    def test_legacy_schema_v1_rejects_pack_fields(self) -> None:
        manifest = json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))
        manifest["schemaVersion"] = 1
        manifest.pop("packs")
        manifest["components"][0]["pack"] = "ci-advice"
        with self.assertRaisesRegex(gkd_bundle.BundleError, "INSTALLED_MANIFEST_INVALID"):
            gkd_bundle._validate_installed_manifest(manifest)

    def test_installed_pack_and_core_digest_drift_is_recomputed(self) -> None:
        for field in ("packDigest", "coreDigest"):
            with self.subTest(field=field):
                target = self._installed(f"installed-{field}")
                manifest = json.loads((target / gkd_bundle.MANIFEST_TARGET).read_text(encoding="utf-8"))
                lock_path = target / gkd_bundle.LOCK_TARGET
                lock = json.loads(lock_path.read_text(encoding="utf-8"))
                if field == "packDigest":
                    lock["packs"][0][field] = "0" * 64
                else:
                    lock[field] = "0" * 64
                gkd_bundle._atomic_write(lock_path, gkd_bundle.canonical_bytes(lock))
                gkd_bundle._atomic_write(
                    target / gkd_bundle.INSTALL_TARGET,
                    gkd_bundle.canonical_bytes(gkd_bundle._install_record(manifest, lock)),
                )
                with self.assertRaisesRegex(gkd_bundle.BundleError, "INSTALLED_LOCK_INVALID"):
                    gkd_bundle.verify(self.boundary, target)


if __name__ == "__main__":
    unittest.main()
