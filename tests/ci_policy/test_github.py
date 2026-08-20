from __future__ import annotations

import subprocess
import unittest

from gkd_ci.github import GitHubClient
from gkd_task.errors import TaskError
from tests.ci_policy.helpers import (
    EXPECTED_HEAD,
    SYNTHETIC_CHECK,
    SYNTHETIC_REPOSITORY,
    check_run,
    pull_request,
    status_context,
)


class FixtureClient(GitHubClient):
    def __init__(self, responses):
        super().__init__()
        self.responses = list(responses)

    def _request(self, endpoint: str):
        del endpoint
        if not self.responses:
            raise AssertionError("fixture exhausted")
        return self.responses.pop(0)


class GitHubBoundaryContracts(unittest.TestCase):
    def test_check_runs_and_status_contexts_are_normalized(self) -> None:
        checks = FixtureClient(
            [pull_request(), {"check_runs": [check_run()], "total_count": 1}, []]
        ).observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))
        self.assertEqual(((SYNTHETIC_CHECK, "success"),), checks.checks)
        statuses = FixtureClient(
            [pull_request(), {"check_runs": [], "total_count": 0}, [status_context()], []]
        ).observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))
        self.assertEqual(((SYNTHETIC_CHECK, "success"),), statuses.checks)

    def test_pagination_is_complete_and_deterministic(self) -> None:
        first = [check_run(f"Other {index}") for index in range(99)]
        first.append(check_run(SYNTHETIC_CHECK))
        client = FixtureClient(
            [
                pull_request(),
                {"check_runs": first, "total_count": 101},
                {"check_runs": [check_run("Last Other")], "total_count": 101},
                [status_context(f"Status {index}") for index in range(100)],
                [],
            ]
        )
        observation = client.observe(
            SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,)
        )
        self.assertEqual(((SYNTHETIC_CHECK, "success"),), observation.checks)
        self.assertEqual([], client.responses)

    def test_duplicate_cross_source_and_unknown_conclusion_fail_closed(self) -> None:
        duplicate = FixtureClient(
            [
                pull_request(),
                {"check_runs": [check_run()], "total_count": 1},
                [status_context()],
                [],
            ]
        )
        with self.assertRaisesRegex(TaskError, "REQUIRED_CHECK_AMBIGUOUS"):
            duplicate.observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))
        unknown = FixtureClient(
            [
                pull_request(),
                {"check_runs": [check_run(conclusion="future_state")], "total_count": 1},
                [],
            ]
        )
        with self.assertRaisesRegex(TaskError, "GITHUB_RESPONSE_INVALID"):
            unknown.observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))

    def test_pr_repository_number_branch_sha_and_response_shapes_are_strict(self) -> None:
        mutations = (
            pull_request(number=9),
            pull_request(repository="acme/other"),
            pull_request(head_branch="bad..branch"),
        )
        for value in mutations:
            with self.subTest(value=value), self.assertRaisesRegex(TaskError, "GITHUB_RESPONSE_INVALID"):
                FixtureClient([value]).observe(
                    SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,)
                )
        mismatch = FixtureClient(
            [
                pull_request(),
                {"check_runs": [check_run(head="b" * 40)], "total_count": 1},
                [],
            ]
        )
        with self.assertRaisesRegex(TaskError, "GITHUB_RESPONSE_INVALID"):
            mismatch.observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))

    def test_head_drift_returns_pr_fact_without_querying_checks(self) -> None:
        client = FixtureClient([pull_request(head="b" * 40)])
        observed = client.observe(
            SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,)
        )
        self.assertEqual("b" * 40, observed.head_sha)
        self.assertEqual((), observed.checks)
        self.assertEqual([], client.responses)

    def test_adapter_deadline_exhaustion_stops_before_subprocess(self) -> None:
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("runner must not be called")

        client = GitHubClient(runner=runner, deadline=5.0, monotonic=lambda: 5.0)
        with self.assertRaisesRegex(TaskError, "GITHUB_DEADLINE_EXHAUSTED"):
            client.observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))
        self.assertEqual([], calls)

    def test_github_subprocess_surface_is_read_only_and_errors_are_redacted(self) -> None:
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 1, "raw body", "Bearer fixture-secret /Users/private")

        client = GitHubClient(runner=runner)
        with self.assertRaisesRegex(TaskError, "GITHUB_QUERY_FAILED") as raised:
            client.observe(SYNTHETIC_REPOSITORY, 8, EXPECTED_HEAD, (SYNTHETIC_CHECK,))
        self.assertNotIn("fixture-secret", str(raised.exception))
        self.assertEqual("gh", calls[0][0][0])
        self.assertEqual(("api", "--method", "GET"), calls[0][0][1:4])
        self.assertNotIn("--paginate", calls[0][0])
        self.assertFalse(calls[0][1]["check"])


if __name__ == "__main__":
    unittest.main()
