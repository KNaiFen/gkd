from __future__ import annotations

import json
import threading
import unittest

from gkd_watchdog.watcher import CancellationToken, WatchService
from gkd_watchdog.jsonrpc import AppServerRemoteError
from gkd_watchdog.constants import CURRENT_RUNTIME_BASELINE

from tests.watchdog.helpers import FakeClock, ScriptedSession, parsed_request


def turn_notification(status: str, *, at_ms: int = 0):
    return (
        at_ms,
        {
            "method": "turn/completed",
            "params": {
                "threadId": "child-thread-1",
                "turn": {
                    "id": "child-turn-1",
                    "status": status,
                    "items": [{"text": "private body"}],
                },
            },
        },
    )


class WatchServiceTests(unittest.TestCase):
    def test_current_removed_steer_fails_closed_before_session_or_control(self) -> None:
        clock = FakeClock()
        request = parsed_request(
            runtimeEvidenceDigest=CURRENT_RUNTIME_BASELINE.schema_digest
        )
        calls = []

        def forbidden_factory(_request, _cancellation):
            calls.append(True)
            raise AssertionError("current removed steer must not start a session")

        result = WatchService(forbidden_factory, clock=clock).watch(request)

        self.assertEqual(result.outcome, "protocol_error")
        self.assertEqual(result.reason, "turn_steer_unsupported")
        self.assertEqual(calls, [])

    def test_twelve_hour_deadline_is_single_and_hourly_ticks_are_silent(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, statuses=["active"] * 20)
        service = WatchService(
            lambda _request, _cancellation: session,
            clock=clock,
            cancel_poll_ms=3_600_000,
        )

        result = service.watch(parsed_request())

        self.assertEqual(result.outcome, "deadline")
        self.assertEqual(result.elapsed_ms, 43_200_000)
        self.assertEqual(result.health_checks, 12)
        methods = [method for method, _ in session.calls]
        self.assertEqual(methods, ["thread/read"] * 24)
        self.assertNotIn("turn/interrupt", methods)
        self.assertNotIn("turn/steer", methods)

    def test_normal_terminal_returns_immediately_without_steer(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, notifications=[turn_notification("completed")])
        result = WatchService(
            lambda _request, _cancellation: session, clock=clock, cancel_poll_ms=3_600_000
        ).watch(parsed_request())

        self.assertEqual(result.outcome, "normal_terminal")
        self.assertEqual(result.elapsed_ms, 0)
        self.assertEqual(
            [method for method, _ in session.calls],
            ["thread/read", "thread/read"],
        )

    def test_stale_active_child_remains_healthy_across_ticks(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, statuses=["active"] * 8)
        request = parsed_request(maxWaitMs=10_000, healthIntervalMs=2_000)
        result = WatchService(
            lambda _request, _cancellation: session, clock=clock, cancel_poll_ms=2_000
        ).watch(request)

        self.assertEqual(result.outcome, "deadline")
        self.assertEqual(result.health_checks, 5)
        self.assertEqual(len(session.calls), 10)
        self.assertTrue(
            all(method == "thread/read" for method, _params in session.calls)
        )

    def test_system_error_interrupts_child_then_steers_bound_parent(self) -> None:
        clock = FakeClock()
        notification = (
            1,
            {
                "method": "thread/status/changed",
                "params": {
                    "threadId": "child-thread-1",
                    "status": {"type": "systemError"},
                },
            },
        )
        session = ScriptedSession(
            clock,
            notifications=[notification, turn_notification("interrupted", at_ms=2)],
        )
        result = WatchService(
            lambda _request, _cancellation: session, clock=clock, cancel_poll_ms=3_600_000
        ).watch(parsed_request())

        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(
            [method for method, _ in session.calls],
            [
                "thread/read",
                "thread/read",
                "thread/read",
                "thread/read",
                "turn/interrupt",
                "thread/read",
                "thread/read",
                "turn/steer",
            ],
        )
        interrupt = session.calls[4][1]
        self.assertEqual(
            interrupt,
            {"threadId": "child-thread-1", "turnId": "child-turn-1"},
        )
        steer = session.calls[7][1]
        self.assertEqual(steer["threadId"], "parent-thread-1")
        self.assertEqual(steer["expectedTurnId"], "parent-turn-1")
        event = json.loads(steer["input"][0]["text"])
        self.assertEqual(event["type"], "gkd_watchdog_event")
        self.assertEqual(event["reason"], "thread_system_error")
        self.assertNotIn("private body", steer["input"][0]["text"])

    def test_failed_terminal_steers_without_interrupting_terminal_child(self) -> None:
        for status in ("failed", "interrupted"):
            with self.subTest(status=status):
                clock = FakeClock()
                session = ScriptedSession(
                    clock, notifications=[turn_notification(status)]
                )
                result = WatchService(
                    lambda _request, _cancellation: session,
                    clock=clock,
                    cancel_poll_ms=3_600_000,
                ).watch(parsed_request())

                self.assertEqual(result.outcome, "abnormal_child")
                self.assertEqual(
                    [method for method, _ in session.calls],
                    [
                        "thread/read",
                        "thread/read",
                        "thread/read",
                        "thread/read",
                        "turn/steer",
                    ],
                )

    def test_explicit_remote_errored_is_abnormal(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, remote_errors={"thread/read": "errored"})
        result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
            parsed_request()
        )
        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(result.reason, "child_errored")
        self.assertEqual([method for method, _ in session.calls], ["thread/read"])

    def test_unknown_thread_state_fails_closed(self) -> None:
        for status in ("idle", "notLoaded", "futureStatus"):
            with self.subTest(status=status):
                clock = FakeClock()
                session = ScriptedSession(clock, statuses=[status])
                result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
                    parsed_request()
                )
                self.assertEqual(result.outcome, "protocol_error")

    def test_nonempty_turns_from_health_read_fail_closed(self) -> None:
        clock = FakeClock()

        class BodyLeakingSession(ScriptedSession):
            def request(self, method, params, *, timeout_ms):
                response = super().request(method, params, timeout_ms=timeout_ms)
                if method == "thread/read":
                    response["thread"]["turns"] = [{"body": "private"}]
                return response

        result = WatchService(
            lambda _request, _cancellation: BodyLeakingSession(clock), clock=clock
        ).watch(parsed_request())
        self.assertEqual(result.outcome, "protocol_error")

    def test_mismatched_steer_response_fails_closed(self) -> None:
        clock = FakeClock()

        class MismatchedSteerSession(ScriptedSession):
            def request(self, method, params, *, timeout_ms):
                if method == "turn/steer":
                    self.calls.append((method, dict(params)))
                    return {"turnId": "different-parent-turn"}
                return super().request(method, params, timeout_ms=timeout_ms)

        session = MismatchedSteerSession(
            clock, notifications=[turn_notification("failed")]
        )
        result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
            parsed_request()
        )
        self.assertEqual(result.outcome, "protocol_error")

    def test_non_expected_steer_errors_remain_protocol_errors(self) -> None:
        expected_reasons = {
            "notFound": "parent_steer_not_found",
            "systemError": "parent_steer_system_error",
            "invalidParams": "parent_steer_invalid_params",
            "remoteError": "parent_steer_remote_error",
        }
        for classification, expected_reason in expected_reasons.items():
            with self.subTest(classification=classification):
                clock = FakeClock()
                session = ScriptedSession(
                    clock,
                    notifications=[turn_notification("failed")],
                    remote_errors={"turn/steer": classification},
                )
                result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
                    parsed_request()
                )
                self.assertEqual(result.outcome, "protocol_error")
                self.assertEqual(result.reason, expected_reason)

    def test_thread_ownership_mismatch_fails_before_control(self) -> None:
        clock = FakeClock()

        class OwnershipSession(ScriptedSession):
            def __init__(self, *args, mode, **kwargs):
                super().__init__(*args, **kwargs)
                self.mode = mode

            def request(self, method, params, *, timeout_ms):
                response = super().request(method, params, timeout_ms=timeout_ms)
                if method != "thread/read":
                    return response
                thread = response["thread"]
                is_child = params["threadId"] == "child-thread-1"
                field, value = {
                    "child_session_missing": ("sessionId", None),
                    "child_session_wrong": ("sessionId", "other-session"),
                    "child_parent_missing": ("parentThreadId", None),
                    "child_parent_wrong": ("parentThreadId", "other-parent"),
                    "parent_session_missing": ("sessionId", None),
                    "parent_session_wrong": ("sessionId", "other-session"),
                }[self.mode]
                if self.mode.startswith("child_") == is_child:
                    if value is None:
                        thread.pop(field, None)
                    else:
                        thread[field] = value
                return response

        for mode in (
            "child_session_missing",
            "child_session_wrong",
            "child_parent_missing",
            "child_parent_wrong",
            "parent_session_missing",
            "parent_session_wrong",
        ):
            with self.subTest(mode=mode):
                session = OwnershipSession(clock, mode=mode)
                result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
                    parsed_request(maxWaitMs=1, healthIntervalMs=1)
                )
                self.assertEqual(result.outcome, "protocol_error")
                methods = [method for method, _ in session.calls]
                self.assertNotIn("turn/interrupt", methods)
                self.assertNotIn("turn/steer", methods)

    def test_thread_ownership_drift_blocks_interrupt_and_steer(self) -> None:
        system_error = (
            0,
            {
                "method": "thread/status/changed",
                "params": {
                    "threadId": "child-thread-1",
                    "status": {"type": "systemError"},
                },
            },
        )

        class DriftingSession(ScriptedSession):
            def __init__(self, *args, drift_thread, **kwargs):
                super().__init__(*args, **kwargs)
                self.drift_thread = drift_thread
                self.read_counts = {"child-thread-1": 0, "parent-thread-1": 0}

            def request(self, method, params, *, timeout_ms):
                response = super().request(method, params, timeout_ms=timeout_ms)
                if method == "thread/read":
                    thread_id = params["threadId"]
                    self.read_counts[thread_id] += 1
                    if thread_id == self.drift_thread and self.read_counts[thread_id] > 1:
                        response["thread"]["sessionId"] = "other-session"
                return response

        cases = (
            ("child-thread-1", [system_error]),
            ("parent-thread-1", [turn_notification("failed")]),
        )
        for drift_thread, notifications in cases:
            with self.subTest(drift_thread=drift_thread):
                clock = FakeClock()
                session = DriftingSession(
                    clock,
                    drift_thread=drift_thread,
                    notifications=notifications,
                )
                result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
                    parsed_request()
                )
                self.assertEqual(result.outcome, "protocol_error")
                methods = [method for method, _ in session.calls]
                self.assertNotIn("turn/interrupt", methods)
                self.assertNotIn("turn/steer", methods)

    def test_parent_read_remote_failure_is_protocol_not_child_abnormal(self) -> None:
        clock = FakeClock()

        class MissingParentSession(ScriptedSession):
            def request(self, method, params, *, timeout_ms):
                if method == "thread/read" and params["threadId"] == "parent-thread-1":
                    raise AppServerRemoteError("notFound")
                return super().request(method, params, timeout_ms=timeout_ms)

        session = MissingParentSession(clock)
        result = WatchService(
            lambda _request, _cancellation: session, clock=clock
        ).watch(parsed_request(maxWaitMs=1, healthIntervalMs=1))

        self.assertEqual(result.outcome, "protocol_error")
        self.assertEqual(result.reason, "parent_thread_read_not_found")
        self.assertNotIn("turn/steer", [method for method, _ in session.calls])

    def test_interrupt_without_bound_terminal_confirmation_never_steers(self) -> None:
        system_error = (
            0,
            {
                "method": "thread/status/changed",
                "params": {
                    "threadId": "child-thread-1",
                    "status": {"type": "systemError"},
                },
            },
        )
        wrong_thread = turn_notification("interrupted", at_ms=1)
        wrong_thread[1]["params"]["threadId"] = "other-child-thread"
        wrong_turn = turn_notification("interrupted", at_ms=1)
        wrong_turn[1]["params"]["turn"]["id"] = "other-child-turn"
        nonterminal = turn_notification("inProgress", at_ms=1)

        for confirmation in (None, wrong_thread, wrong_turn, nonterminal):
            with self.subTest(confirmation=confirmation):
                clock = FakeClock()
                notifications = [system_error]
                if confirmation is not None:
                    notifications.append(confirmation)
                session = ScriptedSession(clock, notifications=notifications)
                result = WatchService(
                    lambda _request, _cancellation: session,
                    clock=clock,
                    interrupt_confirm_timeout_ms=10,
                ).watch(parsed_request())

                self.assertEqual(result.outcome, "protocol_error")
                self.assertEqual(result.reason, "child_interrupt_unconfirmed")
                methods = [method for method, _ in session.calls]
                self.assertIn("turn/interrupt", methods)
                self.assertNotIn("turn/steer", methods)

    def test_wrong_expected_turn_is_rejected_once_without_fallback(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(
            clock,
            notifications=[turn_notification("failed")],
            remote_errors={"turn/steer": "expectedTurnMismatch"},
        )
        result = WatchService(
            lambda _request, _cancellation: session, clock=clock, cancel_poll_ms=3_600_000
        ).watch(parsed_request())

        self.assertEqual(result.outcome, "parent_steer_rejected")
        methods = [method for method, _ in session.calls]
        self.assertEqual(methods.count("turn/steer"), 1)
        self.assertNotIn("turn/start", methods)
        self.assertEqual(
            {params["threadId"] for method, params in session.calls if method == "turn/steer"},
            {"parent-thread-1"},
        )

    def test_not_found_is_abnormal_and_does_not_interrupt_parent(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(
            clock, remote_errors={"thread/read": "notFound"}
        )
        result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
            parsed_request()
        )

        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(
            [method for method, _ in session.calls],
            ["thread/read"],
        )

    def test_cancellation_interrupts_only_bound_child_and_never_parent(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(
            clock, notifications=[turn_notification("interrupted")]
        )
        token = CancellationToken()
        token.cancel()
        result = WatchService(lambda _request, _cancellation: session, clock=clock).watch(
            parsed_request(), token
        )

        self.assertEqual(result.outcome, "cancelled")
        methods = [method for method, _ in session.calls]
        self.assertEqual(
            methods,
            [
                "thread/read",
                "thread/read",
                "thread/read",
                "thread/read",
                "turn/interrupt",
            ],
        )
        self.assertNotIn("turn/steer", methods)

    def test_cancellation_interrupt_failure_is_terminal_protocol_error(self) -> None:
        expected_reasons = {
            "invalidParams": "child_interrupt_invalid_params",
            "systemError": "child_interrupt_system_error",
            "expectedTurnMismatch": "child_interrupt_expected_turn_mismatch",
            "remoteError": "child_interrupt_remote_error",
        }
        for classification, expected_reason in expected_reasons.items():
            with self.subTest(classification=classification):
                clock = FakeClock()
                session = ScriptedSession(
                    clock, remote_errors={"turn/interrupt": classification}
                )
                token = CancellationToken()
                token.cancel()
                result = WatchService(
                    lambda _request, _cancellation: session, clock=clock
                ).watch(parsed_request(), token)

                self.assertEqual(result.outcome, "protocol_error")
                self.assertEqual(result.reason, expected_reason)
                self.assertNotIn(
                    "turn/steer", [method for method, _ in session.calls]
                )

    def test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed(self) -> None:
        for classification in ("notFound", "errored", "interrupted"):
            with self.subTest(classification=classification):
                clock = FakeClock()
                session = ScriptedSession(
                    clock, remote_errors={"turn/interrupt": classification}
                )
                token = CancellationToken()
                token.cancel()
                result = WatchService(
                    lambda _request, _cancellation: session, clock=clock
                ).watch(parsed_request(), token)

                self.assertEqual(result.outcome, "cancelled")
                self.assertNotIn(
                    "turn/steer", [method for method, _ in session.calls]
                )

    def test_two_concurrent_instances_keep_identity_and_calls_separate(self) -> None:
        outcomes = {}
        sessions = {}

        def run(name: str) -> None:
            clock = FakeClock()
            session = ScriptedSession(
                clock, notifications=[turn_notification("completed")]
            )
            sessions[name] = session
            request = parsed_request(
                taskId=f"task-{name}",
                offerId=f"offer-{name}",
            )
            outcomes[name] = WatchService(
                lambda _request, _cancellation: session, clock=clock
            ).watch(request)

        threads = [threading.Thread(target=run, args=(name,)) for name in ("a", "b")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(outcomes["a"].request.task_id, "task-a")
        self.assertEqual(outcomes["b"].request.task_id, "task-b")
        self.assertIsNot(sessions["a"], sessions["b"])
        self.assertEqual(outcomes["a"].outcome, "normal_terminal")
        self.assertEqual(outcomes["b"].outcome, "normal_terminal")


if __name__ == "__main__":
    unittest.main()
