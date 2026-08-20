from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from gkd_ci.github import GitHubObservation
from gkd_ci.monitor import MonitorRequest, monitor_fixed_head, validate_terminal_result
from gkd_ci.policy import POLICY_PATH, load_validated_policy
from gkd_task.errors import TaskError
from tests.ci_policy.helpers import (
    EXPECTED_HEAD,
    SYNTHETIC_CHECK,
    SYNTHETIC_REPOSITORY,
    init_checkout,
    policy_value,
    write_policy,
)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeGitHub:
    def __init__(self, observations):
        self.observations = list(observations)
        self.calls = 0

    def observe(self, repository, pull_request, expected_head, required_checks):
        del repository, pull_request, expected_head, required_checks
        self.calls += 1
        value = self.observations.pop(0) if self.observations else self.last
        if isinstance(value, Exception):
            raise value
        self.last = value
        return value


def observation(
    *,
    head: str = EXPECTED_HEAD,
    state: str = "open",
    checks=((SYNTHETIC_CHECK, "success"),),
) -> GitHubObservation:
    return GitHubObservation(
        base_branch="main",
        checks=tuple(checks),
        head_branch="task/change",
        head_sha=head,
        pull_request=8,
        repository=SYNTHETIC_REPOSITORY,
        state=state,
    )


class MonitorContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-m3-monitor-")
        self.root = Path(self.temporary.name).resolve()
        self.checkout = init_checkout(self.root)
        self.policy = load_validated_policy(self.checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self, timeout: int = 10, interval: int = 2) -> MonitorRequest:
        return MonitorRequest(
            checkout=self.checkout,
            repository=SYNTHETIC_REPOSITORY,
            pull_request=8,
            expected_head=EXPECTED_HEAD,
            policy_path=POLICY_PATH,
            policy_digest=self.policy.digest,
            timeout_seconds=timeout,
            poll_interval_seconds=interval,
        )

    def test_exact_head_all_required_checks_success_is_the_only_success(self) -> None:
        clock = FakeClock()
        result = monitor_fixed_head(
            self.request(), FakeGitHub([observation()]), clock.monotonic, clock.sleep
        )
        self.assertEqual("success", result["outcome"])
        self.assertEqual("ALL_REQUIRED_CHECKS_SUCCESSFUL", result["reason"])
        self.assertEqual(EXPECTED_HEAD, result["expectedHead"])
        self.assertEqual(EXPECTED_HEAD, result["observedHead"])
        self.assertEqual([{"name": SYNTHETIC_CHECK, "state": "success"}], result["checks"])

    def test_head_drift_terminal_failure_and_closed_pr_are_terminal(self) -> None:
        cases = (
            (observation(head="b" * 40), "head_drift", "HEAD_DRIFT"),
            (observation(checks=((SYNTHETIC_CHECK, "failure"),)), "failure", "REQUIRED_CHECK_FAILED"),
            (observation(state="closed", checks=()), "failure", "PULL_REQUEST_NOT_OPEN"),
            (
                GitHubObservation(
                    base_branch="release",
                    checks=((SYNTHETIC_CHECK, "success"),),
                    head_branch="task/change",
                    head_sha=EXPECTED_HEAD,
                    pull_request=8,
                    repository=SYNTHETIC_REPOSITORY,
                    state="open",
                ),
                "error",
                "LIVE_BASE_BRANCH_MISMATCH",
            ),
        )
        for value, outcome, reason in cases:
            with self.subTest(reason=reason):
                client = FakeGitHub([value])
                clock = FakeClock()
                result = monitor_fixed_head(self.request(), client, clock.monotonic, clock.sleep)
                self.assertEqual(outcome, result["outcome"])
                self.assertEqual(reason, result["reason"])
                self.assertEqual(1, client.calls)

    def test_pending_and_missing_checks_poll_then_timeout_once(self) -> None:
        for checks in (((SYNTHETIC_CHECK, "pending"),), ()):
            with self.subTest(checks=checks):
                client = FakeGitHub([observation(checks=checks)])
                clock = FakeClock()
                result = monitor_fixed_head(
                    self.request(timeout=5, interval=2), client, clock.monotonic, clock.sleep
                )
                self.assertEqual("timeout", result["outcome"])
                self.assertEqual("DEADLINE_EXHAUSTED", result["reason"])
                self.assertEqual(4, result["observations"])
                self.assertEqual(5.0, clock.value)

    def test_policy_drift_and_transport_error_return_stable_terminal_errors(self) -> None:
        class DriftingGitHub(FakeGitHub):
            def observe(inner, *args):
                value = super().observe(*args)
                write_policy(
                    self.checkout,
                    policy_value(checks=["Fixture Verify", "Second Verify"]),
                )
                return value

        clock = FakeClock()
        drift = monitor_fixed_head(
            self.request(),
            DriftingGitHub([observation()]),
            clock.monotonic,
            clock.sleep,
        )
        self.assertEqual("error", drift["outcome"])
        self.assertEqual("POLICY_DRIFT", drift["reason"])
        self.assertEqual(self.policy.digest, drift["policyDigest"])
        write_policy(self.checkout)
        clock = FakeClock()
        transport = monitor_fixed_head(
            self.request(),
            FakeGitHub([TaskError("GITHUB_QUERY_FAILED")]),
            clock.monotonic,
            clock.sleep,
        )
        self.assertEqual("error", transport["outcome"])
        self.assertEqual("GITHUB_QUERY_FAILED", transport["reason"])
        self.assertNotIn(str(self.checkout), str(transport))

    def test_observation_completing_at_deadline_cannot_report_success(self) -> None:
        class SlowGitHub(FakeGitHub):
            def observe(inner, *args):
                clock.value = 5.0
                return super().observe(*args)

        clock = FakeClock()
        result = monitor_fixed_head(
            self.request(timeout=5), SlowGitHub([observation()]), clock.monotonic, clock.sleep
        )
        self.assertEqual("timeout", result["outcome"])
        self.assertEqual("DEADLINE_EXHAUSTED", result["reason"])

    def test_terminal_result_rejects_state_and_check_binding_mutations(self) -> None:
        clock = FakeClock()
        result = monitor_fixed_head(
            self.request(), FakeGitHub([observation()]), clock.monotonic, clock.sleep
        )
        for field, value in (
            ("pullRequestState", "closed"),
            ("policyDigest", "invalid"),
            ("checks", []),
        ):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = value
                with self.assertRaisesRegex(TaskError, "TERMINAL_RESULT_INVALID"):
                    validate_terminal_result(mutated)


if __name__ == "__main__":
    unittest.main()
