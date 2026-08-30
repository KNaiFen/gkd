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
    HISTORICAL_LANE,
    HISTORICAL_PROFILE,
    HISTORICAL_SCOPE_NAMES,
    LEGACY_SCOPE_NAMES,
    canonical_bytes,
    digest_object,
    load_canonical_results,
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
            write_manifest(
                default / "manifest.json",
                base_sha=self.head,
                head_sha=self.head,
                verifier_digest=self.digest,
                lane=DEFAULT_LANE,
                profile=DEFAULT_PROFILE,
            )
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

            self.assertNotIn("watcher-core-and-live-negative", DEFAULT_SCOPE_NAMES)
            self.assertEqual(HISTORICAL_SCOPE_NAMES, ("watcher-core-and-live-negative",))
            self.assertEqual("foundation", load_canonical_results(default, "foundation", self.repository)["scope"])
            self.assertEqual(
                "watcher-core-and-live-negative",
                load_canonical_results(historical, "watcher-core-and-live-negative", self.repository)["scope"],
            )
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCOPE_INVALID"):
                load_canonical_results(default, "watcher-core-and-live-negative", self.repository)

    def test_unknown_or_mismatched_lane_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_manifest(
                root / "manifest.json",
                base_sha=self.head,
                head_sha=self.head,
                verifier_digest=self.digest,
                lane=DEFAULT_LANE,
                profile=DEFAULT_PROFILE,
            )
            self._scope(root, "foundation")
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            manifest["profile"] = HISTORICAL_PROFILE
            manifest["manifestDigest"] = digest_object({key: value for key, value in manifest.items() if key != "manifestDigest"})
            (root / "manifest.json").write_bytes(canonical_bytes(manifest))
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCHEMA_INVALID"):
                load_canonical_results(root, "foundation", self.repository)

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
