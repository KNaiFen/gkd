"""Test-only host seam for deterministic activation/claim contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_role.activation import (
    _instant,
    validate_activation,
    validate_activation_binding,
    validate_activation_receipt,
)
from gkd_role.roles import activation_provider, role_record
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, require_keys, require_sha256, require_string
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService


def record_test_activation(
    runtime: RuntimeStore,
    catalog: dict[str, Any],
    expected: dict[str, Any],
    observation: dict[str, Any],
    nonce: str,
) -> dict[str, Any]:
    """Write a synthetic host event; this module is never packaged."""

    require_keys(expected, {"taskId", "repository", "taskBranch", "offerId", "envelopeId", "route", "roleName", "roleDigest", "configDigest", "bundleDigest", "offerCreatedAt", "offerExpiresAt"}, "INVALID_ACTIVATION_REQUEST")
    require_keys(observation, {"evidenceClass", "agentId", "threadDigest", "model", "reasoningEffort", "sandbox", "runtimeSeconds", "activatedAt"}, "INVALID_ACTIVATION_OBSERVATION")
    role = role_record(catalog, expected["roleName"])
    provider = activation_provider(catalog)
    if (
        observation["evidenceClass"] != "host-runtime-event"
        or expected["bundleDigest"] != catalog["bundleDigest"]
        or expected["roleDigest"] != role["roleDigest"]
        or expected["configDigest"] != role["configDigest"]
        or observation["model"] != role["model"]
        or observation["reasoningEffort"] != role["modelReasoningEffort"]
        or observation["sandbox"] != role["sandboxMode"]
        or observation["runtimeSeconds"] != role["runtimeSeconds"]
    ):
        raise TaskError("ACTIVATION_OBSERVATION_MISMATCH")
    require_sha256(observation["threadDigest"], "INVALID_ACTIVATION_OBSERVATION")
    require_string(observation["agentId"], "INVALID_ACTIVATION_OBSERVATION")
    if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
        raise TaskError("INVALID_ACTIVATION_REQUEST")
    if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") <= _instant(observation["activatedAt"], "INVALID_ACTIVATION_OBSERVATION") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
        raise TaskError("ACTIVATION_OUTSIDE_OFFER_WINDOW")
    activation_id = digest_object({"expected": expected, "observation": observation, "nonce": require_string(nonce, "INVALID_ACTIVATION_REQUEST")})
    value = {
        "schemaVersion": 1,
        "kind": "role-activation",
        "activationId": activation_id,
        **expected,
        "agentId": observation["agentId"],
        "threadDigest": observation["threadDigest"],
        "effectiveModel": observation["model"],
        "effectiveReasoningEffort": observation["reasoningEffort"],
        "effectiveSandbox": observation["sandbox"],
        "runtimeSeconds": observation["runtimeSeconds"],
        "activatedAt": observation["activatedAt"],
        "evidenceClass": observation["evidenceClass"],
        "providerName": provider["name"],
        "providerDigest": digest_object(provider),
    }
    value["activationDigest"] = digest_object(value)
    validate_activation(value)
    atomic_write(runtime._path("activations", activation_id), canonical_bytes(value), mode=0o600)
    return {"status": "activation_recorded", "activationId": activation_id, "activationDigest": value["activationDigest"]}


class TestActivationEvidenceProvider:
    """Synthetic consumer used only by hermetic/L2 tests."""

    def __init__(self, runtime: RuntimeStore, activation_id: str, catalog: dict[str, Any]) -> None:
        require_sha256(activation_id, "INVALID_ACTIVATION")
        self.runtime = runtime
        self.activation_id = activation_id
        provider = activation_provider(catalog)
        self.provider_name = provider["name"]
        self.provider_digest = digest_object(provider)
        self.activation: dict[str, Any] | None = None

    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]:
        if purpose != "claim":
            raise TaskError("RUNTIME_EVIDENCE_UNAVAILABLE")
        try:
            self.runtime.read_activation_receipt(self.activation_id)
        except TaskError as error:
            if error.code != "ACTIVATION_RECEIPT_UNAVAILABLE":
                raise
        else:
            raise TaskError("ACTIVATION_REPLAYED")
        activation = self.runtime.read_activation(self.activation_id)
        validate_activation_binding(activation, expected)
        self.activation = activation
        value = {
            "schemaVersion": 1,
            "provider": activation["providerName"],
            "writerId": activation["agentId"],
            "sessionDigest": activation["threadDigest"],
            "roleDigest": activation["roleDigest"],
            "configDigest": activation["configDigest"],
            "route": activation["route"],
            "status": "active",
            "observedAt": activation["activatedAt"],
        }
        value["evidenceDigest"] = digest_object(value)
        return value

    def consume(self, claim_id: str, claim_commit: str, claim_receipt_digest: str, consumed_at: str) -> None:
        if self.activation is None:
            raise TaskError("INVALID_ACTIVATION")
        require_sha256(claim_receipt_digest, "INVALID_ACTIVATION_RECEIPT")
        receipt = {
            "schemaVersion": 1,
            "kind": "activation-receipt",
            "activationId": self.activation_id,
            "activationDigest": self.activation["activationDigest"],
            "claimId": claim_id,
            "claimCommit": claim_commit,
            "claimReceiptDigest": claim_receipt_digest,
            "consumedAt": consumed_at,
        }
        receipt["receiptDigest"] = digest_object(receipt)
        validate_activation_receipt(receipt)
        self.runtime.write_activation_receipt(receipt)

    def recover_consumption(self, task: dict[str, Any], offer: dict[str, Any], claim: dict[str, Any], receipt: dict[str, Any], consumed_at: str) -> dict[str, Any]:
        try:
            existing = self.runtime.read_activation_receipt(self.activation_id)
        except TaskError as error:
            if error.code != "ACTIVATION_RECEIPT_UNAVAILABLE":
                raise
        else:
            if existing["claimId"] != claim["claimId"] or existing["claimCommit"] != receipt["claimCommit"] or existing["claimReceiptDigest"] != receipt["receiptDigest"]:
                raise TaskError("INVALID_ACTIVATION_RECEIPT")
            self.runtime.write_activation_receipt(existing)
            return {"status": "activation_consumption_valid", "activationId": self.activation_id, "claimId": claim["claimId"]}
        activation = self.runtime.read_activation(self.activation_id)
        if (
            activation["providerDigest"] != self.provider_digest
            or activation["providerName"] != self.provider_name
            or activation["taskId"] != task["taskId"]
            or activation["repository"] != task["repository"]["identity"]
            or activation["taskBranch"] != task["repository"]["taskBranch"]
            or activation["offerId"] != claim["offerId"]
            or activation["envelopeId"] != claim["envelopeId"]
            or activation["agentId"] != claim["writerId"]
            or activation["threadDigest"] != claim["sessionDigest"]
            or activation["roleDigest"] != claim["roleDigest"]
            or activation["configDigest"] != claim["configDigest"]
            or activation["roleName"] != offer["roleName"]
            or activation["bundleDigest"] != offer["bundleDigest"]
            or activation["route"] != offer["route"]
            or activation["offerCreatedAt"] != offer["createdAt"]
            or activation["offerExpiresAt"] != offer["expiresAt"]
            or not _instant(activation["offerCreatedAt"], "RUNTIME_EVIDENCE_MISMATCH") <= _instant(activation["activatedAt"], "RUNTIME_EVIDENCE_MISMATCH") < _instant(activation["offerExpiresAt"], "RUNTIME_EVIDENCE_MISMATCH")
        ):
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        self.activation = activation
        self.consume(claim["claimId"], receipt["claimCommit"], receipt["receiptDigest"], consumed_at)
        return {"status": "activation_consumption_recovered", "activationId": self.activation_id, "claimId": claim["claimId"]}


class TestActivationTaskService(TaskService):
    """Test-only host seam; the installed base class remains fail-closed."""

    def _require_activation_authority(self) -> None:
        return
