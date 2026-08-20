"""Trusted-main orchestration from one direct spawn result to an exact claim."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from gkd_bundle import BundleError, verify_bundle_root
from gkd_task.canonical import (
    SystemClock,
    SystemNonce,
    digest_object,
    require_keys,
    require_sha256,
    require_string,
    require_utc,
)
from gkd_task.errors import TaskError
from gkd_task.model import validate_runtime_evidence
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from .activation import TrustedMainActivationAuthority, _instant
from .roles import role_catalog, role_record
from .routing import validate_route_decision


SPAWN_KEYS = {
    "schemaVersion", "status", "spawnCount", "taskName", "agentType", "forkTurns",
    "agentId", "threadDigest", "roleName", "roleDigest", "configDigest",
    "executionBundleDigest", "routeDecisionDigest", "model", "reasoningEffort",
    "sandbox", "runtimeSeconds", "activatedAt", "fallbackAttempted",
}

TERMINAL_RESULT_KEYS = {
    "schemaVersion", "status", "taskId", "repository", "taskBranch", "taskName",
    "offerId", "claimId", "agentId", "sessionDigest", "roleName", "roleDigest", "configDigest",
    "route",
    "executionBundleDigest", "routeDecisionDigest", "terminalAt",
}

HOST_TASK_NAME_PREFIX = "gkd_executor_"
HOST_TASK_NAME_MAX = 128


def _task_name(task_id: str, offer_id: str, epoch: int) -> str:
    require_string(task_id, "INVALID_AUTOMATIC_TASK")
    require_sha256(offer_id, "INVALID_AUTOMATIC_TASK")
    if not isinstance(epoch, int) or epoch < 0:
        raise TaskError("INVALID_AUTOMATIC_TASK")
    normalized = "".join(character.lower() if character.isalnum() else "_" for character in task_id).strip("_")
    if not normalized:
        raise TaskError("INVALID_AUTOMATIC_TASK")
    attempt_digest = digest_object({"taskId": task_id, "offerId": offer_id, "epoch": epoch})
    prefix_limit = HOST_TASK_NAME_MAX - len(HOST_TASK_NAME_PREFIX) - 1 - len(attempt_digest)
    if prefix_limit < 1:
        raise TaskError("INVALID_AUTOMATIC_TASK")
    normalized = normalized[:prefix_limit].rstrip("_")
    if not normalized:
        raise TaskError("INVALID_AUTOMATIC_TASK")
    return f"{HOST_TASK_NAME_PREFIX}{normalized}_{attempt_digest}"


def _validate_terminal_result(value: dict[str, Any]) -> None:
    require_keys(value, TERMINAL_RESULT_KEYS, "INVALID_TERMINAL_RESULT")
    if value["schemaVersion"] != 1 or value["status"] not in {"terminal", "missing"}:
        raise TaskError("INVALID_TERMINAL_RESULT")
    for field in ("taskId", "repository", "taskBranch", "taskName", "agentId", "roleName", "route"):
        require_string(value[field], "INVALID_TERMINAL_RESULT")
    for field in (
        "offerId", "claimId", "sessionDigest", "roleDigest", "configDigest", "executionBundleDigest", "routeDecisionDigest",
    ):
        require_sha256(value[field], "INVALID_TERMINAL_RESULT")
    require_utc(value["terminalAt"], "INVALID_TERMINAL_RESULT")
    if (
        value["roleName"] != "gkd_executor"
        or len(value["taskName"]) > HOST_TASK_NAME_MAX
        or not all(character in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in value["taskName"])
    ):
        raise TaskError("INVALID_TERMINAL_RESULT")


class _TerminalEvidenceProvider:
    """One in-memory terminal observation owned by the trusted bridge."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = deepcopy(result)
        self.consumed = False

    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]:
        if purpose != "reclaim" or self.consumed:
            raise TaskError("RUNTIME_EVIDENCE_UNAVAILABLE")
        if (
            self.result["agentId"] != expected["writerId"]
            or self.result["sessionDigest"] != expected["sessionDigest"]
            or self.result["roleDigest"] != expected["roleDigest"]
            or self.result["configDigest"] != expected["configDigest"]
        ):
            raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
        self.consumed = True
        value = {
            "schemaVersion": 1,
            "provider": "codex-host-runtime",
            "writerId": self.result["agentId"],
            "sessionDigest": self.result["sessionDigest"],
            "roleDigest": self.result["roleDigest"],
            "configDigest": self.result["configDigest"],
            "route": self.result["route"],
            "status": self.result["status"],
            "observedAt": self.result["terminalAt"],
        }
        value["evidenceDigest"] = digest_object(value)
        validate_runtime_evidence(value)
        return value


def validate_spawn_result(facts: dict[str, Any], expected: dict[str, Any]) -> None:
    require_keys(facts, SPAWN_KEYS, "INVALID_SPAWN_RESULT")
    for field in ("taskName", "agentType", "forkTurns", "agentId", "roleName", "model", "reasoningEffort", "sandbox"):
        require_string(facts[field], "INVALID_SPAWN_RESULT")
    for field in ("threadDigest", "roleDigest", "configDigest", "executionBundleDigest", "routeDecisionDigest"):
        require_sha256(facts[field], "INVALID_SPAWN_RESULT")
    require_utc(facts["activatedAt"], "INVALID_SPAWN_RESULT")
    if (
        facts["schemaVersion"] != 1
        or facts["status"] != "spawned"
        or facts["spawnCount"] != 1
        or facts["taskName"] != expected["spawnRequest"]["taskName"]
        or facts["agentType"] != "gkd_executor"
        or facts["forkTurns"] != "none"
        or facts["roleName"] != "gkd_executor"
        or facts["fallbackAttempted"] is not False
        or facts["roleDigest"] != expected["roleDigest"]
        or facts["configDigest"] != expected["configDigest"]
        or facts["executionBundleDigest"] != expected["executionBundleDigest"]
        or facts["routeDecisionDigest"] != expected["routeDecisionDigest"]
        or facts["model"] != expected["role"]["model"]
        or facts["reasoningEffort"] != expected["role"]["reasoningEffort"]
        or facts["sandbox"] != expected["role"]["sandbox"]
        or facts["runtimeSeconds"] != expected["role"]["runtimeSeconds"]
    ):
        raise TaskError("SPAWN_RESULT_MISMATCH")


class TrustedMainRuntimeBridge:
    """Supported trusted-main bridge; candidate task CLI remains fail-closed."""

    def __init__(
        self,
        candidate_root: Any,
        task_path: str,
        runtime: RuntimeStore,
        bundle_root: Any,
        execution_bundle_digest: str,
        clock: Any | None = None,
        nonce: Any | None = None,
        failure_hook: Any | None = None,
    ) -> None:
        require_sha256(execution_bundle_digest, "INVALID_BUNDLE_DIGEST")
        self.candidate_root = candidate_root
        self.task_path = task_path
        self.runtime = runtime
        self.bundle_root = Path(bundle_root)
        self.execution_bundle_digest = execution_bundle_digest
        self.clock = clock or SystemClock()
        self.nonce = nonce or SystemNonce()
        self.failure_hook = failure_hook
        self._verified_catalog()

    def _verified_catalog(self) -> dict[str, Any]:
        try:
            verified = verify_bundle_root(self.bundle_root)
        except BundleError:
            raise TaskError("BUNDLE_CONTENT_MISMATCH") from None
        if verified["contentDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        return role_catalog(self.bundle_root, self.execution_bundle_digest)

    def _service(self, provider: Any | None = None) -> TaskService:
        return TaskService(
            self.candidate_root,
            self.task_path,
            runtime=self.runtime,
            clock=self.clock,
            nonce=self.nonce,
            evidence_provider=provider,
            failure_hook=self.failure_hook,
        )

    def prepare(
        self,
        expected_head: str,
        expected_revision: int,
        route_decision: dict[str, Any],
        expires_at: str,
    ) -> dict[str, Any]:
        catalog = self._verified_catalog()
        validate_route_decision(route_decision, require_automatic=True)
        if route_decision["bundleDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        role = role_record(catalog, "gkd_executor")
        service = self._service()
        service.offer(
            expected_head,
            expected_revision,
            "automatic",
            role["roleDigest"],
            role["configDigest"],
            expires_at,
            "gkd_executor",
            self.execution_bundle_digest,
            route_decision,
        )
        handoff = service.handoff()
        context = service.automatic_claim_context(handoff["envelopeId"])
        return {
            "status": "automatic_spawn_ready",
            "taskId": context["taskId"],
            "offerId": context["offerId"],
            "envelopeId": context["envelopeId"],
            "executionBundleDigest": context["bundleDigest"],
            "routeDecisionDigest": context["routeDecisionDigest"],
            "roleName": context["roleName"],
            "roleDigest": context["roleDigest"],
            "configDigest": context["configDigest"],
            "role": {
                "model": role["model"],
                "reasoningEffort": role["modelReasoningEffort"],
                "sandbox": role["sandboxMode"],
                "runtimeSeconds": role["runtimeSeconds"],
            },
            "spawnRequest": {
                "agentType": "gkd_executor",
                "taskName": _task_name(context["taskId"], context["offerId"], context["epoch"]),
                "forkTurns": "none",
            },
        }

    def claim(
        self,
        expected_head: str,
        expected_revision: int,
        envelope_id: str,
        spawn_result: dict[str, Any],
        activation_nonce: str,
    ) -> dict[str, Any]:
        service = self._service()
        status = service.status()
        if status["head"] != expected_head:
            raise TaskError("CAS_HEAD_MISMATCH")
        if status["revision"] != expected_revision:
            raise TaskError("CAS_REVISION_MISMATCH")
        context = service.automatic_claim_context(envelope_id)
        if context["bundleDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        catalog = self._verified_catalog()
        role = role_record(catalog, "gkd_executor")
        expected_spawn = {
            "executionBundleDigest": context["bundleDigest"],
            "routeDecisionDigest": context["routeDecisionDigest"],
            "roleDigest": context["roleDigest"],
            "configDigest": context["configDigest"],
            "role": {
                "model": role["model"],
                "reasoningEffort": role["modelReasoningEffort"],
                "sandbox": role["sandboxMode"],
                "runtimeSeconds": role["runtimeSeconds"],
            },
            "spawnRequest": {
                "agentType": "gkd_executor",
                "taskName": _task_name(context["taskId"], context["offerId"], context["epoch"]),
                "forkTurns": "none",
            },
        }
        validate_spawn_result(spawn_result, expected_spawn)
        activation_expected = {
            key: context[key]
            for key in (
                "taskId", "repository", "taskBranch", "offerId", "envelopeId", "route",
                "roleName", "roleDigest", "configDigest", "bundleDigest",
                "routeDecisionDigest", "offerCreatedAt", "offerExpiresAt",
            )
        }
        authority = TrustedMainActivationAuthority(self.runtime, catalog)
        activation = authority.build(
            activation_expected,
            {
                "evidenceClass": "host-runtime-event",
                "agentId": spawn_result["agentId"],
                "threadDigest": spawn_result["threadDigest"],
                "model": spawn_result["model"],
                "reasoningEffort": spawn_result["reasoningEffort"],
                "sandbox": spawn_result["sandbox"],
                "runtimeSeconds": spawn_result["runtimeSeconds"],
                "activatedAt": spawn_result["activatedAt"],
            },
            activation_nonce,
        )
        provider = authority.provider(activation["activationId"], activation)
        result = self._service(provider).claim(expected_head, expected_revision, envelope_id)
        return {
            "status": result["status"],
            "revision": result["revision"],
            "head": result["head"],
            "claimId": result["claimId"],
            "offerId": context["offerId"],
            "envelopeId": envelope_id,
            "executionBundleDigest": context["bundleDigest"],
            "routeDecisionDigest": context["routeDecisionDigest"],
            "roleName": context["roleName"],
            "roleDigest": context["roleDigest"],
            "configDigest": context["configDigest"],
        }

    def reclaim_terminal(
        self,
        expected_head: str,
        expected_revision: int,
        terminal_result: dict[str, Any],
        reason: str = "host-terminal",
    ) -> dict[str, Any]:
        """Reclaim one exact implementing claim from a normalized host terminal fact."""

        _validate_terminal_result(terminal_result)
        service = self._service()
        status = service.status()
        if status["head"] != expected_head:
            raise TaskError("CAS_HEAD_MISMATCH")
        if status["revision"] != expected_revision:
            raise TaskError("CAS_REVISION_MISMATCH")
        state = service._state()
        claim = state["lifecycle"]["claim"]
        if state["lifecycle"]["phase"] != "implementing" or claim is None:
            raise TaskError("INVALID_TRANSITION")
        offer = service._offer()
        expected_name = _task_name(state["taskId"], offer["offerId"], offer["epoch"])
        if (
            offer["status"] != "consumed"
            or offer["route"] != "automatic"
            or terminal_result["taskId"] != state["taskId"]
            or terminal_result["repository"] != state["repository"]["identity"]
            or terminal_result["taskBranch"] != state["repository"]["taskBranch"]
            or terminal_result["offerId"] != claim["offerId"]
            or terminal_result["claimId"] != claim["claimId"]
            or terminal_result["taskName"] != expected_name
            or terminal_result["agentId"] != claim["writerId"]
            or terminal_result["sessionDigest"] != claim["sessionDigest"]
            or terminal_result["roleName"] != offer["roleName"]
            or terminal_result["roleDigest"] != claim["roleDigest"]
            or terminal_result["configDigest"] != claim["configDigest"]
            or terminal_result["executionBundleDigest"] != offer["bundleDigest"]
            or terminal_result["routeDecisionDigest"] != claim["routeDecisionDigest"]
        ):
            raise TaskError("TERMINAL_RESULT_MISMATCH")
        claimed_at = _instant(claim["claimedAt"], "TERMINAL_RESULT_MISMATCH")
        terminal_at = _instant(terminal_result["terminalAt"], "TERMINAL_RESULT_MISMATCH")
        now = _instant(self.clock.now(), "TERMINAL_RESULT_MISMATCH")
        if terminal_at < claimed_at or terminal_at > now:
            raise TaskError("TERMINAL_RESULT_MISMATCH")
        provider = _TerminalEvidenceProvider(terminal_result)
        return self._service(provider).reclaim(expected_head, expected_revision, reason)

    def recover(self) -> dict[str, Any]:
        catalog = self._verified_catalog()
        service = self._service()
        transaction = service.recover()
        if transaction["status"] == "recovered_rolled_back":
            return transaction
        context = service.automatic_recovery_context()
        if context["executionBundleDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        authority = TrustedMainActivationAuthority(self.runtime, catalog)
        return self._service(authority.provider(context["activationId"])).recover_activation()
