from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gkd_finalization.core import build_finalization, promotion_plan, validate_finalization
from gkd_task.canonical import canonical_bytes, digest_object
from gkd_task.errors import TaskError
from tests.finalization.helpers import finalization_input


class FinalizationContracts(unittest.TestCase):
    def test_closeout_record_is_canonical_and_uses_at_most_two_prs(self) -> None:
        record = build_finalization(finalization_input())
        validate_finalization(record)
        self.assertEqual("closeout-ready", record["finalization"]["phase"])
        self.assertEqual(2, len([value for value in (record["task"]["taskPr"], record["task"]["finalizationPr"]) if value is not None]))
        self.assertEqual(record["metadata"]["sourceSha"], record["metadata"]["mainSha"])
        self.assertEqual(record["metadata"]["sourceSha"], record["evidence"]["sourceSha"])

    def test_closeout_rejects_product_logic_release_side_effects_and_release_bindings(self) -> None:
        for field, value in (("productLogic", True), ("releaseSideEffects", True), ("adapterDigest", "1" * 64), ("authorizationDigest", "2" * 64), ("assets", [{"name": "asset", "sourceSha": "a" * 40, "bundleDigest": "b" * 64, "sha256": "c" * 64}])):
            with self.subTest(field=field):
                source = finalization_input()
                source[field] = value
                with self.assertRaisesRegex(TaskError, "CLOSEOUT_SCOPE_VIOLATION"):
                    build_finalization(source)

    def test_same_sha_promotion_plan_and_matching_retry_are_idempotent(self) -> None:
        record = build_finalization(finalization_input("release"))
        first = promotion_plan(record)
        request = first["request"]
        self.assertEqual("promotion-ready", first["status"])
        self.assertEqual(record["metadata"]["sourceSha"], request["targetSha"])
        self.assertEqual(request["targetSha"], request["releaseSha"])
        existing = {
            "tagName": request["tagName"],
            "targetSha": request["targetSha"],
            "releaseSha": request["releaseSha"],
            "assetsDigest": digest_object(request["assets"]),
            "provenanceDigest": request["provenanceDigest"],
        }
        retry = promotion_plan(record, existing)
        self.assertEqual("already-promoted", retry["status"])
        existing["releaseSha"] = "0" * 40
        with self.assertRaisesRegex(TaskError, "PROMOTION_CONFLICT"):
            promotion_plan(record, existing)

    def test_public_cli_validates_and_never_exposes_a_release_writer(self) -> None:
        record = build_finalization(finalization_input("release"))
        with tempfile.TemporaryDirectory(prefix="gkd-finalization-contract-") as temporary:
            path = Path(temporary) / "record.json"
            path.write_bytes(canonical_bytes(record))
            command = [sys.executable, "canonical/payload/bin/gkd-finalize", "validate", "--record", str(path)]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, result.returncode, result.stderr.decode())
            self.assertEqual("valid", json.loads(result.stdout)["status"])
            help_result = subprocess.run([sys.executable, "canonical/payload/bin/gkd-finalize", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(0, help_result.returncode, help_result.stderr.decode())
            self.assertNotIn(b"publish", help_result.stdout)
            self.assertNotIn(b"release", help_result.stdout.lower().replace(b"promotion-plan", b""))


if __name__ == "__main__":
    unittest.main()
