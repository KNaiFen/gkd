from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tests.foundation.helpers import copy_governance_repo, gkd_bundle


class EvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = copy_governance_repo(self.root)
        self.protected = self.root / "protected"
        self.protected.mkdir()
        (self.protected / "config.toml").write_text("stable = true\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, name: str) -> tuple[dict, bytes]:
        run_root = self.root / name
        run_root.mkdir()
        output = self.root / f"{name}.json"
        result = gkd_bundle.generate_evidence(
            self.repo / "canonical", run_root, self.protected, output
        )
        return result, output.read_bytes()

    def test_two_clean_evidence_generations_are_byte_identical(self) -> None:
        first_result, first = self._run("run-a")
        second_result, second = self._run("run-b")
        self.assertEqual(first_result, second_result)
        self.assertEqual(first, second)
        self.assertEqual(list((self.root / "run-a").iterdir()), [])
        self.assertEqual(list((self.root / "run-b").iterdir()), [])

    def test_evidence_digest_is_canonical_and_self_excluding(self) -> None:
        _, raw = self._run("run")
        evidence = json.loads(raw)
        digest = evidence.pop("evidenceDigest")
        self.assertEqual(digest, gkd_bundle.sha256_bytes(gkd_bundle.canonical_bytes(evidence)))
        self.assertEqual(evidence["outcome"], "canonical_foundation_ready")
        self.assertTrue(evidence["protectedHome"]["unchanged"])

    def test_evidence_contains_no_temporary_or_machine_path(self) -> None:
        _, raw = self._run("run")
        text = raw.decode("utf-8").casefold()
        self.assertNotIn(str(self.root).casefold(), text)
        self.assertFalse(gkd_bundle._forbidden_content(raw))

    def test_protected_surface_change_is_detected(self) -> None:
        before = gkd_bundle._snapshot_protected(self.protected)
        (self.protected / "config.toml").write_text("stable = false\n", encoding="utf-8")
        after = gkd_bundle._snapshot_protected(self.protected)
        self.assertNotEqual(before, after)

    def test_output_inside_protected_root_fails_without_writing(self) -> None:
        run_root = self.root / "protected-output-run"
        run_root.mkdir()
        protected_output_root = self.protected / "gkd"
        protected_output_root.mkdir()
        output = protected_output_root / "evidence.json"
        with self.assertRaisesRegex(gkd_bundle.BundleError, "EVIDENCE_OUTPUT_OVERLAP"):
            gkd_bundle.generate_evidence(
                self.repo / "canonical", run_root, self.protected, output
            )
        self.assertFalse(output.exists())

    def test_output_symlinked_into_protected_root_is_rejected(self) -> None:
        run_root = self.root / "symlink-output-run"
        run_root.mkdir()
        (self.protected / "gkd").mkdir()
        linked = self.root / "protected-link"
        linked.symlink_to(self.protected, target_is_directory=True)
        output = linked / "gkd/evidence.json"
        with self.assertRaisesRegex(gkd_bundle.BundleError, "EVIDENCE_OUTPUT_OVERLAP"):
            gkd_bundle.generate_evidence(
                self.repo / "canonical", run_root, self.protected, output
            )
        self.assertFalse(output.exists())

    def test_output_inside_source_or_temporary_root_is_rejected(self) -> None:
        for location in ("source", "temporary"):
            with self.subTest(location=location):
                run_root = self.root / f"{location}-output-run"
                run_root.mkdir()
                output = (
                    self.repo / "canonical/evidence.json"
                    if location == "source"
                    else run_root / "evidence.json"
                )
                with self.assertRaisesRegex(
                    gkd_bundle.BundleError, "EVIDENCE_OUTPUT_OVERLAP"
                ):
                    gkd_bundle.generate_evidence(
                        self.repo / "canonical", run_root, self.protected, output
                    )
                self.assertFalse(output.exists())

    def test_cleanup_failure_cannot_publish_ready_evidence(self) -> None:
        run_root = self.root / "cleanup-failure-run"
        run_root.mkdir()
        output = self.root / "cleanup-failure.json"
        with mock.patch.object(gkd_bundle.shutil, "rmtree", return_value=None):
            with self.assertRaisesRegex(
                gkd_bundle.BundleError, "EVIDENCE_CLEANUP_FAILED"
            ):
                gkd_bundle.generate_evidence(
                    self.repo / "canonical", run_root, self.protected, output
                )
        self.assertFalse(output.exists())

    def test_final_snapshot_occurs_only_after_install_cleanup(self) -> None:
        run_root = self.root / "snapshot-order-run"
        run_root.mkdir()
        output = self.root / "snapshot-order.json"
        observed_install_state = []
        original_snapshot = gkd_bundle._snapshot_protected

        def recording_snapshot(root: Path) -> dict:
            observed_install_state.append(
                ((run_root / "install-a").exists(), (run_root / "install-b").exists())
            )
            return original_snapshot(root)

        with mock.patch.object(
            gkd_bundle, "_snapshot_protected", side_effect=recording_snapshot
        ):
            gkd_bundle.generate_evidence(
                self.repo / "canonical", run_root, self.protected, output
            )
        self.assertEqual(observed_install_state, [(False, False), (False, False)])

    def test_project_specific_path_fails_at_evidence_boundary(self) -> None:
        source = self.repo / "canonical"
        declaration = (source / "source.toml").read_text(encoding="utf-8")
        declaration = declaration.replace("gkd/bin/gkd-bundle", "gkd/aio/gkd-bundle")
        (source / "source.toml").write_text(declaration, encoding="utf-8")
        gkd_bundle.generate(source)
        run_root = self.root / "project-marker-run"
        run_root.mkdir()
        output = self.root / "project-marker.json"
        with self.assertRaisesRegex(
            gkd_bundle.BundleError, "PROJECT_SPECIFIC_SOURCE_CONTENT"
        ):
            gkd_bundle.generate_evidence(source, run_root, self.protected, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
