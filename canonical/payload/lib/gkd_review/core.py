"""Deterministic review intent, approval, and recovery state machine."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, digest_object, require_keys, require_sha256
from gkd_task.errors import TaskError

from .adapter import validate_adapter


ENTRY_POINTS = ("guided", "recon", "targeted")
REQUIRED_APPROVALS = ("review", "continue")
INTENT_WORDS = {"ci", "change", "diff", "review", "remediation", "pull", "request"}
MACHINE_PATH_RE = re.compile(r"(?:^|[\s\"'])/(?:Users|home|tmp|private/tmp|var/folders)(?:/|$)", re.IGNORECASE)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,127}$")


def _safe(value: Any, code: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum or "\x00" in value:
        raise TaskError(code)
    if CREDENTIAL_RE.search(value) or MACHINE_PATH_RE.search(value):
        raise TaskError(code)
    return value


def _facts(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict) or not set(value).issubset({"baseBranch", "baseSha", "headSha", "pullRequest", "requiredChecks", "resourcePreset"}):
        raise TaskError("REVIEW_FACTS_INVALID")
    result = deepcopy(value)
    for name in ("baseBranch", "baseSha", "headSha", "resourcePreset"):
        if name in result:
            _safe(result[name], "REVIEW_FACTS_INVALID", 128)
    if "pullRequest" in result and (isinstance(result["pullRequest"], bool) or not isinstance(result["pullRequest"], int) or result["pullRequest"] < 1):
        raise TaskError("REVIEW_FACTS_INVALID")
    checks = result.get("requiredChecks")
    if checks is not None:
        if not isinstance(checks, list) or checks != sorted(set(checks)) or any(not isinstance(item, str) or not item for item in checks):
            raise TaskError("REVIEW_FACTS_INVALID")
        for item in checks:
            _safe(item, "REVIEW_FACTS_INVALID", 128)
    return result


def recommend_review(intent: str | None, target: str | None = None) -> dict[str, Any]:
    if intent is not None:
        _safe(intent, "REVIEW_INTENT_INVALID")
    if target is not None:
        _safe(target, "REVIEW_TARGET_INVALID")
    normalized = (intent or "").casefold()
    matched = sorted(word for word in INTENT_WORDS if word in normalized.split())
    if target and matched:
        entry_point = "targeted"
        status = "recommended"
        reason = "EXPLICIT_TARGET_AND_INTENT"
    elif target:
        entry_point = "guided"
        status = "clarify"
        reason = "REVIEW_INTENT_AMBIGUOUS"
    elif matched:
        entry_point = "guided"
        status = "clarify"
        reason = "REVIEW_TARGET_AMBIGUOUS"
    else:
        entry_point = "recon"
        status = "clarify"
        reason = "REVIEW_INTENT_AMBIGUOUS"
    return {
        "schemaVersion": 1,
        "status": status,
        "entryPoint": entry_point,
        "candidates": list(ENTRY_POINTS),
        "reason": reason,
        "target": target,
        "intent": intent,
        "recommendationDigest": digest_object({
            "schemaVersion": 1,
            "status": status,
            "entryPoint": entry_point,
            "candidates": list(ENTRY_POINTS),
            "reason": reason,
            "target": target,
            "intent": intent,
        }),
    }


def validate_recommendation(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "status", "entryPoint", "candidates", "reason", "target", "intent", "recommendationDigest"},
        "RECOMMENDATION_INVALID",
    )
    if value["schemaVersion"] != 1 or value["status"] not in {"clarify", "recommended"} or value["entryPoint"] not in ENTRY_POINTS:
        raise TaskError("RECOMMENDATION_INVALID")
    if value["candidates"] != list(ENTRY_POINTS) or not isinstance(value["reason"], str):
        raise TaskError("RECOMMENDATION_INVALID")
    if value["intent"] is not None:
        _safe(value["intent"], "RECOMMENDATION_INVALID")
    if value["target"] is not None:
        _safe(value["target"], "RECOMMENDATION_INVALID")
    require_sha256(value["recommendationDigest"], "RECOMMENDATION_INVALID")
    expected = deepcopy(value)
    expected.pop("recommendationDigest")
    if value["recommendationDigest"] != digest_object(expected):
        raise TaskError("RECOMMENDATION_INVALID")


def _state_without_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop("stateDigest", None)
    return result


def validate_review_state(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "reviewId", "entryPoint", "status", "target", "intent", "adapter", "machineFacts", "approval", "cursor", "history", "stateDigest"},
        "REVIEW_STATE_INVALID",
    )
    if value["schemaVersion"] != 1 or value["entryPoint"] not in ENTRY_POINTS or value["status"] not in {"ready", "partially-approved", "resumed", "recovered"}:
        raise TaskError("REVIEW_STATE_INVALID")
    _safe(value["reviewId"], "REVIEW_STATE_INVALID", 128)
    if value["target"] is not None:
        _safe(value["target"], "REVIEW_STATE_INVALID")
    if value["intent"] is not None:
        _safe(value["intent"], "REVIEW_STATE_INVALID")
    validate_adapter(value["adapter"])
    try:
        facts = _facts(value["machineFacts"])
    except TaskError:
        raise TaskError("REVIEW_STATE_INVALID") from None
    if facts != value["machineFacts"]:
        raise TaskError("REVIEW_STATE_INVALID")
    approval = value["approval"]
    if not isinstance(approval, dict) or set(approval) != {"required", "approved", "pending"} or approval["required"] != list(REQUIRED_APPROVALS):
        raise TaskError("REVIEW_STATE_INVALID")
    if approval["approved"] != sorted(set(approval["approved"])) or approval["pending"] != sorted(set(approval["pending"])):
        raise TaskError("REVIEW_STATE_INVALID")
    if set(approval["approved"]) | set(approval["pending"]) != set(REQUIRED_APPROVALS) or set(approval["approved"]) & set(approval["pending"]):
        raise TaskError("REVIEW_STATE_INVALID")
    if not isinstance(value["cursor"], int) or value["cursor"] < 0 or not isinstance(value["history"], list) or not value["history"]:
        raise TaskError("REVIEW_STATE_INVALID")
    if any(item not in {"started", "partial-approval", "resumed", "recovered"} for item in value["history"]):
        raise TaskError("REVIEW_STATE_INVALID")
    require_sha256(value["stateDigest"], "REVIEW_STATE_INVALID")
    if value["stateDigest"] != digest_object(_state_without_digest(value)):
        raise TaskError("REVIEW_STATE_INVALID")


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value["stateDigest"] = digest_object(_state_without_digest(value))
    validate_review_state(value)
    return value


def begin_review(
    entry_point: str,
    adapter: dict[str, Any],
    *,
    target: str | None = None,
    intent: str | None = None,
    machine_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if entry_point not in ENTRY_POINTS:
        raise TaskError("REVIEW_ENTRY_POINT_INVALID")
    validate_adapter(adapter)
    if entry_point == "targeted" and not target:
        raise TaskError("REVIEW_TARGET_REQUIRED")
    if target is not None:
        _safe(target, "REVIEW_TARGET_INVALID")
    if intent is not None:
        _safe(intent, "REVIEW_INTENT_INVALID")
    facts = _facts(machine_facts)
    base = {
        "schemaVersion": 1,
        "entryPoint": entry_point,
        "target": target,
        "intent": intent,
        "adapter": deepcopy(adapter),
        "machineFacts": facts,
    }
    value = {
        **base,
        "reviewId": digest_object(base)[:32],
        "status": "ready",
        "approval": {"required": list(REQUIRED_APPROVALS), "approved": [], "pending": sorted(REQUIRED_APPROVALS)},
        "cursor": 0,
        "history": ["started"],
    }
    return _seal(value)


def approve_partial(value: dict[str, Any], approvals: list[str]) -> dict[str, Any]:
    validate_review_state(value)
    if not isinstance(approvals, list) or not approvals or any(item not in REQUIRED_APPROVALS for item in approvals):
        raise TaskError("APPROVAL_INVALID")
    updated = deepcopy(value)
    approved = sorted(set(updated["approval"]["approved"]) | set(approvals))
    updated["approval"]["approved"] = approved
    updated["approval"]["pending"] = sorted(set(REQUIRED_APPROVALS) - set(approved))
    updated["status"] = "partially-approved"
    updated["cursor"] += 1
    updated["history"].append("partial-approval")
    return _seal(updated)


def resume_review(value: dict[str, Any], continuation: dict[str, Any]) -> dict[str, Any]:
    validate_review_state(value)
    if not isinstance(continuation, dict) or continuation != {"continue": True}:
        raise TaskError("CONTINUATION_REQUIRED")
    if "review" not in value["approval"]["approved"]:
        raise TaskError("APPROVAL_REQUIRED")
    updated = deepcopy(value)
    updated["approval"]["approved"] = sorted(set(REQUIRED_APPROVALS))
    updated["approval"]["pending"] = []
    updated["status"] = "resumed"
    updated["cursor"] += 1
    updated["history"].append("resumed")
    return _seal(updated)


def recover_review(value: dict[str, Any]) -> dict[str, Any]:
    validate_review_state(value)
    if value["status"] not in {"partially-approved", "resumed", "recovered"}:
        raise TaskError("RECOVERY_NOT_AVAILABLE")
    updated = deepcopy(value)
    updated["status"] = "recovered"
    updated["history"].append("recovered")
    return _seal(updated)
