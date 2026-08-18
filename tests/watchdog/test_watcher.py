from __future__ import annotations

import json
import threading
import unittest

from gkd_watchdog.watcher import CancellationToken, WatchService
from gkd_watchdog.jsonrpc import AppServerError

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
    def test_twelve_hour_deadline_is_single_and_hourly_ticks_are_silent(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, statuses=["active"] * 20)
        service = WatchService(
            lambda _request: session,
            clock=clock,
            cancel_poll_ms=3_600_000,
        )

        result = service.watch(parsed_request())

        self.assertEqual(result.outcome, "deadline")
        self.assertEqual(result.elapsed_ms, 43_200_000)
        self.assertEqual(result.health_checks, 12)
        methods = [method for method, _ in session.calls]
        self.assertEqual(methods, ["thread/read"] * 12)
        self.assertNotIn("turn/interrupt", methods)
        self.assertNotIn("turn/steer", methods)

    def test_normal_terminal_returns_immediately_without_steer(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, notifications=[turn_notification("completed")])
        result = WatchService(
            lambda _request: session, clock=clock, cancel_poll_ms=3_600_000
        ).watch(parsed_request())

        self.assertEqual(result.outcome, "normal_terminal")
        self.assertEqual(result.elapsed_ms, 0)
        self.assertEqual([method for method, _ in session.calls], ["thread/read"])

    def test_stale_active_child_remains_healthy_across_ticks(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, statuses=["active"] * 8)
        request = parsed_request(maxWaitMs=10_000, healthIntervalMs=2_000)
        result = WatchService(
            lambda _request: session, clock=clock, cancel_poll_ms=2_000
        ).watch(request)

        self.assertEqual(result.outcome, "deadline")
        self.assertEqual(result.health_checks, 5)
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
        session = ScriptedSession(clock, notifications=[notification])
        result = WatchService(
            lambda _request: session, clock=clock, cancel_poll_ms=3_600_000
        ).watch(parsed_request())

        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(
            [method for method, _ in session.calls],
            ["thread/read", "turn/interrupt", "turn/steer"],
        )
        interrupt = session.calls[1][1]
        self.assertEqual(
            interrupt,
            {"threadId": "child-thread-1", "turnId": "child-turn-1"},
        )
        steer = session.calls[2][1]
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
                    lambda _request: session,
                    clock=clock,
                    cancel_poll_ms=3_600_000,
                ).watch(parsed_request())

                self.assertEqual(result.outcome, "abnormal_child")
                self.assertEqual(
                    [method for method, _ in session.calls],
                    ["thread/read", "turn/steer"],
                )

    def test_explicit_remote_errored_is_abnormal(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock, remote_errors={"thread/read": "errored"})
        result = WatchService(lambda _request: session, clock=clock).watch(
            parsed_request()
        )
        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(result.reason, "child_errored")

    def test_unknown_thread_state_fails_closed(self) -> None:
        for status in ("idle", "notLoaded", "futureStatus"):
            with self.subTest(status=status):
                clock = FakeClock()
                session = ScriptedSession(clock, statuses=[status])
                result = WatchService(lambda _request: session, clock=clock).watch(
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
            lambda _request: BodyLeakingSession(clock), clock=clock
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
        result = WatchService(lambda _request: session, clock=clock).watch(
            parsed_request()
        )
        self.assertEqual(result.outcome, "protocol_error")

    def test_secondary_protocol_error_after_not_found_is_terminal(self) -> None:
        clock = FakeClock()

        class BrokenSteerSession(ScriptedSession):
            def request(self, method, params, *, timeout_ms):
                if method == "turn/steer":
                    raise AppServerError()
                return super().request(method, params, timeout_ms=timeout_ms)

        session = BrokenSteerSession(
            clock, remote_errors={"thread/read": "notFound"}
        )
        result = WatchService(lambda _request: session, clock=clock).watch(
            parsed_request()
        )
        self.assertEqual(result.outcome, "protocol_error")

    def test_wrong_expected_turn_is_rejected_once_without_fallback(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(
            clock,
            notifications=[turn_notification("failed")],
            remote_errors={"turn/steer": "expectedTurnMismatch"},
        )
        result = WatchService(
            lambda _request: session, clock=clock, cancel_poll_ms=3_600_000
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
        result = WatchService(lambda _request: session, clock=clock).watch(
            parsed_request()
        )

        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(
            [method for method, _ in session.calls],
            ["thread/read", "turn/steer"],
        )

    def test_cancellation_interrupts_only_bound_child_and_never_parent(self) -> None:
        clock = FakeClock()
        session = ScriptedSession(clock)
        token = CancellationToken()
        token.cancel()
        result = WatchService(lambda _request: session, clock=clock).watch(
            parsed_request(), token
        )

        self.assertEqual(result.outcome, "cancelled")
        methods = [method for method, _ in session.calls]
        self.assertEqual(methods, ["thread/read", "turn/interrupt"])
        self.assertNotIn("turn/steer", methods)

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
                sessionId=f"session-{name}",
            )
            outcomes[name] = WatchService(
                lambda _request: session, clock=clock
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
