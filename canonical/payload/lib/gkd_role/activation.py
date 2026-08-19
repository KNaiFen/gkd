"""Trusted host-observed role activation records for task claims."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256, require_string, require_utc
from gkd_task.errors import TaskError
from .roles import ACTIVATION_PROVIDER


def _instant(value: str, code: str) -> datetime:
    require_utc(value, code)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise TaskError(code) from None


def validate_activation(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion", "kind", "activationId", "taskId", "repository", "taskBranch",
            "offerId", "envelopeId", "route", "agentId", "threadDigest", "roleName",
            "roleDigest", "configDigest", "bundleDigest", "effectiveModel",
            "effectiveReasoningEffort", "effectiveSandbox", "runtimeSeconds", "activatedAt",
            "offerCreatedAt", "offerExpiresAt", "evidenceClass", "providerName", "providerDigest", "activationDigest",
        },
        "INVALID_ACTIVATION",
    )
    if value["schemaVersion"] != 1 or value["kind"] != "role-activation" or value["evidenceClass"] != "host-runtime-event":
        raise TaskError("INVALID_ACTIVATION")
    for field in ("taskId", "repository", "taskBranch", "route", "agentId", "roleName", "effectiveModel", "effectiveReasoningEffort", "effectiveSandbox", "providerName"):
        require_string(value[field], "INVALID_ACTIVATION")
    for field in ("activationId", "offerId", "envelopeId", "threadDigest", "roleDigest", "configDigest", "bundleDigest", "providerDigest", "activationDigest"):
        require_sha256(value[field], "INVALID_ACTIVATION")
    if value["runtimeSeconds"] not in {3600, 43200}:
        raise TaskError("INVALID_ACTIVATION")
    for field in ("offerCreatedAt", "offerExpiresAt", "activatedAt"):
        _instant(value[field], "INVALID_ACTIVATION")
    if value["providerName"] != ACTIVATION_PROVIDER["name"] or value["providerDigest"] != digest_object(ACTIVATION_PROVIDER):
        raise TaskError("INVALID_ACTIVATION")
    if not _instant(value["offerCreatedAt"], "INVALID_ACTIVATION") <= _instant(value["activatedAt"], "INVALID_ACTIVATION") < _instant(value["offerExpiresAt"], "INVALID_ACTIVATION"):
        raise TaskError("INVALID_ACTIVATION")
    unsigned = deepcopy(value)
    actual = unsigned.pop("activationDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_ACTIVATION")


def validate_activation_receipt(value: dict[str, Any]) -> None:
    require_keys(value, {"schemaVersion", "kind", "activationId", "activationDigest", "claimId", "claimCommit", "claimReceiptDigest", "consumedAt", "receiptDigest"}, "INVALID_ACTIVATION_RECEIPT")
    if value["schemaVersion"] != 1 or value["kind"] != "activation-receipt":
        raise TaskError("INVALID_ACTIVATION_RECEIPT")
    for field in ("activationId", "activationDigest", "claimId", "claimReceiptDigest", "receiptDigest"):
        require_sha256(value[field], "INVALID_ACTIVATION_RECEIPT")
    require_sha1(value["claimCommit"], "INVALID_ACTIVATION_RECEIPT")
    require_utc(value["consumedAt"], "INVALID_ACTIVATION_RECEIPT")
    unsigned = deepcopy(value)
    actual = unsigned.pop("receiptDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_ACTIVATION_RECEIPT")


def validate_activation_binding(activation: dict[str, Any], expected: dict[str, Any]) -> None:
    """Validate task/offer/role binding for a host-owned activation consumer."""

    if activation["providerName"] != ACTIVATION_PROVIDER["name"] or activation["providerDigest"] != digest_object(ACTIVATION_PROVIDER):
        raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
    if not _instant(activation["offerCreatedAt"], "RUNTIME_EVIDENCE_MISMATCH") <= _instant(activation["activatedAt"], "RUNTIME_EVIDENCE_MISMATCH") < _instant(activation["offerExpiresAt"], "RUNTIME_EVIDENCE_MISMATCH"):
        raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
    for name in ("taskId", "repository", "taskBranch", "route", "roleDigest", "configDigest", "roleName", "bundleDigest", "offerId", "envelopeId", "offerCreatedAt", "offerExpiresAt"):
        if expected.get(name) != activation[name]:
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
