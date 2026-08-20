"""Trusted-main orchestration from one direct spawn result to an exact claim."""

from __future__ import annotations

from typing import Any

from gkd_task.canonical import SystemClock, SystemNonce, require_keys, require_sha256, require_string, require_utc
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from .activation import TrustedMainActivationAuthority
from .roles import role_catalog, role_record
from .routing import validate_route_decision


SPAWN_KEYS = {
    "schemaVersion", "status", "spawnCount", "taskName", "agentType", "forkTurns",
    "agentId", "threadDigest", "roleName", "roleDigest", "configDigest",
    "executionBundleDigest", "routeDecisionDigest", "model", "reasoningEffort",
    "sandbox", "runtimeSeconds", "activatedAt", "fallbackAttempted",
}


def _task_name(task_id: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "_" for character in task_id).strip("_")
    if not normalized:
        raise TaskError("INVALID_AUTOMATIC_TASK")
    return f"gkd_executor_{normalized}"


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
        self.catalog = role_catalog(bundle_root, execution_bundle_digest)
        self.execution_bundle_digest = execution_bundle_digest
        self.clock = clock or SystemClock()
        self.nonce = nonce or SystemNonce()
        self.failure_hook = failure_hook

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
        validate_route_decision(route_decision, require_automatic=True)
        if route_decision["bundleDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        role = role_record(self.catalog, "gkd_executor")
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
                "taskName": _task_name(context["taskId"]),
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
        role = role_record(self.catalog, "gkd_executor")
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
                "taskName": _task_name(context["taskId"]),
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
        authority = TrustedMainActivationAuthority(self.runtime, self.catalog)
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

    def recover(self) -> dict[str, Any]:
        service = self._service()
        transaction = service.recover()
        if transaction["status"] == "recovered_rolled_back":
            return transaction
        context = service.automatic_recovery_context()
        if context["executionBundleDigest"] != self.execution_bundle_digest:
            raise TaskError("EXECUTION_BUNDLE_MISMATCH")
        authority = TrustedMainActivationAuthority(self.runtime, self.catalog)
        return self._service(authority.provider(context["activationId"])).recover_activation()
