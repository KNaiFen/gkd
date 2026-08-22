"""Trusted host-observed role activation records for task claims."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, require_keys, require_sha1, require_sha256, require_string, require_utc
from gkd_task.errors import TaskError
from .roles import ACTIVATION_PROVIDER, activation_provider, role_record


HOST_ACKNOWLEDGEMENT_EVIDENCE = "host-spawn-acknowledgement"


def _instant(value: str, code: str) -> datetime:
    require_utc(value, code)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise TaskError(code) from None


def validate_activation(value: dict[str, Any]) -> None:
    legacy_keys = {
        "schemaVersion", "kind", "activationId", "taskId", "repository", "taskBranch",
        "offerId", "envelopeId", "route", "agentId", "threadDigest", "roleName",
        "roleDigest", "configDigest", "bundleDigest", "effectiveModel",
        "effectiveReasoningEffort", "effectiveSandbox", "runtimeSeconds", "activatedAt",
        "offerCreatedAt", "offerExpiresAt", "evidenceClass", "providerName", "providerDigest", "activationDigest",
    }
    acknowledgement_keys = {
        "schemaVersion", "kind", "activationId", "taskId", "repository", "taskBranch",
        "offerId", "envelopeId", "route", "executorTaskName", "executorAttemptDigest", "roleName",
        "roleDigest", "configDigest", "bundleDigest", "configuredModel", "configuredReasoningEffort",
        "configuredSandbox", "runtimeSeconds", "acknowledgedAt", "offerCreatedAt", "offerExpiresAt",
        "evidenceClass", "providerName", "providerDigest", "activationDigest",
    }
    if "routeDecisionDigest" in value:
        legacy_keys.add("routeDecisionDigest")
        acknowledgement_keys.add("routeDecisionDigest")
    if value.get("schemaVersion") == 1:
        require_keys(value, legacy_keys, "INVALID_ACTIVATION")
        if value["kind"] != "role-activation" or value["evidenceClass"] != "host-runtime-event":
            raise TaskError("INVALID_ACTIVATION")
        for field in ("taskId", "repository", "taskBranch", "route", "agentId", "roleName", "effectiveModel", "effectiveReasoningEffort", "effectiveSandbox", "providerName"):
            require_string(value[field], "INVALID_ACTIVATION")
        for field in ("activationId", "offerId", "envelopeId", "threadDigest", "roleDigest", "configDigest", "bundleDigest", "providerDigest", "activationDigest"):
            require_sha256(value[field], "INVALID_ACTIVATION")
        for field in ("offerCreatedAt", "offerExpiresAt", "activatedAt"):
            _instant(value[field], "INVALID_ACTIVATION")
        observed_at = value["activatedAt"]
    elif value.get("schemaVersion") == 2:
        require_keys(value, acknowledgement_keys, "INVALID_ACTIVATION")
        if value["kind"] != "role-activation" or value["evidenceClass"] != HOST_ACKNOWLEDGEMENT_EVIDENCE:
            raise TaskError("INVALID_ACTIVATION")
        for field in (
            "taskId", "repository", "taskBranch", "route", "executorTaskName", "roleName",
            "configuredModel", "configuredReasoningEffort", "configuredSandbox", "providerName",
        ):
            require_string(value[field], "INVALID_ACTIVATION")
        for field in (
            "activationId", "offerId", "envelopeId", "executorAttemptDigest", "roleDigest", "configDigest",
            "bundleDigest", "providerDigest", "activationDigest",
        ):
            require_sha256(value[field], "INVALID_ACTIVATION")
        for field in ("offerCreatedAt", "offerExpiresAt", "acknowledgedAt"):
            _instant(value[field], "INVALID_ACTIVATION")
        observed_at = value["acknowledgedAt"]
    else:
        raise TaskError("INVALID_ACTIVATION")
    if "routeDecisionDigest" in value:
        require_sha256(value["routeDecisionDigest"], "INVALID_ACTIVATION")
    if value["runtimeSeconds"] not in {3600, 43200}:
        raise TaskError("INVALID_ACTIVATION")
    if value["providerName"] != ACTIVATION_PROVIDER["name"] or value["providerDigest"] != digest_object(ACTIVATION_PROVIDER):
        raise TaskError("INVALID_ACTIVATION")
    if not _instant(value["offerCreatedAt"], "INVALID_ACTIVATION") <= _instant(observed_at, "INVALID_ACTIVATION") < _instant(value["offerExpiresAt"], "INVALID_ACTIVATION"):
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
    observed_at = activation["acknowledgedAt"] if activation["schemaVersion"] == 2 else activation["activatedAt"]
    if not _instant(activation["offerCreatedAt"], "RUNTIME_EVIDENCE_MISMATCH") <= _instant(observed_at, "RUNTIME_EVIDENCE_MISMATCH") < _instant(activation["offerExpiresAt"], "RUNTIME_EVIDENCE_MISMATCH"):
        raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
    names = ["taskId", "repository", "taskBranch", "route", "roleDigest", "configDigest", "roleName", "bundleDigest", "offerId", "envelopeId", "offerCreatedAt", "offerExpiresAt"]
    if "routeDecisionDigest" in expected:
        names.append("routeDecisionDigest")
    for name in names:
        if expected.get(name) != activation.get(name):
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")


class TrustedMainActivationAuthority:
    """Main-owned workflow boundary that records verified host activation facts."""

    def __init__(self, runtime: Any, catalog: dict[str, Any]) -> None:
        self.runtime = runtime
        self.catalog = deepcopy(catalog)
        provider = activation_provider(catalog)
        self.provider_name = provider["name"]
        self.provider_digest = digest_object(provider)

    def build(
        self,
        expected: dict[str, Any],
        host_facts: dict[str, Any],
        nonce: str,
    ) -> dict[str, Any]:
        if host_facts.get("evidenceClass") == HOST_ACKNOWLEDGEMENT_EVIDENCE:
            return self._build_acknowledgement(expected, host_facts, nonce)
        expected_keys = {"taskId", "repository", "taskBranch", "offerId", "envelopeId", "route", "roleName", "roleDigest", "configDigest", "bundleDigest", "offerCreatedAt", "offerExpiresAt"}
        if "routeDecisionDigest" in expected:
            expected_keys.add("routeDecisionDigest")
            require_sha256(expected["routeDecisionDigest"], "INVALID_ACTIVATION_REQUEST")
        require_keys(expected, expected_keys, "INVALID_ACTIVATION_REQUEST")
        require_keys(host_facts, {"evidenceClass", "agentId", "threadDigest", "model", "reasoningEffort", "sandbox", "runtimeSeconds", "activatedAt"}, "INVALID_ACTIVATION_OBSERVATION")
        role = role_record(self.catalog, expected["roleName"])
        if (
            host_facts["evidenceClass"] != "host-runtime-event"
            or expected["bundleDigest"] != self.catalog["bundleDigest"]
            or expected["roleDigest"] != role["roleDigest"]
            or expected["configDigest"] != role["configDigest"]
            or host_facts["model"] != role["model"]
            or host_facts["reasoningEffort"] != role["modelReasoningEffort"]
            or host_facts["sandbox"] != role["sandboxMode"]
            or host_facts["runtimeSeconds"] != role["runtimeSeconds"]
        ):
            raise TaskError("ACTIVATION_OBSERVATION_MISMATCH")
        require_sha256(host_facts["threadDigest"], "INVALID_ACTIVATION_OBSERVATION")
        require_string(host_facts["agentId"], "INVALID_ACTIVATION_OBSERVATION")
        if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
            raise TaskError("INVALID_ACTIVATION_REQUEST")
        if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") <= _instant(host_facts["activatedAt"], "INVALID_ACTIVATION_OBSERVATION") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
            raise TaskError("ACTIVATION_OUTSIDE_OFFER_WINDOW")
        activation_id = digest_object({"expected": expected, "hostFacts": host_facts, "nonce": require_string(nonce, "INVALID_ACTIVATION_REQUEST")})
        value = {
            "schemaVersion": 1,
            "kind": "role-activation",
            "activationId": activation_id,
            **expected,
            "agentId": host_facts["agentId"],
            "threadDigest": host_facts["threadDigest"],
            "effectiveModel": host_facts["model"],
            "effectiveReasoningEffort": host_facts["reasoningEffort"],
            "effectiveSandbox": host_facts["sandbox"],
            "runtimeSeconds": host_facts["runtimeSeconds"],
            "activatedAt": host_facts["activatedAt"],
            "evidenceClass": host_facts["evidenceClass"],
            "providerName": self.provider_name,
            "providerDigest": self.provider_digest,
        }
        value["activationDigest"] = digest_object(value)
        validate_activation(value)
        return value

    def _build_acknowledgement(
        self,
        expected: dict[str, Any],
        host_facts: dict[str, Any],
        nonce: str,
    ) -> dict[str, Any]:
        expected_keys = {
            "taskId", "repository", "taskBranch", "offerId", "envelopeId", "route", "roleName",
            "roleDigest", "configDigest", "bundleDigest", "offerCreatedAt", "offerExpiresAt", "executorTaskName",
        }
        if "routeDecisionDigest" in expected:
            expected_keys.add("routeDecisionDigest")
            require_sha256(expected["routeDecisionDigest"], "INVALID_ACTIVATION_REQUEST")
        require_keys(expected, expected_keys, "INVALID_ACTIVATION_REQUEST")
        require_keys(host_facts, {"evidenceClass", "taskName", "acknowledgedAt"}, "INVALID_ACTIVATION_OBSERVATION")
        role = role_record(self.catalog, expected["roleName"])
        if (
            host_facts["evidenceClass"] != HOST_ACKNOWLEDGEMENT_EVIDENCE
            or expected["bundleDigest"] != self.catalog["bundleDigest"]
            or expected["roleDigest"] != role["roleDigest"]
            or expected["configDigest"] != role["configDigest"]
            or host_facts["taskName"] != expected["executorTaskName"]
        ):
            raise TaskError("ACTIVATION_OBSERVATION_MISMATCH")
        require_string(host_facts["taskName"], "INVALID_ACTIVATION_OBSERVATION")
        if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
            raise TaskError("INVALID_ACTIVATION_REQUEST")
        if not _instant(expected["offerCreatedAt"], "INVALID_ACTIVATION_REQUEST") <= _instant(host_facts["acknowledgedAt"], "INVALID_ACTIVATION_OBSERVATION") < _instant(expected["offerExpiresAt"], "INVALID_ACTIVATION_REQUEST"):
            raise TaskError("ACTIVATION_OUTSIDE_OFFER_WINDOW")
        attempt = digest_object(
            {
                "contract": "host-spawn-acknowledgement-v1",
                "taskId": expected["taskId"],
                "offerId": expected["offerId"],
                "envelopeId": expected["envelopeId"],
                "taskName": host_facts["taskName"],
                "bundleDigest": expected["bundleDigest"],
                "routeDecisionDigest": expected.get("routeDecisionDigest"),
            }
        )
        activation_id = digest_object({"expected": expected, "hostFacts": host_facts, "nonce": require_string(nonce, "INVALID_ACTIVATION_REQUEST")})
        value = {
            "schemaVersion": 2,
            "kind": "role-activation",
            "activationId": activation_id,
            **expected,
            "executorAttemptDigest": attempt,
            "configuredModel": role["model"],
            "configuredReasoningEffort": role["modelReasoningEffort"],
            "configuredSandbox": role["sandboxMode"],
            "runtimeSeconds": role["runtimeSeconds"],
            "acknowledgedAt": host_facts["acknowledgedAt"],
            "evidenceClass": HOST_ACKNOWLEDGEMENT_EVIDENCE,
            "providerName": self.provider_name,
            "providerDigest": self.provider_digest,
        }
        value["activationDigest"] = digest_object(value)
        validate_activation(value)
        return value

    def record(
        self,
        expected: dict[str, Any],
        host_facts: dict[str, Any],
        nonce: str,
    ) -> dict[str, Any]:
        value = self.build(expected, host_facts, nonce)
        atomic_write(self.runtime._path("activations", value["activationId"]), canonical_bytes(value), mode=0o600)
        return {"status": "activation_recorded", "activationId": value["activationId"], "activationDigest": value["activationDigest"]}

    def provider(self, activation_id: str, pending_activation: dict[str, Any] | None = None) -> "TrustedActivationEvidenceProvider":
        return TrustedActivationEvidenceProvider(self.runtime, activation_id, self.catalog, pending_activation)


class TrustedActivationEvidenceProvider:
    """Provider object passed by trusted main to the task service."""

    trusted_main_owned = True

    def __init__(self, runtime: Any, activation_id: str, catalog: dict[str, Any], pending_activation: dict[str, Any] | None = None) -> None:
        require_sha256(activation_id, "INVALID_ACTIVATION")
        self.runtime = runtime
        self.activation_id = activation_id
        provider = activation_provider(catalog)
        self.provider_name = provider["name"]
        self.provider_digest = digest_object(provider)
        self.activation: dict[str, Any] | None = None
        self.pending_activation = deepcopy(pending_activation) if pending_activation is not None else None

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
        activation = self.pending_activation or self.runtime.read_activation(self.activation_id)
        if activation["activationId"] != self.activation_id:
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        validate_activation(activation)
        validate_activation_binding(activation, expected)
        self.activation = activation
        if activation["schemaVersion"] == 2:
            writer_id = activation["executorTaskName"]
            session_digest = activation["executorAttemptDigest"]
            observed_at = activation["acknowledgedAt"]
        else:
            writer_id = activation["agentId"]
            session_digest = activation["threadDigest"]
            observed_at = activation["activatedAt"]
        value = {
            "schemaVersion": 1,
            "provider": activation["providerName"],
            "writerId": writer_id,
            "sessionDigest": session_digest,
            "roleDigest": activation["roleDigest"],
            "configDigest": activation["configDigest"],
            "route": activation["route"],
            "status": "active",
            "observedAt": observed_at,
        }
        value["evidenceDigest"] = digest_object(value)
        return value

    def transaction_files(self) -> dict[str, bytes]:
        if self.pending_activation is None:
            return {}
        return {
            f"activations/{self.activation_id}.json": canonical_bytes(self.pending_activation),
        }

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
        validate_activation_binding(
            activation,
            {
                "taskId": task["taskId"],
                "repository": task["repository"]["identity"],
                "taskBranch": task["repository"]["taskBranch"],
                "offerId": claim["offerId"],
                "envelopeId": claim["envelopeId"],
                "route": offer["route"],
                "roleName": offer["roleName"],
                "roleDigest": claim["roleDigest"],
                "configDigest": claim["configDigest"],
                "bundleDigest": offer["bundleDigest"],
                "offerCreatedAt": offer["createdAt"],
                "offerExpiresAt": offer["expiresAt"],
                **({"routeDecisionDigest": offer["routeDecisionDigest"]} if offer.get("routeDecisionDigest") else {}),
            },
        )
        if activation["schemaVersion"] == 2:
            identity_matches = (
                activation["executorTaskName"] == claim["writerId"]
                and activation["executorAttemptDigest"] == claim["sessionDigest"]
                and claim.get("executorTaskName") == activation["executorTaskName"]
                and claim.get("executorAttemptDigest") == activation["executorAttemptDigest"]
            )
        else:
            identity_matches = activation["agentId"] == claim["writerId"] and activation["threadDigest"] == claim["sessionDigest"]
        if activation["providerDigest"] != self.provider_digest or activation["providerName"] != self.provider_name or not identity_matches:
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        self.activation = activation
        self.consume(claim["claimId"], receipt["claimCommit"], receipt["receiptDigest"], consumed_at)
        return {"status": "activation_consumption_recovered", "activationId": self.activation_id, "claimId": claim["claimId"]}
