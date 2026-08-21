"""Bounded deterministic fixed-head terminal monitor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable

from gkd_task.canonical import require_keys, require_sha1, require_sha256
from gkd_task.errors import TaskError

from .github import GitHubClient, GitHubObservation
from .policy import (
    CHECK_RE,
    POLICY_PATH,
    RepositoryPolicy,
    _valid_branch,
    _valid_repository,
    load_validated_policy,
)


OUTCOMES = {"error", "failure", "head_drift", "success", "timeout"}


@dataclass(frozen=True)
class MonitorRequest:
    checkout: Path
    repository: str
    pull_request: int
    expected_head: str
    policy_path: str
    policy_digest: str
    timeout_seconds: int
    poll_interval_seconds: int

    def __post_init__(self) -> None:
        if not _valid_repository(self.repository):
            raise TaskError("REPOSITORY_INVALID")
        require_sha1(self.expected_head, "EXPECTED_HEAD_INVALID")
        require_sha256(self.policy_digest, "POLICY_DIGEST_INVALID")
        if (
            isinstance(self.pull_request, bool)
            or not isinstance(self.pull_request, int)
            or self.pull_request < 1
            or self.pull_request > 2_147_483_647
            or self.policy_path != POLICY_PATH
            or isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds < 1
            or self.timeout_seconds > 43_200
            or isinstance(self.poll_interval_seconds, bool)
            or not isinstance(self.poll_interval_seconds, int)
            or self.poll_interval_seconds < 1
            or self.poll_interval_seconds > self.timeout_seconds
        ):
            raise TaskError("MONITOR_REQUEST_INVALID")


def validate_terminal_result(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "baseBranch",
            "checks",
            "elapsedSeconds",
            "expectedHead",
            "headBranch",
            "observations",
            "observedHead",
            "outcome",
            "policyDigest",
            "provider",
            "pullRequest",
            "pullRequestState",
            "reason",
            "repository",
            "requiredChecks",
            "schemaVersion",
        },
        "TERMINAL_RESULT_INVALID",
    )
    early_error = all(
        value[field] is None
        for field in ("baseBranch", "expectedHead", "policyDigest", "pullRequest", "repository")
    )
    if (
        value["schemaVersion"] != 1
        or value["provider"] != "github"
        or value["outcome"] not in OUTCOMES
        or not isinstance(value["reason"], str)
        or not value["reason"]
        or not isinstance(value["observations"], int)
        or value["observations"] < 0
        or not isinstance(value["elapsedSeconds"], int)
        or value["elapsedSeconds"] < 0
        or not isinstance(value["checks"], list)
        or (not early_error and not _valid_repository(value["repository"]))
        or (not early_error and (isinstance(value["pullRequest"], bool) or not isinstance(value["pullRequest"], int)))
        or (not early_error and value["pullRequest"] < 1)
        or (not early_error and not _valid_branch(value["baseBranch"]))
        or (value["headBranch"] is not None and not _valid_branch(value["headBranch"]))
        or value["pullRequestState"] not in {None, "closed", "open"}
        or not isinstance(value["requiredChecks"], list)
        or (not early_error and not value["requiredChecks"])
        or value["requiredChecks"] != sorted(set(value["requiredChecks"]))
        or any(not isinstance(check, str) or not CHECK_RE.fullmatch(check) for check in value["requiredChecks"])
        or (early_error and (
            value["outcome"] != "error"
            or value["checks"]
            or value["requiredChecks"]
            or value["headBranch"] is not None
            or value["observedHead"] is not None
            or value["pullRequestState"] is not None
            or value["observations"] != 0
            or value["elapsedSeconds"] != 0
        ))
        or (not early_error and any(
            value[field] is None
            for field in ("baseBranch", "expectedHead", "policyDigest", "pullRequest", "repository")
        ))
    ):
        raise TaskError("TERMINAL_RESULT_INVALID")
    if early_error:
        return
    require_sha1(value["expectedHead"], "TERMINAL_RESULT_INVALID")
    require_sha256(value["policyDigest"], "TERMINAL_RESULT_INVALID")
    if value["observedHead"] is not None:
        require_sha1(value["observedHead"], "TERMINAL_RESULT_INVALID")
    check_names = []
    for check in value["checks"]:
        require_keys(check, {"name", "state"}, "TERMINAL_RESULT_INVALID")
        if check["name"] not in value["requiredChecks"] or check["state"] not in {"failure", "pending", "success"}:
            raise TaskError("TERMINAL_RESULT_INVALID")
        check_names.append(check["name"])
    if check_names != sorted(set(check_names), key=value["requiredChecks"].index):
        raise TaskError("TERMINAL_RESULT_INVALID")
    if value["outcome"] == "success" and (
        value["observedHead"] != value["expectedHead"]
        or value["pullRequestState"] != "open"
        or check_names != value["requiredChecks"]
        or any(check["state"] != "success" for check in value["checks"])
    ):
        raise TaskError("TERMINAL_RESULT_INVALID")


def _terminal(
    request: MonitorRequest,
    policy: RepositoryPolicy,
    outcome: str,
    reason: str,
    observations: int,
    elapsed: float,
    observation: GitHubObservation | None,
) -> dict[str, Any]:
    value = {
        "baseBranch": policy.base_branch,
        "checks": [
            {"name": name, "state": state}
            for name, state in (() if observation is None else observation.checks)
        ],
        "elapsedSeconds": int(elapsed),
        "expectedHead": request.expected_head,
        "headBranch": None if observation is None else observation.head_branch,
        "observations": observations,
        "observedHead": None if observation is None else observation.head_sha,
        "outcome": outcome,
        "policyDigest": request.policy_digest,
        "provider": "github",
        "pullRequest": request.pull_request,
        "pullRequestState": None if observation is None else observation.state,
        "reason": reason,
        "repository": request.repository,
        "requiredChecks": list(policy.required_checks),
        "schemaVersion": 1,
    }
    validate_terminal_result(value)
    return value


def monitor_fixed_head(
    request: MonitorRequest,
    github: GitHubClient | Any | None = None,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    started = monotonic()
    deadline = started + request.timeout_seconds
    policy = load_validated_policy(request.checkout, request.repository, request.policy_path)
    if policy.digest != request.policy_digest:
        return _terminal(request, policy, "error", "POLICY_DRIFT", 0, 0, None)
    if monotonic() >= deadline:
        return _terminal(request, policy, "timeout", "DEADLINE_EXHAUSTED", 0, monotonic() - started, None)
    client = github or GitHubClient(deadline=deadline, monotonic=monotonic)
    observations = 0
    last: GitHubObservation | None = None
    while True:
        try:
            observed_policy = load_validated_policy(request.checkout, request.repository, request.policy_path)
            if observed_policy.digest != request.policy_digest:
                return _terminal(request, policy, "error", "POLICY_DRIFT", observations, monotonic() - started, last)
            observation = client.observe(
                request.repository,
                request.pull_request,
                request.expected_head,
                policy.required_checks,
            )
            observations += 1
            last = observation
            observed_policy = load_validated_policy(request.checkout, request.repository, request.policy_path)
            if observed_policy.digest != request.policy_digest:
                return _terminal(request, policy, "error", "POLICY_DRIFT", observations, monotonic() - started, observation)
        except TaskError as error:
            if error.code == "GITHUB_DEADLINE_EXHAUSTED":
                return _terminal(request, policy, "timeout", "DEADLINE_EXHAUSTED", observations, monotonic() - started, last)
            return _terminal(request, policy, "error", error.code, observations, monotonic() - started, last)
        if monotonic() >= deadline:
            return _terminal(request, policy, "timeout", "DEADLINE_EXHAUSTED", observations, monotonic() - started, observation)
        if observation.repository.casefold() != request.repository.casefold():
            return _terminal(request, policy, "error", "LIVE_REPOSITORY_MISMATCH", observations, monotonic() - started, observation)
        if observation.pull_request != request.pull_request:
            return _terminal(request, policy, "error", "LIVE_PULL_REQUEST_MISMATCH", observations, monotonic() - started, observation)
        if observation.base_branch != policy.base_branch:
            return _terminal(request, policy, "error", "LIVE_BASE_BRANCH_MISMATCH", observations, monotonic() - started, observation)
        if observation.head_sha != request.expected_head:
            return _terminal(request, policy, "head_drift", "HEAD_DRIFT", observations, monotonic() - started, observation)
        if observation.state != "open":
            return _terminal(request, policy, "failure", "PULL_REQUEST_NOT_OPEN", observations, monotonic() - started, observation)
        checks = observation.checks
        if any(state == "failure" for _, state in checks):
            return _terminal(request, policy, "failure", "REQUIRED_CHECK_FAILED", observations, monotonic() - started, observation)
        if len(checks) == len(policy.required_checks) and all(state == "success" for _, state in checks):
            return _terminal(request, policy, "success", "ALL_REQUIRED_CHECKS_SUCCESSFUL", observations, monotonic() - started, observation)
        now = monotonic()
        if now >= deadline:
            return _terminal(request, policy, "timeout", "DEADLINE_EXHAUSTED", observations, now - started, observation)
        sleeper(min(float(request.poll_interval_seconds), deadline - now))
