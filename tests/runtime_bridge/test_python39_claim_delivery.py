from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from gkd_task.canonical import digest_object
from gkd_task.runtime import RuntimeStore

from tests.runtime_bridge.helpers import ready_bridge, spawn_result
from tests.task_core.helpers import TaskRepo


class Python39ClaimDeliveryContracts(unittest.TestCase):
    """Exercise the real bridge receipt boundary through the installed CLI."""

    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _deliver(self, claim_id: str, candidate_output: str, document_path: str, document_digest: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            "-B",
            str(Path("canonical/payload/bin/gkd-task").resolve()),
            "deliver",
            "--candidate-root", str(self.repo.candidate),
            "--task-path", self.repo.task_path,
            "--runtime-root", str(self.repo.runtime_root),
            "--expected-head", self.repo.head(),
            "--expected-revision", str(self.repo.state()["revision"]),
            "--claim-id", claim_id,
            "--candidate-output-bundle-digest", candidate_output,
            "--delivery-document-path", document_path,
            "--delivery-document-digest", document_digest,
        ]
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = os.pathsep.join(
            str(path.resolve()) for path in (Path("canonical/payload/lib"), Path("."))
        )
        return subprocess.run(
            command,
            cwd=Path.cwd(),
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_fresh_trusted_bridge_claim_delivers_through_cli(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        claimed = bridge.claim(
            *self.repo.cas(),
            prepared["envelopeId"],
            spawn_result(prepared),
            "python39-cli-delivery",
        )
        document_path, document_digest = self.repo.prepare_delivery_document()
        result = self._deliver(claimed["claimId"], "d" * 64, document_path, document_digest)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("delivered", json.loads(result.stdout)["status"])
        self.assertEqual("delivered", self.repo.state()["lifecycle"]["phase"])

    def test_claim_receipt_drift_blocks_cli_delivery_without_final_state(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        claimed = bridge.claim(
            *self.repo.cas(),
            prepared["envelopeId"],
            spawn_result(prepared),
            "python39-cli-receipt-drift",
        )
        runtime = RuntimeStore(self.repo.runtime_root)
        receipt = runtime.read_claim_receipt(claimed["claimId"])
        receipt["claimCommit"] = "0" * 40
        receipt["receiptDigest"] = digest_object(
            {key: value for key, value in receipt.items() if key != "receiptDigest"}
        )
        runtime.write_claim_receipt(claimed["claimId"], receipt)

        document_path, document_digest = self.repo.prepare_delivery_document()
        expected_revision = self.repo.state()["revision"]
        result = self._deliver(claimed["claimId"], "d" * 64, document_path, document_digest)

        self.assertEqual(2, result.returncode)
        self.assertEqual("CLAIM_RECEIPT_UNAVAILABLE", json.loads(result.stderr)["error"])
        state = self.repo.state()
        self.assertEqual("implementing", state["lifecycle"]["phase"])
        self.assertEqual(expected_revision, state["revision"])
        self.assertIsNone(state["lifecycle"]["delivery"])
