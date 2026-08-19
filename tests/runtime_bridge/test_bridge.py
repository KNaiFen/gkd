from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest

from gkd_role.bridge import validate_spawn_result
from gkd_role.roles import role_catalog
from gkd_role.routing import validate_route_decision
from gkd_task.canonical import digest_object
from gkd_task.errors import TaskError
from gkd_task.model import finalize_state, validate_offer, validate_state
from gkd_task.runtime import RuntimeStore, validate_envelope
from gkd_task.service import TaskService
from tests.runtime_bridge.helpers import BUNDLE_ROOT, automatic_decision, bundle_digest, ready_bridge, spawn_result
from tests.task_core.helpers import FUTURE_TIME, TaskRepo


class AutomaticBridgeContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

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
        delivery = self.repo.state()["lifecycle"]["delivery"]
        self.assertEqual(prepared["executionBundleDigest"], delivery["executionBundleDigest"])
        self.assertEqual(candidate_output, delivery["candidateOutputBundleDigest"])
        self.assertEqual(prepared["routeDecisionDigest"], delivery["routeDecisionDigest"])
        tampered = deepcopy(self.repo.state())
        tampered["lifecycle"]["delivery"]["executionBundleDigest"] = "e" * 64
        with self.assertRaises(TaskError) as raised:
            validate_state(finalize_state(tampered))
        self.assertEqual("INVALID_TASK_STATE", raised.exception.code)

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

    def test_replay_stale_cas_and_execution_bundle_replacement_fail_closed(self) -> None:
        bridge, prepared = ready_bridge(self.repo)
        facts = spawn_result(prepared)
        with self.assertRaises(TaskError) as raised:
            bridge.claim("0" * 40, self.repo.state()["revision"], prepared["envelopeId"], facts, "activation-nonce")
        self.assertEqual("CAS_HEAD_MISMATCH", raised.exception.code)
        claimed = bridge.claim(*self.repo.cas(), prepared["envelopeId"], facts, "activation-nonce")
        with self.assertRaises(TaskError):
            bridge.claim(*self.repo.cas(), prepared["envelopeId"], facts, "activation-nonce")
        self.assertEqual(claimed["claimId"], self.repo.state()["lifecycle"]["claim"]["claimId"])

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
