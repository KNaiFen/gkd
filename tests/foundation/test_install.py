from __future__ import annotations

import json
import os
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
