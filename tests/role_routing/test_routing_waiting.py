from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from gkd_role.routing import GATES, decide_route, m2a_route_evidence
from gkd_role.waiting import new_wait_state, transition, validate_wait_state
from gkd_task.errors import TaskError

from tests.role_routing.helpers import bundle_digest


class RoutingContracts(unittest.TestCase):
    def request(self, route=None, **overrides):
        gates = {name: True for name in GATES}
        gates.update(overrides)
        return {"schemaVersion": 1, "requestedRoute": route, "bundleDigest": bundle_digest(), "gates": gates}

    def test_manual_is_default_and_does_not_claim_automatic_readiness(self) -> None:
        result = decide_route(self.request())
        self.assertEqual("manual", result["outcome"])
        self.assertIsNone(result["selectedRole"])
        self.assertFalse(result["fallbackAttempted"])

    def test_explicit_automatic_selects_only_gkd_executor_when_every_gate_is_true(self) -> None:
        result = decide_route(self.request("automatic"))
        self.assertEqual("automatic", result["outcome"])
        self.assertEqual("gkd_executor", result["selectedRole"])

    def test_each_missing_automatic_gate_returns_one_stable_manual_only_refusal(self) -> None:
        for gate in GATES:
            with self.subTest(gate=gate):
                result = decide_route(self.request("automatic", **{gate: False}))
                self.assertEqual("manual_only", result["outcome"])
                self.assertEqual("AUTOMATIC_ROUTE_GATES_INCOMPLETE", result["refusal"]["code"])
                self.assertEqual([gate], result["refusal"]["failedGates"])
                self.assertFalse(result["fallbackAttempted"])

    def test_m2a_evidence_is_forced_manual_only_until_m2b(self) -> None:
        result = m2a_route_evidence(bundle_digest())
        self.assertEqual("manual_only", result["outcome"])
        self.assertEqual(["waitGateReady"], result["refusal"]["failedGates"])

    def test_unknown_or_incomplete_route_input_fails_closed(self) -> None:
        request = self.request("automatic")
        request["unknown"] = True
        with self.assertRaisesRegex(TaskError, "INVALID_ROUTE_REQUEST"):
            decide_route(request)
        request = self.request("automatic")
        del request["gates"]["waitGateReady"]
        with self.assertRaisesRegex(TaskError, "INVALID_ROUTE_REQUEST"):
            decide_route(request)


class WaitingContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.started = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.identity = {"taskId": "TASK-1", "repository": "example.test/team/repo", "head": "a" * 40, "claimId": "b" * 64, "agentId": "agent-one", "sessionDigest": "c" * 64, "bundleDigest": bundle_digest()}
        self.state = new_wait_state(self.identity, "2026-01-01T00:00:00Z")

    def observation(self, kind: str, hour: int, timeout=3_600_000, identity=None):
        return {"schemaVersion": 1, "kind": kind, "observedAt": (self.started + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"), "timeoutMs": timeout, "identity": self.identity if identity is None else identity}

    def test_healthy_intervals_one_through_eleven_only_allow_immediate_silent_rewait(self) -> None:
        state = self.state
        for hour in range(1, 12):
            result = transition(state, self.observation("healthy_timeout", hour))
            self.assertEqual("wait_again", result["outcome"])
            self.assertEqual(3_600_000, result["waitTimeoutMs"])
            self.assertFalse(result["voluntaryOutputAllowed"])
            self.assertFalse(result["inspectionAllowed"])
            self.assertTrue(result["sameAgentRequired"])
            state = result["state"]

    def test_twelfth_elapsed_hour_emits_one_bound_interrupt_and_timeout(self) -> None:
        state = self.state
        for hour in range(1, 12):
            state = transition(state, self.observation("healthy_timeout", hour))["state"]
        result = transition(state, self.observation("healthy_timeout", 12))
        self.assertEqual("deadline_timeout", result["outcome"])
        self.assertEqual({"agentId": "agent-one", "once": True}, result["interrupt"])
        self.assertTrue(result["state"]["interruptIssued"])
        with self.assertRaisesRegex(TaskError, "WAIT_ALREADY_TERMINAL"):
            transition(result["state"], self.observation("healthy_timeout", 13))

    def test_first_or_delayed_observation_at_deadline_can_only_timeout(self) -> None:
        first = transition(self.state, self.observation("healthy_timeout", 13))
        self.assertEqual("deadline_timeout", first["outcome"])
        self.assertEqual(12, first["state"]["completedIntervals"])
        self.assertTrue(first["state"]["interruptIssued"])
        with self.assertRaisesRegex(TaskError, "WAIT_ALREADY_TERMINAL"):
            transition(first["state"], self.observation("healthy_timeout", 13))

        state = transition(self.state, self.observation("healthy_timeout", 1))["state"]
        delayed = transition(state, self.observation("healthy_timeout", 13))
        self.assertEqual("deadline_timeout", delayed["outcome"])
        self.assertEqual({"agentId": "agent-one", "once": True}, delayed["interrupt"])

    def test_child_terminal_error_and_user_intervention_return_immediately(self) -> None:
        for kind, outcome in (("executor_terminal", "executor_terminal"), ("executor_error", "executor_error"), ("user_intervention", "executor_terminal")):
            with self.subTest(kind=kind):
                result = transition(self.state, self.observation(kind, 0, timeout=None))
                self.assertEqual(outcome, result["outcome"])
                self.assertIsNone(result["waitTimeoutMs"])

    def test_task_head_agent_or_bundle_drift_fails_closed(self) -> None:
        for field, value in (("taskId", "OTHER"), ("head", "d" * 40), ("agentId", "agent-two"), ("bundleDigest", "e" * 64)):
            drifted = dict(self.identity); drifted[field] = value
            with self.subTest(field=field):
                self.assertEqual("fail_closed_drift", transition(self.state, self.observation("healthy_timeout", 1, identity=drifted))["outcome"])

    def test_short_wait_and_early_timeout_are_rejected_not_rounded_up(self) -> None:
        with self.assertRaisesRegex(TaskError, "WAIT_TIMEOUT_PARAMETER_MISMATCH"):
            transition(self.state, self.observation("healthy_timeout", 1, timeout=360_000))
        with self.assertRaisesRegex(TaskError, "WAIT_INTERVAL_NOT_ELAPSED"):
            transition(self.state, {**self.observation("healthy_timeout", 1), "observedAt": "2026-01-01T00:59:59Z"})
        state = transition(self.state, self.observation("healthy_timeout", 1))["state"]
        with self.assertRaisesRegex(TaskError, "WAIT_INTERVAL_NOT_ELAPSED"):
            transition(state, self.observation("healthy_timeout", 1))

    def test_wait_state_unknown_fields_and_digest_tampering_fail_closed(self) -> None:
        mutated = deepcopy(self.state); mutated["unknown"] = True
        with self.assertRaisesRegex(TaskError, "INVALID_WAIT_STATE"):
            validate_wait_state(mutated)

    def test_host_acknowledgement_wait_uses_task_name_handle_not_agent_identity(self) -> None:
        identity = {
            "taskId": "TASK-1",
            "repository": "example.test/team/repo",
            "head": "a" * 40,
            "claimId": "b" * 64,
            "executorTaskName": "gkd_executor_task_abc",
            "executorAttemptDigest": "c" * 64,
            "bundleDigest": bundle_digest(),
        }
        state = new_wait_state(identity, "2026-01-01T00:00:00Z")
        self.assertEqual(2, state["schemaVersion"])
        self.assertNotIn("agentId", state)
        self.assertNotIn("sessionDigest", state)
        for hour in range(1, 12):
            observation = {"schemaVersion": 1, "kind": "healthy_timeout", "observedAt": (self.started + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"), "timeoutMs": 3_600_000, "identity": identity}
            state = transition(state, observation)["state"]
        terminal = transition(state, {"schemaVersion": 1, "kind": "healthy_timeout", "observedAt": "2026-01-01T12:00:00Z", "timeoutMs": 3_600_000, "identity": identity})
        self.assertEqual({"executorTaskName": "gkd_executor_task_abc", "once": True}, terminal["interrupt"])
        mutated = deepcopy(self.state); mutated["completedIntervals"] = 1
        with self.assertRaisesRegex(TaskError, "INVALID_WAIT_STATE"):
            validate_wait_state(mutated)


if __name__ == "__main__":
    unittest.main()
