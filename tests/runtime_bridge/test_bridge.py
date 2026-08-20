from __future__ import annotations

import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from gkd_role.bridge import validate_spawn_result
from gkd_role.roles import role_catalog
from gkd_role.routing import validate_route_decision
from gkd_task.acceptance import _validate_fixed_candidate
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.model import finalize_state, validate_offer, validate_state
from gkd_task.runtime import RuntimeStore, validate_envelope
from gkd_task.service import TaskService
from tests.runtime_bridge.helpers import BUNDLE_ROOT, SOURCE_ROOT, automatic_decision, bundle_digest, ready_bridge, spawn_result
from tests.task_core.helpers import FUTURE_TIME, TaskRepo


class AutomaticBridgeContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def _runtime_snapshot(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
            for path in self.repo.runtime_root.rglob("*")
            if path.is_file()
        }

    def _copied_bundle_bridge(self):
        source = self.repo.root / "execution-source"
        shutil.copytree(SOURCE_ROOT, source)
        bridge, prepared = ready_bridge(self.repo, source / "payload")
        return bridge, prepared, source / "payload"

    def _delivered_candidate(self):
        bridge, prepared = ready_bridge(self.repo)
        claimed = bridge.claim(
            *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "acceptance-activation"
        )
        runtime = RuntimeStore(self.repo.runtime_root)
        delivered = TaskService(
            self.repo.candidate, self.repo.task_path, runtime
        ).deliver(*self.repo.cas(), claimed["claimId"], "d" * 64)
        claim = self.repo.state()["lifecycle"]["claim"]
        return prepared, claim, runtime, delivered

    def test_route_offer_activation_claim_and_delivery_bind_both_bundle_identities(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        self.assertEqual("automatic_spawn_ready", prepared["status"])
        self.assertEqual("gkd_executor", prepared["spawnRequest"]["agentType"])
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "activation-nonce")
        self.assertEqual("implementing", claimed["status"])
        state = self.repo.state()
        claim = state["lifecycle"]["claim"]
        self.assertEqual(prepared["executionBundleDigest"], claim["executionBundleDigest"])
        self.assertEqual(prepared["routeDecisionDigest"], claim["routeDecisionDigest"])
        candidate_output = "d" * 64
        service = TaskService(self.repo.candidate, self.repo.task_path, RuntimeStore(self.repo.runtime_root))
        delivered = service.deliver(*self.repo.cas(), claimed["claimId"], candidate_output)
        self.assertEqual("delivered", delivered["status"])
        runtime = RuntimeStore(self.repo.runtime_root)
        _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], runtime)
        delivery = self.repo.state()["lifecycle"]["delivery"]
        self.assertEqual(prepared["executionBundleDigest"], delivery["executionBundleDigest"])
        self.assertEqual(candidate_output, delivery["candidateOutputBundleDigest"])
        self.assertEqual(prepared["routeDecisionDigest"], delivery["routeDecisionDigest"])
        tampered = deepcopy(self.repo.state())
        tampered["lifecycle"]["delivery"]["executionBundleDigest"] = "e" * 64
        with self.assertRaises(TaskError) as raised:
            validate_state(finalize_state(tampered))
        self.assertEqual("INVALID_TASK_STATE", raised.exception.code)
        runtime.delete_activation(claim["activationId"])
        with self.assertRaises(TaskError) as raised:
            _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], runtime)
        self.assertEqual("CLAIM_RECEIPT_UNAVAILABLE", raised.exception.code)

    def test_automatic_offer_requires_exact_persisted_decision_and_six_gates(self) -> None:
        service = self.repo.ready_and_authorized()
        catalog = role_catalog(BUNDLE_ROOT, bundle_digest())
        role = next(item for item in catalog["roles"] if item["name"] == "gkd_executor")
        with self.assertRaises(TaskError) as raised:
            service.offer(*self.repo.cas(), "automatic", role["roleDigest"], role["configDigest"], FUTURE_TIME, "gkd_executor", bundle_digest())
        self.assertEqual("AUTOMATIC_ROUTE_DECISION_REQUIRED", raised.exception.code)
        decision = automatic_decision()
        extra_gate = deepcopy(decision)
        extra_gate["gates"]["unexpectedGate"] = True
        extra_gate["decisionDigest"] = digest_object(
            {key: value for key, value in extra_gate.items() if key != "decisionDigest"}
        )
        with self.assertRaises(TaskError):
            validate_route_decision(extra_gate, require_automatic=True)
        for gate in decision["gates"]:
            request = {
                "schemaVersion": 1,
                "requestedRoute": "automatic",
                "bundleDigest": bundle_digest(),
                "gates": {**decision["gates"], gate: False},
            }
            rejected = __import__("gkd_role.routing", fromlist=["decide_route"]).decide_route(request)
            self.assertEqual("manual_only", rejected["outcome"])
            with self.assertRaises(TaskError):
                validate_route_decision(rejected, require_automatic=True)
        service.offer(
            *self.repo.cas(), "automatic", role["roleDigest"], role["configDigest"],
            FUTURE_TIME, "gkd_executor", bundle_digest(), decision,
        )
        handoff = service.handoff()
        envelope = RuntimeStore(self.repo.runtime_root).read_envelope(handoff["envelopeId"])
        envelope["routeGates"]["unexpectedGate"] = True
        envelope["envelopeDigest"] = digest_object(
            {key: value for key, value in envelope.items() if key != "envelopeDigest"}
        )
        with self.assertRaises(TaskError) as raised:
            validate_envelope(envelope)
        self.assertEqual("INVALID_LAUNCH_ENVELOPE", raised.exception.code)

    def test_fixed_head_acceptance_requires_automatic_activation_receipt(self) -> None:
        _, claim, runtime, delivered = self._delivered_candidate()
        runtime.delete_claim_activation_receipt(claim["claimId"])
        with self.assertRaises(TaskError) as raised:
            _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], runtime)
        self.assertEqual("ACTIVATION_RECEIPT_UNAVAILABLE", raised.exception.code)

    def test_fixed_head_acceptance_rejects_receipt_claim_mismatch(self) -> None:
        _, claim, runtime, delivered = self._delivered_candidate()
        receipt = runtime.read_claim_activation_receipt(claim["claimId"])
        receipt["claimId"] = "e" * 64
        receipt["receiptDigest"] = digest_object(
            {key: value for key, value in receipt.items() if key != "receiptDigest"}
        )
        atomic_write(
            runtime._path("claim-activation-receipts", claim["claimId"]),
            canonical_bytes(receipt),
            mode=0o600,
        )
        with self.assertRaises(TaskError) as raised:
            _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], runtime)
        self.assertEqual("INVALID_ACTIVATION_RECEIPT", raised.exception.code)

    def test_fixed_head_acceptance_rejects_activation_route_decision_mismatch(self) -> None:
        prepared, claim, runtime, delivered = self._delivered_candidate()
        self.assertEqual(prepared["routeDecisionDigest"], claim["routeDecisionDigest"])
        claim_receipt = runtime.read_claim_receipt(claim["claimId"])
        journal = runtime.read_journal(claim_receipt["transactionId"])
        activation = runtime.read_activation(claim["activationId"])
        activation["routeDecisionDigest"] = "e" * 64
        activation["activationDigest"] = digest_object(
            {key: value for key, value in activation.items() if key != "activationDigest"}
        )
        atomic_write(
            runtime._path("activations", claim["activationId"]),
            canonical_bytes(activation),
            mode=0o600,
        )
        journal["runtimeFiles"][0]["postimage"] = base64.b64encode(
            canonical_bytes(activation)
        ).decode("ascii")
        journal["journalDigest"] = digest_object(
            {key: value for key, value in journal.items() if key != "journalDigest"}
        )
        atomic_write(
            runtime.journal_path(journal["transactionId"]),
            canonical_bytes(journal),
            mode=0o600,
        )
        claim_receipt["transactionDigest"] = journal["journalDigest"]
        claim_receipt["receiptDigest"] = digest_object(
            {key: value for key, value in claim_receipt.items() if key != "receiptDigest"}
        )
        runtime.write_claim_receipt(claim["claimId"], claim_receipt)
        activation_receipt = runtime.read_claim_activation_receipt(claim["claimId"])
        activation_receipt["activationDigest"] = activation["activationDigest"]
        activation_receipt["claimReceiptDigest"] = claim_receipt["receiptDigest"]
        activation_receipt["receiptDigest"] = digest_object(
            {key: value for key, value in activation_receipt.items() if key != "receiptDigest"}
        )
        runtime.write_activation_receipt(activation_receipt)
        with self.assertRaises(TaskError) as raised:
            _validate_fixed_candidate(self.repo.candidate, self.repo.task_path, delivered["head"], runtime)
        self.assertEqual("INVALID_ACTIVATION_RECEIPT", raised.exception.code)

    def test_legacy_role_bound_offer_and_envelope_cannot_select_automatic(self) -> None:
        service = self.repo.ready_and_authorized()
        catalog = role_catalog(BUNDLE_ROOT, bundle_digest())
        role = next(item for item in catalog["roles"] if item["name"] == "gkd_executor")
        service.offer(
            *self.repo.cas(), "manual", role["roleDigest"], role["configDigest"],
            FUTURE_TIME, "gkd_executor", bundle_digest(),
        )
        offer = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))
        offer["route"] = "automatic"
        with self.assertRaises(TaskError) as raised:
            validate_offer(offer)
        self.assertEqual("INVALID_OFFER", raised.exception.code)
        handoff = service.handoff()
        envelope = RuntimeStore(self.repo.runtime_root).read_envelope(handoff["envelopeId"])
        envelope["route"] = "automatic"
        envelope["envelopeDigest"] = digest_object(
            {key: value for key, value in envelope.items() if key != "envelopeDigest"}
        )
        with self.assertRaises(TaskError) as raised:
            validate_envelope(envelope)
        self.assertEqual("INVALID_LAUNCH_ENVELOPE", raised.exception.code)

    def test_spawn_mismatch_matrix_is_write_free(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        tracked_before = (self.repo.task_root / "task.json").read_bytes()
        runtime_before = sorted(path.relative_to(self.repo.runtime_root).as_posix() for path in self.repo.runtime_root.rglob("*") if path.is_file())
        mutations = {
            "missing": {key: value for key, value in spawn_result(prepared).items() if key != "agentId"},
            "duplicate": spawn_result(prepared, spawnCount=2),
            "task": spawn_result(prepared, taskName="other_task"),
            "role": spawn_result(prepared, agentType="worker"),
            "fork": spawn_result(prepared, forkTurns="all"),
            "fallback": spawn_result(prepared, fallbackAttempted=True),
            "bundle": spawn_result(prepared, executionBundleDigest="e" * 64),
            "decision": spawn_result(prepared, routeDecisionDigest="e" * 64),
            "identity": spawn_result(prepared, threadDigest="not-a-digest"),
        }
        for name, facts in mutations.items():
            with self.subTest(name=name), self.assertRaises(TaskError):
                bridge.claim(*self.repo.cas(), prepared["envelopeId"], facts, "activation-nonce")
            self.assertEqual(tracked_before, (self.repo.task_root / "task.json").read_bytes())
            self.assertEqual(runtime_before, sorted(path.relative_to(self.repo.runtime_root).as_posix() for path in self.repo.runtime_root.rglob("*") if path.is_file()))

    def test_replay_and_stale_cas_fail_closed(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        facts = spawn_result(prepared)
        with self.assertRaises(TaskError) as raised:
            bridge.claim("0" * 40, self.repo.state()["revision"], prepared["envelopeId"], facts, "activation-nonce")
        self.assertEqual("CAS_HEAD_MISMATCH", raised.exception.code)
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], facts, "activation-nonce")
        with self.assertRaises(TaskError):
            bridge.claim(*self.repo.cas(), prepared["envelopeId"], facts, "activation-nonce")
        self.assertEqual(claimed["claimId"], self.repo.state()["lifecycle"]["claim"]["claimId"])

    def test_claim_revalidates_execution_bundle_after_prepare(self) -> None:
        bridge, prepared, copied_bundle = self._copied_bundle_bridge()
        tracked_before = (self.repo.task_root / "task.json").read_bytes()
        runtime_before = self._runtime_snapshot()
        shutil.rmtree(copied_bundle)

        with self.assertRaises(TaskError) as raised:
            bridge.claim(
                *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "missing-bundle"
            )
        self.assertEqual("BUNDLE_CONTENT_MISMATCH", raised.exception.code)
        self.assertEqual(tracked_before, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(runtime_before, self._runtime_snapshot())

    def test_recover_revalidates_replaced_bundle_and_remains_retryable(self) -> None:
        bridge, prepared, copied_bundle = self._copied_bundle_bridge()

        def interrupt(phase: str) -> None:
            if phase == "committed":
                raise RuntimeError("synthetic committed transaction interruption")

        bridge.failure_hook = interrupt
        with self.assertRaises(RuntimeError):
            bridge.claim(
                *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "replaced-bundle"
            )
        bridge.failure_hook = None
        tracked_before = (self.repo.task_root / "task.json").read_bytes()
        runtime_before = self._runtime_snapshot()

        shutil.rmtree(copied_bundle)
        shutil.copytree(BUNDLE_ROOT, copied_bundle)
        skill = copied_bundle / "skills" / "gkd-execute" / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"replaced\n")
        with self.assertRaises(TaskError) as raised:
            bridge.recover()
        self.assertEqual("BUNDLE_CONTENT_MISMATCH", raised.exception.code)
        self.assertEqual(tracked_before, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(runtime_before, self._runtime_snapshot())

        shutil.rmtree(copied_bundle)
        shutil.copytree(BUNDLE_ROOT, copied_bundle)
        recovered = bridge.recover()
        self.assertEqual("activation_consumption_recovered", recovered["status"])
        self.assertEqual([], list((self.repo.runtime_root / "active-transactions").glob("*.json")))
        for directory in ("activations", "activation-receipts", "claim-activation-receipts", "claim-receipts"):
            self.assertEqual(1, len(list((self.repo.runtime_root / directory).glob("*.json"))))

    def test_committed_claim_receipt_interruption_recovers_without_replay(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        original = bridge.runtime.write_claim_receipt
        calls = 0

        def fail_once(claim_id, value):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("synthetic receipt interruption")
            return original(claim_id, value)

        bridge.runtime.write_claim_receipt = fail_once
        with self.assertRaises(OSError):
            bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "activation-nonce")
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])
        bridge.runtime.write_claim_receipt = original
        recovered = bridge.recover()
        self.assertEqual("activation_consumption_recovered", recovered["status"])
        self.assertEqual(self.repo.state()["lifecycle"]["claim"]["claimId"], recovered["claimId"])

    def test_activation_receipt_interruption_recovers_without_second_claim(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        original = bridge.runtime.write_activation_receipt
        calls = 0

        def fail_once(value):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("synthetic activation receipt interruption")
            return original(value)

        bridge.runtime.write_activation_receipt = fail_once
        with self.assertRaises(OSError):
            bridge.claim(*self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "activation-nonce")
        claim_id = self.repo.state()["lifecycle"]["claim"]["claimId"]
        bridge.runtime.write_activation_receipt = original
        recovered = bridge.recover()
        self.assertEqual("activation_consumption_recovered", recovered["status"])
        self.assertEqual(claim_id, recovered["claimId"])

    def test_interrupted_activation_transaction_rolls_back_without_residue(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        before = (self.repo.task_root / "task.json").read_bytes()

        def interrupt(phase: str) -> None:
            if phase == "runtime_written":
                raise RuntimeError("synthetic activation transaction interruption")

        bridge.failure_hook = interrupt
        with self.assertRaises(RuntimeError):
            bridge.claim(
                *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "interrupted-activation"
            )
        self.assertEqual(1, len(list((self.repo.runtime_root / "activations").glob("*.json"))))
        self.assertEqual(1, len(list((self.repo.runtime_root / "active-transactions").glob("*.json"))))
        self.assertEqual(before, (self.repo.task_root / "task.json").read_bytes())
        bridge.failure_hook = None
        recovered = bridge.recover()
        self.assertEqual("recovered_rolled_back", recovered["status"])
        self.assertEqual([], list((self.repo.runtime_root / "activations").glob("*.json")))
        self.assertEqual([], list((self.repo.runtime_root / "active-transactions").glob("*.json")))
        self.assertEqual([], list((self.repo.runtime_root / "activation-receipts").glob("*.json")))
        self.assertEqual([], list((self.repo.runtime_root / "claim-activation-receipts").glob("*.json")))
        self.assertEqual(before, (self.repo.task_root / "task.json").read_bytes())

    def test_committed_activation_transaction_recovery_finishes_receipts(self) -> None:
        bridge, prepared = ready_bridge(self.repo)

        def interrupt(phase: str) -> None:
            if phase == "committed":
                raise RuntimeError("synthetic committed transaction interruption")

        bridge.failure_hook = interrupt
        with self.assertRaises(RuntimeError):
            bridge.claim(
                *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "committed-activation"
            )
        claim_id = self.repo.state()["lifecycle"]["claim"]["claimId"]
        self.assertEqual(1, len(list((self.repo.runtime_root / "active-transactions").glob("*.json"))))
        bridge.failure_hook = None
        recovered = bridge.recover()
        self.assertEqual("activation_consumption_recovered", recovered["status"])
        self.assertEqual(claim_id, recovered["claimId"])
        self.assertEqual([], list((self.repo.runtime_root / "active-transactions").glob("*.json")))
        for directory in ("activations", "activation-receipts", "claim-activation-receipts", "claim-receipts"):
            self.assertEqual(1, len(list((self.repo.runtime_root / directory).glob("*.json"))))

    def test_concurrent_automatic_claim_has_one_activation_and_no_orphan(self) -> None:
        _, prepared = ready_bridge(self.repo)
        expected_head, expected_revision = self.repo.cas()
        spawn_path = self.repo.root / "spawn-result.json"
        marker = self.repo.root / "claim-start"
        spawn_path.write_bytes(canonical_bytes(spawn_result(prepared)))
        worker = Path("tests/runtime_bridge/automatic_claim_worker.py").resolve()
        base_command = [
            sys.executable,
            str(worker),
            "--candidate-root", str(self.repo.candidate),
            "--task-path", self.repo.task_path,
            "--runtime-root", str(self.repo.runtime_root),
            "--bundle-root", str(BUNDLE_ROOT.resolve()),
            "--bundle-digest", bundle_digest(),
            "--expected-head", expected_head,
            "--expected-revision", str(expected_revision),
            "--envelope-id", str(prepared["envelopeId"]),
            "--spawn-result", str(spawn_path),
            "--start-marker", str(marker),
        ]
        environment = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.environ.get("PYTHONPATH", f"{Path('canonical/payload/lib').resolve()}:{Path.cwd()}"),
        }
        processes = [
            subprocess.Popen(
                [*base_command, "--activation-nonce", nonce],
                cwd=Path.cwd(),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for nonce in ("concurrent-activation-a", "concurrent-activation-b")
        ]
        marker.touch()
        results = [(process.returncode, stdout, stderr) for process in processes for stdout, stderr in [process.communicate(timeout=30)]]
        self.assertEqual([0, 2], sorted(result[0] for result in results))
        loser = next(result for result in results if result[0] != 0)
        self.assertIn(json.loads(loser[2])["error"], {"HEAD_MISMATCH", "CAS_HEAD_MISMATCH"})
        for directory in ("activations", "activation-receipts", "claim-activation-receipts", "claim-receipts"):
            self.assertEqual(1, len(list((self.repo.runtime_root / directory).glob("*.json"))))
        self.assertEqual([], list((self.repo.runtime_root / "active-transactions").glob("*.json")))
        self.assertEqual([], list((self.repo.runtime_root / "transaction-doubt").glob("*.json")))
        automatic_journals = [
            json.loads(path.read_bytes())
            for path in (self.repo.runtime_root / "transactions").glob("*.json")
            if "runtimeFiles" in json.loads(path.read_bytes())
        ]
        self.assertEqual(1, len(automatic_journals))
        self.assertEqual("committed", automatic_journals[0]["status"])
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])

    def test_candidate_public_claim_stays_fail_closed_and_byte_unchanged(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        before = (self.repo.task_root / "task.json").read_bytes()
        runtime_before = {
            path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
            for path in self.repo.runtime_root.rglob("*")
            if path.is_file()
        }
        command = [
            str(Path("canonical/payload/bin/gkd-task").resolve()),
            "claim",
            "--candidate-root", str(self.repo.candidate),
            "--task-path", self.repo.task_path,
            "--runtime-root", str(self.repo.runtime_root),
            "--expected-head", self.repo.head(),
            "--expected-revision", str(self.repo.state()["revision"]),
            "--envelope-id", str(prepared["envelopeId"]),
        ]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE", json.loads(result.stderr)["error"])
        self.assertEqual(before, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(
            runtime_before,
            {
                path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
                for path in self.repo.runtime_root.rglob("*")
                if path.is_file()
            },
        )

    def test_public_role_automatic_claim_rejects_forged_spawn_without_writes(self) -> None:
        _, prepared = ready_bridge(self.repo)
        spawn_path = self.repo.root / "forged-spawn.json"
        spawn_path.write_bytes(canonical_bytes(spawn_result(prepared)))
        task_before = (self.repo.task_root / "task.json").read_bytes()
        runtime_before = {
            path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
            for path in self.repo.runtime_root.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [
                str(Path("canonical/payload/bin/gkd-role").resolve()),
                "automatic-claim",
                "--candidate-root", str(self.repo.candidate),
                "--task-path", self.repo.task_path,
                "--runtime-root", str(self.repo.runtime_root),
                "--bundle-root", str(BUNDLE_ROOT.resolve()),
                "--execution-bundle-digest", bundle_digest(),
                "--spawn-result", str(spawn_path),
                "--expected-head", self.repo.head(),
                "--expected-revision", str(self.repo.state()["revision"]),
                "--envelope-id", str(prepared["envelopeId"]),
                "--activation-nonce", "forged-activation",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE", json.loads(result.stderr)["error"])
        self.assertEqual(task_before, (self.repo.task_root / "task.json").read_bytes())
        self.assertEqual(
            runtime_before,
            {
                path.relative_to(self.repo.runtime_root).as_posix(): path.read_bytes()
                for path in self.repo.runtime_root.rglob("*")
                if path.is_file()
            },
        )

    def test_main_outputs_are_path_minimized_and_identity_free(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        claimed = bridge.claim(
            *self.repo.cas(), prepared["envelopeId"], spawn_result(prepared), "activation-nonce"
        )
        encoded = json.dumps({"prepared": prepared, "claimed": claimed}, sort_keys=True)
        for forbidden in (str(self.repo.root), "capability", "agentId", "threadDigest", "prompt", "transcript"):
            self.assertNotIn(forbidden, encoded)
        validate_spawn_result(spawn_result(prepared), prepared)


if __name__ == "__main__":
    unittest.main()
