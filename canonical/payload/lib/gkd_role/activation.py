"""Trusted host-observed role activation records for task claims."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256, require_string, require_utc
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore

from .roles import role_record


def validate_activation(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion", "kind", "activationId", "taskId", "repository", "taskBranch",
            "offerId", "envelopeId", "route", "agentId", "threadDigest", "roleName",
            "roleDigest", "configDigest", "bundleDigest", "effectiveModel",
            "effectiveReasoningEffort", "effectiveSandbox", "runtimeSeconds", "activatedAt",
            "evidenceClass", "providerDigest", "activationDigest",
        },
        "INVALID_ACTIVATION",
    )
    if value["schemaVersion"] != 1 or value["kind"] != "role-activation" or value["evidenceClass"] != "host-runtime-event":
        raise TaskError("INVALID_ACTIVATION")
    for field in ("taskId", "repository", "taskBranch", "route", "agentId", "roleName", "effectiveModel", "effectiveReasoningEffort", "effectiveSandbox"):
        require_string(value[field], "INVALID_ACTIVATION")
    for field in ("activationId", "offerId", "envelopeId", "threadDigest", "roleDigest", "configDigest", "bundleDigest", "providerDigest", "activationDigest"):
        require_sha256(value[field], "INVALID_ACTIVATION")
    if value["runtimeSeconds"] not in {3600, 43200}:
        raise TaskError("INVALID_ACTIVATION")
    require_utc(value["activatedAt"], "INVALID_ACTIVATION")
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


def record_activation(
    runtime: RuntimeStore,
    catalog: dict[str, Any],
    expected: dict[str, Any],
    observation: dict[str, Any],
    nonce: str,
) -> dict[str, Any]:
    require_keys(expected, {"taskId", "repository", "taskBranch", "offerId", "envelopeId", "route", "roleName", "roleDigest", "configDigest", "bundleDigest"}, "INVALID_ACTIVATION_REQUEST")
    require_keys(observation, {"evidenceClass", "agentId", "threadDigest", "model", "reasoningEffort", "sandbox", "runtimeSeconds", "activatedAt", "providerDigest"}, "INVALID_ACTIVATION_OBSERVATION")
    role = role_record(catalog, expected["roleName"])
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
    for field in ("threadDigest", "providerDigest"):
        require_sha256(observation[field], "INVALID_ACTIVATION_OBSERVATION")
    require_string(observation["agentId"], "INVALID_ACTIVATION_OBSERVATION")
    require_utc(observation["activatedAt"], "INVALID_ACTIVATION_OBSERVATION")
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
        "providerDigest": observation["providerDigest"],
    }
    value["activationDigest"] = digest_object(value)
    validate_activation(value)
    runtime.write_activation(value)
    return {"status": "activation_recorded", "activationId": activation_id, "activationDigest": value["activationDigest"]}


class ActivationEvidenceProvider:
    """Reads only the trusted machine-local activation store, never candidate files."""

    def __init__(self, runtime: RuntimeStore, activation_id: str, expected: dict[str, Any], provider_digest: str) -> None:
        require_sha256(activation_id, "INVALID_ACTIVATION")
        require_sha256(provider_digest, "INVALID_ACTIVATION")
        self.runtime = runtime
        self.activation_id = activation_id
        self.expected = deepcopy(expected)
        self.provider_digest = provider_digest
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
        required = {
            "taskId": activation["taskId"], "repository": activation["repository"], "taskBranch": activation["taskBranch"],
            "offerId": activation["offerId"], "envelopeId": activation["envelopeId"], "route": activation["route"],
            "roleName": activation["roleName"], "roleDigest": activation["roleDigest"], "configDigest": activation["configDigest"],
            "bundleDigest": activation["bundleDigest"],
        }
        if required != self.expected or activation["providerDigest"] != self.provider_digest:
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        for name in ("taskId", "repository", "taskBranch", "route", "roleDigest", "configDigest", "roleName", "bundleDigest", "offerId", "envelopeId"):
            if expected.get(name) != activation[name]:
                raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        self.activation = activation
        value = {
            "schemaVersion": 1,
            "provider": "trusted-activation",
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

    def recover_consumption(self, task: dict[str, Any], claim: dict[str, Any], receipt: dict[str, Any], consumed_at: str) -> dict[str, Any]:
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
        expected = self.expected
        if (
            activation["providerDigest"] != self.provider_digest
            or activation["taskId"] != task["taskId"]
            or activation["repository"] != task["repository"]["identity"]
            or activation["taskBranch"] != task["repository"]["taskBranch"]
            or activation["offerId"] != claim["offerId"]
            or activation["agentId"] != claim["writerId"]
            or activation["threadDigest"] != claim["sessionDigest"]
            or activation["roleDigest"] != claim["roleDigest"]
            or activation["configDigest"] != claim["configDigest"]
            or any(activation[name] != expected[name] for name in expected)
        ):
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        self.activation = activation
        self.consume(claim["claimId"], receipt["claimCommit"], receipt["receiptDigest"], consumed_at)
        return {"status": "activation_consumption_recovered", "activationId": self.activation_id, "claimId": claim["claimId"]}
