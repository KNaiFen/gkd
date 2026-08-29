from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import subprocess

from gkd_task.results import (
    CanonicalResultError,
    DEFAULT_SCOPE_NAMES,
    HISTORICAL_SCOPE_NAMES,
    load_canonical_results,
    write_manifest,
    write_scope_result,
)


class VerificationLaneContracts(unittest.TestCase):
    def test_default_and_historical_results_are_separate_fixed_lanes(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        current_head = subprocess.check_output(
            ("git", "-C", str(repository), "rev-parse", "HEAD"), text=True
        ).strip()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            default = root / "default"
            historical = root / "historical"
            default.mkdir()
            historical.mkdir()
            verifier_digest = "a" * 64
            write_manifest(default / "manifest.json", base_sha=current_head, head_sha=current_head, verifier_digest=verifier_digest)
            write_scope_result(default / "foundation.json", base_sha=current_head, head_sha=current_head, scope="foundation", tests=[{"id": "default", "status": "pass"}], verifier_digest=verifier_digest)
            write_manifest(historical / "manifest.json", base_sha=current_head, head_sha=current_head, verifier_digest=verifier_digest, scope_names=HISTORICAL_SCOPE_NAMES)
            write_scope_result(historical / "watcher-core-and-live-negative.json", base_sha=current_head, head_sha=current_head, scope="watcher-core-and-live-negative", tests=[{"id": "historical", "status": "pass"}], verifier_digest=verifier_digest)

            self.assertNotIn("watcher-core-and-live-negative", DEFAULT_SCOPE_NAMES)
            self.assertEqual(load_canonical_results(historical, "watcher-core-and-live-negative", repository)["scope"], "watcher-core-and-live-negative")
            with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCOPE_MISMATCH"):
                load_canonical_results(default, "watcher-core-and-live-negative", repository)
