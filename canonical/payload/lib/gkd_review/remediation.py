"""Explicit review remediation planning with no merge or rerun writer."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, digest_object, require_keys, require_sha256
from gkd_task.errors import TaskError

from .core import MACHINE_PATH_RE, _safe


SEVERITIES = ("high", "low", "medium")


def _finding(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"id", "severity", "summary"}:
        raise TaskError("REMEDIATION_FINDING_INVALID")
    _safe(value["id"], "REMEDIATION_FINDING_INVALID", 64)
    _safe(value["summary"], "REMEDIATION_FINDING_INVALID", 256)
    if CREDENTIAL_RE.search(value["summary"]) or MACHINE_PATH_RE.search(value["summary"]) or value["severity"] not in SEVERITIES:
        raise TaskError("REMEDIATION_FINDING_INVALID")
    return deepcopy(value)


def _without_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop("remediationDigest", None)
    return result


def validate_remediation(value: dict[str, Any]) -> None:
    require_keys(value, {"schemaVersion", "reviewId", "status", "findings", "approvedFindings", "pendingFindings", "history", "remediationDigest"}, "REMEDIATION_INVALID")
    if value["schemaVersion"] != 1 or value["status"] not in {"proposed", "partially-approved", "resumed", "recovered"}:
        raise TaskError("REMEDIATION_INVALID")
    _safe(value["reviewId"], "REMEDIATION_INVALID", 128)
    findings = [_finding(item) for item in value["findings"]]
    ids = [item["id"] for item in findings]
    if not findings or ids != sorted(set(ids)):
        raise TaskError("REMEDIATION_INVALID")
    for name in ("approvedFindings", "pendingFindings"):
        if value[name] != sorted(set(value[name])) or any(item not in ids for item in value[name]):
            raise TaskError("REMEDIATION_INVALID")
    if set(value["approvedFindings"]) & set(value["pendingFindings"]) or set(value["approvedFindings"]) | set(value["pendingFindings"]) != set(ids):
        raise TaskError("REMEDIATION_INVALID")
    if not isinstance(value["history"], list) or not value["history"] or any(item not in {"proposed", "partial-approval", "resumed", "recovered"} for item in value["history"]):
        raise TaskError("REMEDIATION_INVALID")
    require_sha256(value["remediationDigest"], "REMEDIATION_INVALID")
    if value["remediationDigest"] != digest_object(_without_digest(value)):
        raise TaskError("REMEDIATION_INVALID")


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value["remediationDigest"] = digest_object(_without_digest(value))
    validate_remediation(value)
    return value


def begin_remediation(review_state: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    from .core import validate_review_state

    validate_review_state(review_state)
    normalized = sorted((_finding(item) for item in findings), key=lambda item: item["id"])
    if not normalized:
        raise TaskError("REMEDIATION_FINDINGS_REQUIRED")
    ids = [item["id"] for item in normalized]
    value = {
        "schemaVersion": 1,
        "reviewId": review_state["reviewId"],
        "status": "proposed",
        "findings": normalized,
        "approvedFindings": [],
        "pendingFindings": ids,
        "history": ["proposed"],
    }
    return _seal(value)


def approve_remediation(value: dict[str, Any], finding_ids: list[str]) -> dict[str, Any]:
    validate_remediation(value)
    if not isinstance(finding_ids, list) or not finding_ids or any(item not in value["pendingFindings"] for item in finding_ids):
        raise TaskError("REMEDIATION_APPROVAL_INVALID")
    updated = deepcopy(value)
    updated["approvedFindings"] = sorted(set(updated["approvedFindings"]) | set(finding_ids))
    updated["pendingFindings"] = sorted(set(item["id"] for item in updated["findings"]) - set(updated["approvedFindings"]))
    updated["status"] = "partially-approved"
    updated["history"].append("partial-approval")
    return _seal(updated)


def resume_remediation(value: dict[str, Any], continuation: dict[str, Any]) -> dict[str, Any]:
    validate_remediation(value)
    if continuation != {"continue": True}:
        raise TaskError("CONTINUATION_REQUIRED")
    if not value["approvedFindings"]:
        raise TaskError("REMEDIATION_APPROVAL_REQUIRED")
    updated = deepcopy(value)
    updated["approvedFindings"] = sorted(item["id"] for item in updated["findings"])
    updated["pendingFindings"] = []
    updated["status"] = "resumed"
    updated["history"].append("resumed")
    return _seal(updated)


def recover_remediation(value: dict[str, Any]) -> dict[str, Any]:
    validate_remediation(value)
    if value["status"] not in {"partially-approved", "resumed", "recovered"}:
        raise TaskError("RECOVERY_NOT_AVAILABLE")
    updated = deepcopy(value)
    updated["status"] = "recovered"
    updated["history"].append("recovered")
    return _seal(updated)
