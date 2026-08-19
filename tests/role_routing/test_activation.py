from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import os
import subprocess
import sys
import unittest
from unittest import mock

from gkd_role.roles import role_catalog, role_record
from gkd_task.canonical import FixedClock, canonical_bytes
from gkd_task.acceptance import _validate_fixed_candidate
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo

from tests.role_routing.helpers import BUNDLE_ROOT, bundle_digest
from tests.role_routing.activation_support import TestActivationEvidenceProvider, TestActivationTaskService, record_test_activation


class ActivationContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()
        self.bundle = bundle_digest()
        self.catalog = role_catalog(BUNDLE_ROOT, self.bundle)
        self.role = role_record(self.catalog, "gkd_executor")
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", self.role["roleDigest"], self.role["configDigest"], FUTURE_TIME, "gkd_executor", self.bundle)
        self.handoff = service.handoff()
        self.offer = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))
        self.expected = {
            "taskId": self.repo.task_id,
            "repository": self.repo.identity,
            "taskBranch": self.repo.task_branch,
            "offerId": self.offer["offerId"],
            "envelopeId": self.handoff["envelopeId"],
            "route": "manual",
            "roleName": "gkd_executor",
            "roleDigest": self.role["roleDigest"],
        "configDigest": self.role["configDigest"],
        "bundleDigest": self.bundle,
        "offerCreatedAt": self.offer["createdAt"],
        "offerExpiresAt": self.offer["expiresAt"],
        }
        self.observation = {
            "evidenceClass": "host-runtime-event",
            "agentId": "agent-one",
            "threadDigest": "e" * 64,
            "model": self.role["model"],
            "reasoningEffort": self.role["modelReasoningEffort"],
            "sandbox": self.role["sandboxMode"],
            "runtimeSeconds": self.role["runtimeSeconds"],
            "activatedAt": FIXED_TIME,
        }
        self.runtime = RuntimeStore(self.repo.runtime_root)

    def tearDown(self) -> None:
        self.repo.close()

    def record(self, expected=None, observation=None):
        return record_test_activation(self.runtime, self.catalog, expected or self.expected, observation or self.observation, "activation-nonce")

    def provider(self, activation_id, catalog=None):
        return TestActivationEvidenceProvider(self.runtime, activation_id, catalog or self.catalog)

    def claim(self, provider):
        service = TestActivationTaskService(self.repo.candidate, self.repo.task_path, self.runtime, FixedClock(FIXED_TIME), evidence_provider=provider)
        return service.claim(*self.repo.cas(), self.handoff["envelopeId"])

    def test_exact_host_activation_claims_once_and_writes_consumption_receipt(self) -> None:
        activation = self.record()
        claimed = self.claim(self.provider(activation["activationId"]))
        receipt = self.runtime.read_activation_receipt(activation["activationId"])
        self.assertEqual(claimed["claimId"], receipt["claimId"])
        self.assertEqual(claimed["head"], receipt["claimCommit"])

    def test_missing_or_candidate_written_activation_is_not_evidence(self) -> None:
        fake_id = "f" * 64
        (self.repo.root / "candidate-written-activation.json").write_bytes(canonical_bytes({"activationId": fake_id}))
        with self.assertRaisesRegex(TaskError, "ACTIVATION_UNAVAILABLE"):
            self.claim(self.provider(fake_id))

    def test_cross_task_offer_envelope_route_and_bundle_bindings_fail_before_claim_commit(self) -> None:
        for field, value in (("taskId", "OTHER"), ("repository", "example.test/other/repo"), ("taskBranch", "task/other"), ("offerId", "f" * 64), ("envelopeId", "a" * 64), ("route", "automatic")):
            expected = dict(self.expected); expected[field] = value
            activation = self.record(expected=expected)
            commits = self.repo.commits()
            with self.subTest(field=field), self.assertRaisesRegex(TaskError, "RUNTIME_EVIDENCE_MISMATCH"):
                self.claim(self.provider(activation["activationId"]))
            self.assertEqual(commits, self.repo.commits())
        expected = dict(self.expected); expected["bundleDigest"] = "b" * 64
        with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
            self.record(expected=expected)

    def test_role_model_effort_sandbox_runtime_and_digest_drift_are_rejected_at_activation(self) -> None:
        mutations = (
            ("model", "gpt-5.6-terra"),
            ("reasoningEffort", "medium"),
            ("sandbox", "read-only"),
            ("runtimeSeconds", 3600),
        )
        for field, value in mutations:
            observed = dict(self.observation); observed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
                self.record(observation=observed)
        expected = dict(self.expected); expected["roleDigest"] = "f" * 64
        with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
            self.record(expected=expected)

    def test_expired_and_cross_role_activation_bindings_are_rejected(self) -> None:
        observed = dict(self.observation)
        observed["activatedAt"] = "2028-01-02T03:04:05Z"
        with self.assertRaisesRegex(TaskError, "ACTIVATION_OUTSIDE_OFFER_WINDOW"):
            self.record(observation=observed)
        expected = dict(self.expected)
        expected["roleName"] = "gkd_acceptor"
        with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
            self.record(expected=expected)

    def test_self_report_evidence_class_and_unknown_observation_fields_are_rejected(self) -> None:
        observed = dict(self.observation); observed["evidenceClass"] = "agent-self-report"
        with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
            self.record(observation=observed)
        observed = dict(self.observation); observed["claim"] = "ready"
        with self.assertRaisesRegex(TaskError, "INVALID_ACTIVATION_OBSERVATION"):
            self.record(observation=observed)

    def test_provider_catalog_drift_and_replay_are_rejected(self) -> None:
        activation = self.record()
        forged = deepcopy(self.catalog)
        forged["activationProviderDigest"] = "f" * 64
        with self.assertRaisesRegex(TaskError, "INVALID_ROLE_CATALOG"):
            self.claim(self.provider(activation["activationId"], forged))
        claimed = self.claim(self.provider(activation["activationId"]))
        replay = self.provider(activation["activationId"])
        with self.assertRaisesRegex(TaskError, "ACTIVATION_REPLAYED"):
            replay.observe("claim", self.expected)
        self.assertEqual("implementing", claimed["status"])

    def test_late_second_claim_cannot_win_after_exact_activation_is_consumed(self) -> None:
        activation = self.record()
        first = self.provider(activation["activationId"])
        second = self.provider(activation["activationId"])
        self.claim(first)
        with self.assertRaisesRegex(TaskError, "OFFER_CONFLICT|ACTIVATION_REPLAYED|INVALID_LAUNCH_ENVELOPE"):
            self.claim(second)

    def test_activation_receipt_write_failure_recovers_from_committed_claim_receipt(self) -> None:
        activation = self.record()
        provider = self.provider(activation["activationId"])
        service = TestActivationTaskService(self.repo.candidate, self.repo.task_path, self.runtime, FixedClock(FIXED_TIME), evidence_provider=provider)
        with mock.patch.object(self.runtime, "write_activation_receipt", side_effect=TaskError("ACTIVATION_RECEIPT_WRITE_FAILED")):
            with self.assertRaisesRegex(TaskError, "ACTIVATION_RECEIPT_WRITE_FAILED"):
                service.claim(*self.repo.cas(), self.handoff["envelopeId"])
        state = self.repo.state()
        self.assertEqual("implementing", state["lifecycle"]["phase"])
        recovery = TestActivationTaskService(self.repo.candidate, self.repo.task_path, self.runtime, FixedClock(FIXED_TIME), evidence_provider=self.provider(activation["activationId"]))
        result = recovery.recover_activation()
        self.assertEqual("activation_consumption_recovered", result["status"])
        self.assertEqual(state["lifecycle"]["claim"]["claimId"], self.runtime.read_activation_receipt(activation["activationId"])["claimId"])
        delivered = recovery.deliver(*self.repo.cas(), state["lifecycle"]["claim"]["claimId"])
        self.assertEqual("delivered", delivered["status"])

    def test_two_subprocesses_competing_for_one_activation_have_one_winner(self) -> None:
        activation = self.record()
        expected_path = self.repo.root / "activation-expected.json"
        expected_path.write_bytes(canonical_bytes(self.expected))
        command = [
            sys.executable,
            "tests/role_routing/activation_claim_worker.py",
            "--candidate", str(self.repo.candidate),
            "--task-path", self.repo.task_path,
            "--runtime", str(self.repo.runtime_root),
            "--activation", activation["activationId"],
            "--expected", str(expected_path),
            "--bundle-root", str(BUNDLE_ROOT),
            "--envelope", self.handoff["envelopeId"],
        ]
        env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"; env["PYTHONPATH"] = "canonical/payload/lib:."
        first = subprocess.Popen(command, cwd=Path.cwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, cwd=Path.cwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        results = [first.communicate(timeout=20), second.communicate(timeout=20)]
        codes = [first.returncode, second.returncode]
        self.assertEqual(1, codes.count(0), results)
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])

    def test_delivery_and_fixed_candidate_acceptance_require_claim_indexed_activation_receipt(self) -> None:
        activation = self.record()
        claimed = self.claim(self.provider(activation["activationId"]))
        service = TestActivationTaskService(self.repo.candidate, self.repo.task_path, self.runtime, FixedClock(FIXED_TIME))
        delivered = service.deliver(*self.repo.cas(), claimed["claimId"])
        _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], self.runtime)
        self.runtime.delete_claim_activation_receipt(claimed["claimId"])
        with self.assertRaisesRegex(TaskError, "ACTIVATION_RECEIPT_UNAVAILABLE"):
            _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], self.runtime)

    def test_activation_cli_rejects_caller_selected_provider_and_fails_closed(self) -> None:
        provider = self.repo.root / "arbitrary-provider"
        provider.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        provider.chmod(0o755)
        expected_path = self.repo.root / "activation-request.json"
        expected_path.write_bytes(canonical_bytes(self.expected))
        command = [
            str(Path("canonical/payload/bin/gkd-role").resolve()), "activation-record",
            "--runtime-root", str(self.repo.runtime_root), "--expected", str(expected_path), "--nonce", "provider-nonce",
        ]
        env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(command, cwd=Path.cwd(), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("ACTIVATION_PROVIDER_UNAVAILABLE", json.loads(result.stderr)["error"])
        rejected = subprocess.run(command + ["--provider-command", str(provider)], cwd=Path.cwd(), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(2, rejected.returncode)
        self.assertEqual("INVALID_ARGUMENTS", json.loads(rejected.stderr)["error"])
        task_command = [
            str(Path("canonical/payload/bin/gkd-task").resolve()), "claim",
            "--candidate-root", str(self.repo.candidate), "--task-path", self.repo.task_path,
            "--runtime-root", str(self.repo.runtime_root), "--expected-head", self.repo.head(),
            "--expected-revision", str(self.repo.state()["revision"]), "--envelope-id", self.handoff["envelopeId"],
            "--activation-id", "f" * 64,
        ]
        rejected = subprocess.run(task_command, cwd=Path.cwd(), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(2, rejected.returncode)
        self.assertEqual("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE", json.loads(rejected.stderr)["error"])

    def test_executor_equivalent_payload_cannot_import_or_call_activation_writer(self) -> None:
        before_head = self.repo.head()
        before_revision = self.repo.state()["revision"]
        script = """
from gkd_role.activation import record_activation, ActivationEvidenceProvider
from gkd_task.runtime import RuntimeStore
RuntimeStore.write_activation(None, {})
"""
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = "canonical/payload/lib"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ImportError", result.stderr)
        activation_dir = self.repo.runtime_root / "activations"
        self.assertFalse(activation_dir.exists() and any(activation_dir.iterdir()))

        claim = subprocess.run(
            [
                str(Path("canonical/payload/bin/gkd-task").resolve()), "claim",
                "--candidate-root", str(self.repo.candidate), "--task-path", self.repo.task_path,
                "--runtime-root", str(self.repo.runtime_root), "--expected-head", before_head,
                "--expected-revision", str(before_revision), "--envelope-id", self.handoff["envelopeId"],
                "--activation-id", "a" * 64,
            ],
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(2, claim.returncode)
        self.assertEqual("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE", json.loads(claim.stderr)["error"])
        self.assertEqual(before_head, self.repo.head())
        self.assertEqual(before_revision, self.repo.state()["revision"])

        library_script = """
from pathlib import Path
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
runtime = RuntimeStore(Path(__import__("sys").argv[3]))
service = TaskService(Path(__import__("sys").argv[1]), __import__("sys").argv[2], runtime=runtime)
state = service._state()
service.claim(service.status()["head"], state["revision"], __import__("sys").argv[4])
"""
        before_runtime = {
            path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
            for path in self.repo.runtime_root.rglob("*")
            if path.is_file()
        }
        library = subprocess.run(
            [sys.executable, "-c", library_script, str(self.repo.candidate), self.repo.task_path, str(self.repo.runtime_root), self.handoff["envelopeId"]],
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(0, library.returncode)
        self.assertIn("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE", library.stderr)
        self.assertEqual(before_head, self.repo.head())
        self.assertEqual(before_revision, self.repo.state()["revision"])
        after_runtime = {
            path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
            for path in self.repo.runtime_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before_runtime, after_runtime)


if __name__ == "__main__":
    unittest.main()
