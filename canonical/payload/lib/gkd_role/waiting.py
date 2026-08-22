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
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise TaskError("INVALID_WAIT_STATE") from None


def validate_wait_state(value: dict[str, Any]) -> None:
    legacy_keys = {"schemaVersion", "taskId", "repository", "head", "claimId", "agentId", "sessionDigest", "bundleDigest", "startedAt", "deadlineAt", "completedIntervals", "interruptIssued", "terminal", "stateDigest"}
    acknowledgement_keys = {"schemaVersion", "taskId", "repository", "head", "claimId", "executorTaskName", "executorAttemptDigest", "bundleDigest", "startedAt", "deadlineAt", "completedIntervals", "interruptIssued", "terminal", "stateDigest"}
    if value.get("schemaVersion") == 1:
        require_keys(value, legacy_keys, "INVALID_WAIT_STATE")
        identity_names = ("agentId", "sessionDigest")
    elif value.get("schemaVersion") == 2:
        require_keys(value, acknowledgement_keys, "INVALID_WAIT_STATE")
        identity_names = ("executorTaskName", "executorAttemptDigest")
    else:
        raise TaskError("INVALID_WAIT_STATE")
    for field in ("taskId", "repository", identity_names[0]):
        require_string(value[field], "INVALID_WAIT_STATE")
    require_sha1(value["head"], "INVALID_WAIT_STATE")
    for field in ("claimId", identity_names[1], "bundleDigest", "stateDigest"):
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
    acknowledgement_keys = {"taskId", "repository", "head", "claimId", "executorTaskName", "executorAttemptDigest", "bundleDigest"}
    legacy_keys = {"taskId", "repository", "head", "claimId", "agentId", "sessionDigest", "bundleDigest"}
    if set(facts) == acknowledgement_keys:
        schema_version = 2
    elif set(facts) == legacy_keys:
        schema_version = 1
    else:
        raise TaskError("INVALID_WAIT_STATE")
    started = _time(started_at)
    value = {"schemaVersion": schema_version, **facts, "startedAt": started_at, "deadlineAt": (started + timedelta(hours=MAX_INTERVALS)).strftime("%Y-%m-%dT%H:%M:%SZ"), "completedIntervals": 0, "interruptIssued": False, "terminal": None}
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
    identity_names = ("executorTaskName", "executorAttemptDigest") if state["schemaVersion"] == 2 else ("agentId", "sessionDigest")
    expected_identity = {name: state[name] for name in ("taskId", "repository", "head", "claimId", *identity_names, "bundleDigest")}
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
        deadline = _time(state["deadlineAt"])
        if observed >= deadline:
            updated["completedIntervals"] = MAX_INTERVALS
            outcome = "deadline_timeout"
            updated["interruptIssued"] = True
            updated["terminal"] = {"outcome": outcome, "observedAt": observation["observedAt"]}
        else:
            minimum = _time(state["startedAt"]) + timedelta(hours=state["completedIntervals"] + 1)
            if observed < minimum:
                raise TaskError("WAIT_INTERVAL_NOT_ELAPSED")
            updated["completedIntervals"] += 1
            outcome = "wait_again"
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
        "interrupt": ({"executorTaskName": state["executorTaskName"], "once": True} if state["schemaVersion"] == 2 else {"agentId": state["agentId"], "once": True}) if outcome == "deadline_timeout" else None,
        "state": updated,
    }
    decision["decisionDigest"] = digest_object(decision)
    return decision
