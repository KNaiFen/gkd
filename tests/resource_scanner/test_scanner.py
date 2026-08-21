from __future__ import annotations

import json
import unittest

from gkd_ci.scanner import scan_artifact, scan_diff, scan_pull_request, validate_scanner_result
from gkd_task.errors import TaskError


class ScannerContracts(unittest.TestCase):
    def test_clean_diff_has_canonical_nonterminal_result(self) -> None:
        result = scan_diff("diff --git a/readme b/readme\n+ordinary text\n", "docs/readme.md")
        validate_scanner_result(result)
        self.assertEqual("clean", result["outcome"])
        self.assertFalse(result["terminal"])

    def test_credential_is_redacted_and_terminal(self) -> None:
        secret = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
        result = scan_diff(f"+token={secret}\n", "src/config.txt")
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual("terminal", result["outcome"])
        self.assertTrue(result["terminal"])
        self.assertNotIn(secret, encoded)
        self.assertNotIn("token=", encoded)
        validate_scanner_result(result)

    def test_pull_request_and_artifact_boundaries_are_explicit(self) -> None:
        pull = scan_pull_request({"title": "change", "body": "details", "files": [{"path": "src/a.py", "patch": "+safe"}]})
        self.assertEqual("pull-request", pull["surface"])
        artifact = scan_artifact({"files": [{"path": "dist/report.txt", "content": "safe"}]})
        self.assertEqual("artifact", artifact["surface"])
        with self.assertRaisesRegex(TaskError, "SCANNER_INPUT_INVALID"):
            scan_artifact({"files": [{"path": "/tmp/report.txt", "content": "safe"}]})

    def test_private_key_and_assignment_patterns_are_terminal(self) -> None:
        result = scan_diff("-----BEGIN PRIVATE KEY-----\nsecret=real-value\n")
        self.assertEqual("terminal", result["outcome"])
        self.assertGreaterEqual(len(result["findings"]), 2)

    def test_scanner_rejects_unknown_surface_and_oversized_input(self) -> None:
        with self.assertRaisesRegex(TaskError, "SCANNER_INPUT_INVALID"):
            scan_pull_request({"title": "", "body": "", "files": [{"path": "a", "patch": "x"}], "extra": True})
        with self.assertRaisesRegex(TaskError, "SCANNER_INPUT_INVALID"):
            scan_diff("x" * (2 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
