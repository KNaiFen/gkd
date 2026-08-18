"""Deterministic one-hour wait and 12-hour deadline state."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256, require_string, require_utc
from gkd_task.errors import TaskError


WAIT_TIMEOUT_MS = 3_600_000
MAX_INTERVALS = 12


def _time(value: str) -> datetime:
    require_utc(value, "INVALID_WAIT_STATE")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def validate_wait_state(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "taskId", "repository", "head", "claimId", "agentId", "sessionDigest", "bundleDigest", "startedAt", "deadlineAt", "completedIntervals", "interruptIssued", "terminal", "stateDigest"},
        "INVALID_WAIT_STATE",
    )
    if value["schemaVersion"] != 1:
        raise TaskError("INVALID_WAIT_STATE")
    for field in ("taskId", "repository", "agentId"):
        require_string(value[field], "INVALID_WAIT_STATE")
    require_sha1(value["head"], "INVALID_WAIT_STATE")
    for field in ("claimId", "sessionDigest", "bundleDigest", "stateDigest"):
        require_sha256(value[field], "INVALID_WAIT_STATE")
    started = _time(value["startedAt"])
    deadline = _time(value["deadlineAt"])
    if deadline != started + timedelta(hours=MAX_INTERVALS):
        raise TaskError("INVALID_WAIT_STATE")
    if not isinstance(value["completedIntervals"], int) or not 0 <= value["completedIntervals"] <= MAX_INTERVALS:
        raise TaskError("INVALID_WAIT_STATE")
    if not isinstance(value["interruptIssued"], bool) or (value["terminal"] is not None and not isinstance(value["terminal"], dict)):
        raise TaskError("INVALID_WAIT_STATE")
    unsigned = deepcopy(value)
    actual = unsigned.pop("stateDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_WAIT_STATE")


def new_wait_state(facts: dict[str, Any], started_at: str) -> dict[str, Any]:
    require_keys(facts, {"taskId", "repository", "head", "claimId", "agentId", "sessionDigest", "bundleDigest"}, "INVALID_WAIT_STATE")
    started = _time(started_at)
    value = {"schemaVersion": 1, **facts, "startedAt": started_at, "deadlineAt": (started + timedelta(hours=MAX_INTERVALS)).strftime("%Y-%m-%dT%H:%M:%SZ"), "completedIntervals": 0, "interruptIssued": False, "terminal": None}
    value["stateDigest"] = digest_object(value)
    validate_wait_state(value)
    return value


def transition(state: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    validate_wait_state(state)
    require_keys(observation, {"schemaVersion", "kind", "observedAt", "timeoutMs", "identity"}, "INVALID_WAIT_OBSERVATION")
    if observation["schemaVersion"] != 1 or observation["kind"] not in {"healthy_timeout", "executor_terminal", "executor_error", "user_intervention"}:
        raise TaskError("INVALID_WAIT_OBSERVATION")
    observed = _time(observation["observedAt"])
    identity = observation["identity"]
    expected_identity = {name: state[name] for name in ("taskId", "repository", "head", "claimId", "agentId", "sessionDigest", "bundleDigest")}
    drift = not isinstance(identity, dict) or identity != expected_identity
    if state["terminal"] is not None:
        raise TaskError("WAIT_ALREADY_TERMINAL")
    updated = deepcopy(state)
    if drift:
        outcome = "fail_closed_drift"
        updated["terminal"] = {"outcome": outcome, "observedAt": observation["observedAt"]}
    elif observation["kind"] == "healthy_timeout":
        if observation["timeoutMs"] != WAIT_TIMEOUT_MS:
            raise TaskError("WAIT_TIMEOUT_PARAMETER_MISMATCH")
        minimum = _time(state["startedAt"]) + timedelta(hours=state["completedIntervals"] + 1)
        if observed < minimum:
            raise TaskError("WAIT_INTERVAL_NOT_ELAPSED")
        updated["completedIntervals"] += 1
        if updated["completedIntervals"] < MAX_INTERVALS:
            outcome = "wait_again"
        else:
            outcome = "deadline_timeout"
            updated["interruptIssued"] = True
            updated["terminal"] = {"outcome": outcome, "observedAt": observation["observedAt"]}
    else:
        if observation["timeoutMs"] is not None:
            raise TaskError("INVALID_WAIT_OBSERVATION")
        outcome = "executor_error" if observation["kind"] == "executor_error" else "executor_terminal"
        updated["terminal"] = {"outcome": outcome, "observedAt": observation["observedAt"]}
    updated.pop("stateDigest", None)
    updated["stateDigest"] = digest_object(updated)
    decision = {
        "schemaVersion": 1,
        "outcome": outcome,
        "waitTimeoutMs": WAIT_TIMEOUT_MS if outcome == "wait_again" else None,
        "sameAgentRequired": outcome == "wait_again",
        "voluntaryOutputAllowed": False if outcome == "wait_again" else True,
        "inspectionAllowed": False if outcome == "wait_again" else True,
        "interrupt": {"agentId": state["agentId"], "once": True} if outcome == "deadline_timeout" else None,
        "state": updated,
    }
    decision["decisionDigest"] = digest_object(decision)
    return decision
