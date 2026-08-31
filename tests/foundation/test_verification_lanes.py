from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest

from gkd_task.results import (
    CanonicalResultError,
    DEFAULT_LANE,
    DEFAULT_PROFILE,
    DEFAULT_SCOPE_NAMES,
    CI_ADVICE_LANE,
    CI_ADVICE_PROFILE,
    CI_ADVICE_SCOPE_NAMES,
    HISTORICAL_LANE,
    HISTORICAL_PROFILE,
    HISTORICAL_SCOPE_NAMES,
    LEGACY_SCOPE_NAMES,
    O6_CORE_SCOPE_NAMES,
    OPTIONAL_PACK_LANE,
    OPTIONAL_PACK_PROFILE,
    OPTIONAL_PACK_SCOPE_NAMES,
    REVIEW_REMEDIATION_LANE,
    REVIEW_REMEDIATION_PROFILE,
    REVIEW_REMEDIATION_SCOPE_NAMES,
    canonical_bytes,
    digest_object,
    load_canonical_results,
    select_canonical_results,
    write_manifest,
    write_scope_result,
)


class VerificationLaneContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[2]
        self.head = subprocess.check_output(("git", "-C", str(self.repository), "rev-parse", "HEAD"), text=True).strip()
        self.digest = "a" * 64

    def _scope(self, root: Path, name: str) -> None:
        write_scope_result(
            root / f"{name}.json",
            base_sha=self.head,
            head_sha=self.head,
            scope=name,
            tests=[{"id": name, "status": "pass"}],
            verifier_digest=self.digest,
        )

    def test_default_and_historical_lanes_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            default = root / "default"
            historical = root / "historical"
            default.mkdir()
            historical.mkdir()
            write_manifest(default / "manifest.json", base_sha=self.head, head_sha=self.head, verifier_digest=self.digest)
            self._scope(default, "foundation")
            write_manifest(
                historical / "manifest.json",
                base_sha=self.head,
                head_sha=self.head,
                verifier_digest=self.digest,
                lane=HISTORICAL_LANE,
                profile=HISTORICAL_PROFILE,
            )
            self._scope(historical, "watcher-core-and-live-negative")

            self.assertEqual(DEFAULT_LANE, "default")
            self.assertEqual(DEFAULT_PROFILE, "core")
            self.assertNotIn("watcher-core-and-live-negative", DEFAULT_SCOPE_NAMES)
            self.assertNotIn("m3-resource-scanner", DEFAULT_SCOPE_NAMES)
            self.assertNotIn("m3-review-core", DEFAULT_SCOPE_NAMES)
            self.assertEqual(HISTORICAL_SCOPE_NAMES, ("watcher-core-and-live-negative",))
            self.assertEqual(CI_ADVICE_SCOPE_NAMES, ("m3-resource-scanner",))
            self.assertEqual(REVIEW_REMEDIATION_SCOPE_NAMES, ("m3-review-core",))
            self.assertEqual(OPTIONAL_PACK_SCOPE_NAMES, ("m3-resource-scanner", "m3-review-core"))
            self.assertEqual("foundation", load_canonical_results(default, "foundation", self.repository)["scope"])
            self.assertEqual(
                "watcher-core-and-live-negative",
                load_canonical_results(historical, "watcher-core-and-live-negative", self.repository)["scope"],
            )
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCOPE_INVALID"):
                load_canonical_results(default, "watcher-core-and-live-negative", self.repository)

    def test_optional_pack_lanes_are_explicit_and_composable(self) -> None:
        cases = (
            (CI_ADVICE_LANE, CI_ADVICE_PROFILE, CI_ADVICE_SCOPE_NAMES),
            (REVIEW_REMEDIATION_LANE, REVIEW_REMEDIATION_PROFILE, REVIEW_REMEDIATION_SCOPE_NAMES),
            (OPTIONAL_PACK_LANE, OPTIONAL_PACK_PROFILE, OPTIONAL_PACK_SCOPE_NAMES),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for index, (lane, profile, scopes) in enumerate(cases):
                root = Path(temporary) / str(index)
                root.mkdir()
                write_manifest(root / "manifest.json", base_sha=self.head, head_sha=self.head, verifier_digest=self.digest, lane=lane, profile=profile)
                for scope in scopes:
                    self._scope(root, scope)
                    self.assertEqual(scope, load_canonical_results(root, scope, self.repository)["scope"])

    def test_unknown_or_mismatched_lane_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_manifest(root / "manifest.json", base_sha=self.head, head_sha=self.head, verifier_digest=self.digest)
            self._scope(root, "foundation")
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            manifest["profile"] = HISTORICAL_PROFILE
            manifest["manifestDigest"] = digest_object({key: value for key, value in manifest.items() if key != "manifestDigest"})
            (root / "manifest.json").write_bytes(canonical_bytes(manifest))
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCHEMA_INVALID"):
                load_canonical_results(root, "foundation", self.repository)

    def test_o6_core_manifest_is_an_explicit_future_default_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = {
                "baseSha": self.head,
                "environment": {
                    "dependenciesInstalled": False,
                    "platform": platform.system().lower(),
                    "pythonVersion": sys.version.split()[0],
                },
                "headSha": self.head,
                "lane": DEFAULT_LANE,
                "profile": DEFAULT_PROFILE,
                "schemaVersion": 2,
                "scopes": list(O6_CORE_SCOPE_NAMES),
                "verifierDigest": self.digest,
            }
            manifest["manifestDigest"] = digest_object(manifest)
            (root / "manifest.json").write_bytes(canonical_bytes(manifest))
            self._scope(root, "foundation")
            self.assertEqual(8, len(DEFAULT_SCOPE_NAMES))
            self.assertEqual(8, len(O6_CORE_SCOPE_NAMES))
            self.assertEqual(DEFAULT_SCOPE_NAMES, O6_CORE_SCOPE_NAMES)
            self.assertEqual(
                "foundation",
                load_canonical_results(root, "foundation", self.repository)["scope"],
            )

            manifest["lane"] = "unknown"
            manifest["profile"] = "unknown"
            manifest["manifestDigest"] = digest_object({key: value for key, value in manifest.items() if key != "manifestDigest"})
            (root / "manifest.json").write_bytes(canonical_bytes(manifest))
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCHEMA_INVALID"):
                load_canonical_results(root, "foundation", self.repository)

    def test_legacy_manifest_remains_strictly_bound_to_all_legacy_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = {
                "baseSha": self.head,
                "environment": {
                    "dependenciesInstalled": False,
                    "platform": platform.system().lower(),
                    "pythonVersion": sys.version.split()[0],
                },
                "headSha": self.head,
                "schemaVersion": 1,
                "scopes": list(LEGACY_SCOPE_NAMES),
                "verifierDigest": self.digest,
            }
            manifest["manifestDigest"] = digest_object(manifest)
            (root / "manifest.json").write_bytes(canonical_bytes(manifest))
            self._scope(root, "foundation")
            self.assertEqual("foundation", load_canonical_results(root, "foundation", self.repository)["scope"])

    def test_result_selection_reuses_a_validated_complete_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = [
                "tests.example.Contracts.test_first",
                "tests.example.Contracts.test_second",
            ]
            write_manifest(root / "manifest.json", base_sha=self.head, head_sha=self.head, verifier_digest=self.digest)
            result = write_scope_result(
                root / "task-core.json",
                base_sha=self.head,
                head_sha=self.head,
                scope="task-core",
                tests=[{"id": test_id, "status": "pass"} for test_id in expected],
                verifier_digest=self.digest,
            )

            selection = select_canonical_results(root, "task-core", self.repository, expected, [expected[1]])

            self.assertEqual(result["resultDigest"], selection["resultDigest"])
            self.assertEqual(self.head, selection["headSha"])
            self.assertEqual([{"id": expected[1], "status": "pass"}], selection["tests"])

    def test_result_selection_rejects_missing_duplicate_or_drifted_scope_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = [
                "tests.example.Contracts.test_first",
                "tests.example.Contracts.test_second",
            ]
            write_manifest(root / "manifest.json", base_sha=self.head, head_sha=self.head, verifier_digest=self.digest)
            write_scope_result(
                root / "task-core.json",
                base_sha=self.head,
                head_sha=self.head,
                scope="task-core",
                tests=[{"id": expected[0], "status": "pass"}],
                verifier_digest=self.digest,
            )
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_TEST_IDS_MISMATCH"):
                select_canonical_results(root, "task-core", self.repository, expected, [expected[0]])

            write_scope_result(
                root / "task-core.json",
                base_sha=self.head,
                head_sha=self.head,
                scope="task-core",
                tests=[{"id": test_id, "status": "pass"} for test_id in expected],
                verifier_digest=self.digest,
            )
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_TEST_IDS_INVALID"):
                select_canonical_results(root, "task-core", self.repository, expected, [expected[0], expected[0]])

            drifted_head = "0" * 40
            write_manifest(root / "manifest.json", base_sha=self.head, head_sha=drifted_head, verifier_digest=self.digest)
            write_scope_result(
                root / "task-core.json",
                base_sha=self.head,
                head_sha=drifted_head,
                scope="task-core",
                tests=[{"id": test_id, "status": "pass"} for test_id in expected],
                verifier_digest=self.digest,
            )
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_HEAD_MISMATCH"):
                select_canonical_results(root, "task-core", self.repository, expected, [expected[0]])
