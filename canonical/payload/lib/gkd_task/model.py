"""Strict durable task, offer, authorization, and evidence models."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from .canonical import (
    canonical_bytes,
    digest_object,
    read_canonical_json,
    relative_path,
    require_keys,
    require_sha1,
    require_sha256,
    require_string,
    require_utc,
    sha256_bytes,
)
from .documents import inspect_tracked_package
from .errors import TaskError


TASK_SCHEMA_VERSION = 1
PHASES = {
    "planning",
    "awaiting_claim",
    "implementing",
    "delivered",
    "accepted",
    "completed",
}
ACTION_MODES = {"implement_only", "implement_and_merge_on_acceptance"}
KNOWN_ACTIONS = {
    "commit",
    "push",
    "pr_update",
    "ci_repair",
    "ready_for_review",
    "conditional_merge",
}
EVENT_TYPES = {
    "bootstrap",
    "requirements_ready",
    "plan_proposed",
    "plan_approved",
    "authorized",
    "offer_created",
    "claimed",
    "revoked",
    "reclaimed",
    "blocked",
    "resumed",
    "delivered",
    "accepted",
    "completed",
    "migrated_v1",
}


def _repository_record(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TASK_STATE")
    require_keys(value, {"identity", "baseBranch", "baseSha", "taskBranch", "taskPath"}, "INVALID_TASK_STATE")
    require_string(value["identity"], "INVALID_TASK_STATE")
    require_string(value["baseBranch"], "INVALID_TASK_STATE")
    require_sha1(value["baseSha"], "INVALID_TASK_STATE")
    require_string(value["taskBranch"], "INVALID_TASK_STATE")
    relative_path(value["taskPath"], "INVALID_TASK_STATE")


def _documents_record(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TASK_STATE")
    require_keys(value, {"requirements", "plan", "implementation"}, "INVALID_TASK_STATE")
    expected = {
        "requirements": {"path", "version", "documentRevision", "digest", "status"},
        "plan": {"path", "version", "documentRevision", "digest", "materialDigest", "status"},
        "implementation": {"path", "version", "documentRevision", "digest"},
    }
    for name, keys in expected.items():
        record = value[name]
        if not isinstance(record, dict):
            raise TaskError("INVALID_TASK_STATE")
        require_keys(record, keys, "INVALID_TASK_STATE")
        relative_path(record["path"], "INVALID_TASK_STATE")
        if not isinstance(record["version"], int) or record["version"] < 1:
            raise TaskError("INVALID_TASK_STATE")
        if not isinstance(record["documentRevision"], int) or record["documentRevision"] < 1:
            raise TaskError("INVALID_TASK_STATE")
        require_sha256(record["digest"], "INVALID_TASK_STATE")
    if value["requirements"]["status"] not in {"draft", "ready"}:
        raise TaskError("INVALID_TASK_STATE")
    if value["plan"]["status"] not in {"proposed", "approved"}:
        raise TaskError("INVALID_TASK_STATE")
    require_sha256(value["plan"]["materialDigest"], "INVALID_TASK_STATE")


def _approval_record(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise TaskError("INVALID_TASK_STATE")
    require_keys(value, {"planVersion", "materialDigest", "decisionRef", "approvedAt"}, "INVALID_TASK_STATE")
    if not isinstance(value["planVersion"], int) or value["planVersion"] < 1:
        raise TaskError("INVALID_TASK_STATE")
    require_sha256(value["materialDigest"], "INVALID_TASK_STATE")
    require_string(value["decisionRef"], "INVALID_TASK_STATE")
    require_utc(value["approvedAt"], "INVALID_TASK_STATE")


def _implementation_authorization(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise TaskError("INVALID_TASK_STATE")
    require_keys(value, {"planVersion", "materialDigest", "decisionRef", "authorizedAt"}, "INVALID_TASK_STATE")
    if not isinstance(value["planVersion"], int) or value["planVersion"] < 1:
        raise TaskError("INVALID_TASK_STATE")
    require_sha256(value["materialDigest"], "INVALID_TASK_STATE")
    require_string(value["decisionRef"], "INVALID_TASK_STATE")
    require_utc(value["authorizedAt"], "INVALID_TASK_STATE")


def _lifecycle_record(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TASK_STATE")
    require_keys(
        value,
        {"phase", "epoch", "blocked", "writer", "offer", "claim", "retiredClaims", "delivery", "acceptance", "completion"},
        "INVALID_TASK_STATE",
    )
    if value["phase"] not in PHASES or not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_TASK_STATE")
    if value["blocked"] is not None:
        block = value["blocked"]
        if not isinstance(block, dict):
            raise TaskError("INVALID_TASK_STATE")
        require_keys(block, {"reason", "owner", "blockedAt"}, "INVALID_TASK_STATE")
        require_string(block["reason"], "INVALID_TASK_STATE")
        require_string(block["owner"], "INVALID_TASK_STATE")
        require_utc(block["blockedAt"], "INVALID_TASK_STATE")
    for name in ("writer", "offer", "claim", "delivery", "acceptance", "completion"):
        if value[name] is not None and not isinstance(value[name], dict):
            raise TaskError("INVALID_TASK_STATE")
    if value["writer"] is not None:
        require_keys(value["writer"], {"claimId", "writerId", "sessionDigest"}, "INVALID_TASK_STATE")
        require_sha256(value["writer"]["claimId"], "INVALID_TASK_STATE")
        require_string(value["writer"]["writerId"], "INVALID_TASK_STATE")
        require_sha256(value["writer"]["sessionDigest"], "INVALID_TASK_STATE")
    if value["offer"] is not None:
        require_keys(value["offer"], {"offerId", "epoch", "authorizationDigest"}, "INVALID_TASK_STATE")
        require_sha256(value["offer"]["offerId"], "INVALID_TASK_STATE")
        require_sha256(value["offer"]["authorizationDigest"], "INVALID_TASK_STATE")
        if not isinstance(value["offer"]["epoch"], int) or value["offer"]["epoch"] < 0:
            raise TaskError("INVALID_TASK_STATE")
    if value["claim"] is not None:
        _claim_record(value["claim"])
    if not isinstance(value["retiredClaims"], list):
        raise TaskError("INVALID_TASK_STATE")
    for retired in value["retiredClaims"]:
        if not isinstance(retired, dict):
            raise TaskError("INVALID_TASK_STATE")
        require_keys(retired, {"offerId", "claim", "epoch", "reason", "retiredAt"}, "INVALID_TASK_STATE")
        require_sha256(retired["offerId"], "INVALID_TASK_STATE")
        if retired["claim"] is not None:
            _claim_record(retired["claim"])
            if retired["claim"]["offerId"] != retired["offerId"] or retired["claim"]["epoch"] != retired["epoch"]:
                raise TaskError("INVALID_TASK_STATE")
        if not isinstance(retired["epoch"], int) or retired["epoch"] < 0:
            raise TaskError("INVALID_TASK_STATE")
        require_string(retired["reason"], "INVALID_TASK_STATE")
        require_utc(retired["retiredAt"], "INVALID_TASK_STATE")
    if value["delivery"] is not None:
        require_keys(value["delivery"], {"implementationHead", "claimId", "deliveredAt"}, "INVALID_TASK_STATE")
        require_sha1(value["delivery"]["implementationHead"], "INVALID_TASK_STATE")
        require_sha256(value["delivery"]["claimId"], "INVALID_TASK_STATE")
        require_utc(value["delivery"]["deliveredAt"], "INVALID_TASK_STATE")
    if value["acceptance"] is not None:
        require_keys(value["acceptance"], {"candidateHead", "reviewDigest", "merged", "acceptedAt"}, "INVALID_TASK_STATE")
        require_sha1(value["acceptance"]["candidateHead"], "INVALID_TASK_STATE")
        require_sha256(value["acceptance"]["reviewDigest"], "INVALID_TASK_STATE")
        if not isinstance(value["acceptance"]["merged"], bool):
            raise TaskError("INVALID_TASK_STATE")
        require_utc(value["acceptance"]["acceptedAt"], "INVALID_TASK_STATE")
    if value["completion"] is not None:
        require_keys(value["completion"], {"mergeHead", "archiveDigest", "completedAt"}, "INVALID_TASK_STATE")
        require_sha1(value["completion"]["mergeHead"], "INVALID_TASK_STATE")
        require_sha256(value["completion"]["archiveDigest"], "INVALID_TASK_STATE")
        require_utc(value["completion"]["completedAt"], "INVALID_TASK_STATE")
    offer = value["offer"]
    claim = value["claim"]
    writer = value["writer"]
    delivery = value["delivery"]
    acceptance = value["acceptance"]
    completion = value["completion"]
    if offer is not None and offer["epoch"] != value["epoch"]:
        raise TaskError("INVALID_TASK_STATE")
    if claim is not None and claim["epoch"] != value["epoch"]:
        raise TaskError("INVALID_TASK_STATE")
    if offer is not None and claim is not None and offer["offerId"] != claim["offerId"]:
        raise TaskError("INVALID_TASK_STATE")
    if writer is not None and claim is not None and (
        writer["claimId"] != claim["claimId"]
        or writer["writerId"] != claim["writerId"]
        or writer["sessionDigest"] != claim["sessionDigest"]
    ):
        raise TaskError("INVALID_TASK_STATE")
    if delivery is not None and (claim is None or delivery["claimId"] != claim["claimId"]):
        raise TaskError("INVALID_TASK_STATE")
    if value["retiredClaims"]:
        epochs = [item["epoch"] for item in value["retiredClaims"]]
        if epochs != sorted(set(epochs)) or any(epoch >= value["epoch"] for epoch in epochs):
            raise TaskError("INVALID_TASK_STATE")
    phase_requirements = {
        "planning": (False, False, False, False, False, False),
        "awaiting_claim": (False, True, False, False, False, False),
        "implementing": (True, True, True, False, False, False),
        "delivered": (False, True, True, True, False, False),
        "accepted": (False, True, True, True, True, False),
        "completed": (False, True, True, True, True, True),
    }
    required = phase_requirements[value["phase"]]
    actual = tuple(item is not None for item in (writer, offer, claim, delivery, acceptance, completion))
    if actual != required:
        raise TaskError("INVALID_TASK_STATE")


def _claim_record(value: dict[str, Any]) -> None:
    legacy_keys = {"claimId", "offerId", "epoch", "writerId", "sessionDigest", "roleDigest", "configDigest", "claimedAt", "claimBaseHead"}
    if "activationId" in value or "envelopeId" in value:
        require_keys(value, legacy_keys | {"activationId", "envelopeId"}, "INVALID_TASK_STATE")
        require_sha256(value["activationId"], "INVALID_TASK_STATE")
        require_sha256(value["envelopeId"], "INVALID_TASK_STATE")
    else:
        require_keys(value, legacy_keys, "INVALID_TASK_STATE")
    for field in ("claimId", "offerId", "sessionDigest", "roleDigest", "configDigest"):
        require_sha256(value[field], "INVALID_TASK_STATE")
    if not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_TASK_STATE")
    require_string(value["writerId"], "INVALID_TASK_STATE")
    require_utc(value["claimedAt"], "INVALID_TASK_STATE")
    require_sha1(value["claimBaseHead"], "INVALID_TASK_STATE")


def _history_relationships(value: dict[str, Any]) -> None:
    history = value["history"]
    lifecycle = value["lifecycle"]
    if not history or history[0]["type"] != "bootstrap" or history[0]["head"] != value["repository"]["baseSha"]:
        raise TaskError("INVALID_TASK_STATE")
    if any(event["head"] is None for event in history):
        raise TaskError("INVALID_TASK_STATE")
    if [event["at"] for event in history] != sorted(event["at"] for event in history):
        raise TaskError("INVALID_TASK_STATE")

    retirement_events = [event for event in history if event["type"] in {"revoked", "reclaimed"}]
    retired_claims = lifecycle["retiredClaims"]
    if len(retirement_events) != lifecycle["epoch"] or len(retirement_events) != len(retired_claims):
        raise TaskError("INVALID_TASK_STATE")
    if any(event["recordDigest"] != digest_object(retired) for event, retired in zip(retirement_events, retired_claims)):
        raise TaskError("INVALID_TASK_STATE")

    phase_events = [
        event
        for event in history
        if event["type"] in {"offer_created", "claimed", "revoked", "reclaimed", "delivered", "accepted", "completed"}
    ]
    last_phase_event = phase_events[-1]["type"] if phase_events else None
    expected_last = {
        "planning": None if lifecycle["epoch"] == 0 else {"revoked", "reclaimed"},
        "awaiting_claim": "offer_created",
        "implementing": "claimed",
        "delivered": "delivered",
        "accepted": "accepted",
        "completed": "completed",
    }[lifecycle["phase"]]
    if isinstance(expected_last, set):
        if last_phase_event not in expected_last:
            raise TaskError("INVALID_TASK_STATE")
    elif last_phase_event != expected_last:
        raise TaskError("INVALID_TASK_STATE")

    record_bindings = (
        ("claimed", lifecycle["claim"]),
        ("delivered", lifecycle["delivery"]),
        ("accepted", lifecycle["acceptance"]),
        ("completed", lifecycle["completion"]),
    )
    for event_type, record in record_bindings:
        matching = [event for event in history if event["type"] == event_type]
        if record is None:
            if matching and lifecycle["epoch"] == 0:
                raise TaskError("INVALID_TASK_STATE")
            continue
        if not matching or matching[-1]["recordDigest"] != digest_object(record):
            raise TaskError("INVALID_TASK_STATE")

    blocked = False
    active_block_digest: str | None = None
    for event in history:
        if event["type"] == "blocked":
            if blocked:
                raise TaskError("INVALID_TASK_STATE")
            blocked = True
            active_block_digest = event["recordDigest"]
        elif event["type"] == "resumed":
            if not blocked or event["recordDigest"] != active_block_digest:
                raise TaskError("INVALID_TASK_STATE")
            blocked = False
            active_block_digest = None
    if blocked != (lifecycle["blocked"] is not None):
        raise TaskError("INVALID_TASK_STATE")
    if blocked and active_block_digest != digest_object(lifecycle["blocked"]):
        raise TaskError("INVALID_TASK_STATE")


def finalize_state(value: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(value)
    state.pop("integrityDigest", None)
    state["integrityDigest"] = digest_object(state)
    return state


def validate_state(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "taskId",
            "revision",
            "repository",
            "documents",
            "approval",
            "implementationAuthorization",
            "actionAuthorizationDigest",
            "lifecycle",
            "history",
            "integrityDigest",
        },
        "INVALID_TASK_STATE",
    )
    if value["schemaVersion"] != TASK_SCHEMA_VERSION:
        raise TaskError("INVALID_TASK_STATE")
    require_string(value["taskId"], "INVALID_TASK_STATE")
    if not isinstance(value["revision"], int) or value["revision"] < 0:
        raise TaskError("INVALID_TASK_STATE")
    _repository_record(value["repository"])
    _documents_record(value["documents"])
    _approval_record(value["approval"])
    _implementation_authorization(value["implementationAuthorization"])
    if value["actionAuthorizationDigest"] is not None:
        require_sha256(value["actionAuthorizationDigest"], "INVALID_TASK_STATE")
    _lifecycle_record(value["lifecycle"])
    approval = value["approval"]
    implementation = value["implementationAuthorization"]
    authorization_digest_value = value["actionAuthorizationDigest"]
    plan = value["documents"]["plan"]
    if (implementation is None) != (authorization_digest_value is None):
        raise TaskError("INVALID_TASK_STATE")
    if implementation is not None and (
        approval is None
        or implementation["planVersion"] != plan["version"]
        or implementation["materialDigest"] != plan["materialDigest"]
    ):
        raise TaskError("INVALID_TASK_STATE")
    lifecycle_offer = value["lifecycle"]["offer"]
    if lifecycle_offer is not None and lifecycle_offer["authorizationDigest"] != authorization_digest_value:
        raise TaskError("INVALID_TASK_STATE")
    if value["lifecycle"]["phase"] != "planning" and implementation is None:
        raise TaskError("INVALID_TASK_STATE")
    if value["lifecycle"]["phase"] == "completed" and not value["lifecycle"]["acceptance"]["merged"]:
        raise TaskError("INVALID_TASK_STATE")
    if not isinstance(value["history"], list) or len(value["history"]) != value["revision"] + 1:
        raise TaskError("INVALID_TASK_STATE")
    for index, event in enumerate(value["history"]):
        if not isinstance(event, dict):
            raise TaskError("INVALID_TASK_STATE")
        require_keys(event, {"revision", "type", "at", "head", "recordDigest"}, "INVALID_TASK_STATE")
        if event["revision"] != index or event["type"] not in EVENT_TYPES:
            raise TaskError("INVALID_TASK_STATE")
        require_utc(event["at"], "INVALID_TASK_STATE")
        if event["head"] is not None:
            require_sha1(event["head"], "INVALID_TASK_STATE")
        require_sha256(event["recordDigest"], "INVALID_TASK_STATE")
    _history_relationships(value)
    require_sha256(value["integrityDigest"], "INVALID_TASK_STATE")
    unsigned = deepcopy(value)
    actual = unsigned.pop("integrityDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("TASK_STATE_TAMPERED")
    if approval is not None and (
        approval["planVersion"] != plan["version"]
        or approval["materialDigest"] != plan["materialDigest"]
        or plan["status"] != "approved"
    ):
        raise TaskError("PLAN_APPROVAL_MISMATCH")


def read_state(path: Path, task_root: Path | None = None) -> dict[str, Any]:
    value = read_canonical_json(path, "INVALID_TASK_STATE", validate_state)
    if task_root is not None:
        records = inspect_tracked_package(task_root)
        if records["requirements"]["digest"] != value["documents"]["requirements"]["digest"]:
            raise TaskError("DOCUMENT_DIGEST_DRIFT")
        if records["plan"]["digest"] != value["documents"]["plan"]["digest"]:
            raise TaskError("DOCUMENT_DIGEST_DRIFT")
        if records["plan"]["materialDigest"] != value["documents"]["plan"]["materialDigest"]:
            raise TaskError("PLAN_MATERIAL_DRIFT")
        if records["implementation"]["digest"] != value["documents"]["implementation"]["digest"]:
            raise TaskError("DOCUMENT_DIGEST_DRIFT")
    return value


def new_state(
    task_id: str,
    repository: dict[str, str],
    documents: dict[str, Any],
    at: str,
    head: str,
) -> dict[str, Any]:
    event = {
        "revision": 0,
        "type": "bootstrap",
        "at": at,
        "head": head,
        "recordDigest": sha256_bytes(canonical_bytes({"taskId": task_id, "repository": repository})),
    }
    return finalize_state(
        {
            "schemaVersion": TASK_SCHEMA_VERSION,
            "taskId": task_id,
            "revision": 0,
            "repository": repository,
            "documents": documents,
            "approval": None,
            "implementationAuthorization": None,
            "actionAuthorizationDigest": None,
            "lifecycle": {
                "phase": "planning",
                "epoch": 0,
                "blocked": None,
                "writer": None,
                "offer": None,
                "claim": None,
                "retiredClaims": [],
                "delivery": None,
                "acceptance": None,
                "completion": None,
            },
            "history": [event],
        }
    )


def advance_state(state: dict[str, Any], event_type: str, at: str, head: str, record: Any) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise TaskError("INVALID_TRANSITION")
    result = deepcopy(state)
    result["revision"] += 1
    result["history"].append(
        {
            "revision": result["revision"],
            "type": event_type,
            "at": at,
            "head": head,
            "recordDigest": digest_object(record),
        }
    )
    return finalize_state(result)


def record_acceptance_state(
    state: dict[str, Any],
    candidate_head: str,
    review_digest: str,
    merged: bool,
    at: str,
) -> dict[str, Any]:
    if state["lifecycle"]["phase"] != "delivered" or state["lifecycle"]["blocked"] is not None:
        raise TaskError("INVALID_TRANSITION")
    require_sha1(candidate_head, "INVALID_TASK_STATE")
    require_sha256(review_digest, "INVALID_TASK_STATE")
    if not isinstance(merged, bool):
        raise TaskError("INVALID_TASK_STATE")
    record = {
        "candidateHead": candidate_head,
        "reviewDigest": review_digest,
        "merged": merged,
        "acceptedAt": require_utc(at, "INVALID_TASK_STATE"),
    }
    updated = deepcopy(state)
    updated["lifecycle"]["phase"] = "accepted"
    updated["lifecycle"]["acceptance"] = record
    return advance_state(updated, "accepted", at, candidate_head, record)


def record_completion_state(
    state: dict[str, Any],
    merge_head: str,
    archive_digest: str,
    at: str,
) -> dict[str, Any]:
    if (
        state["lifecycle"]["phase"] != "accepted"
        or state["lifecycle"]["blocked"] is not None
        or state["lifecycle"]["acceptance"] is None
        or not state["lifecycle"]["acceptance"]["merged"]
    ):
        raise TaskError("INVALID_TRANSITION")
    require_sha1(merge_head, "INVALID_TASK_STATE")
    require_sha256(archive_digest, "INVALID_TASK_STATE")
    record = {
        "mergeHead": merge_head,
        "archiveDigest": archive_digest,
        "completedAt": require_utc(at, "INVALID_TASK_STATE"),
    }
    updated = deepcopy(state)
    updated["lifecycle"]["phase"] = "completed"
    updated["lifecycle"]["completion"] = record
    return advance_state(updated, "completed", at, merge_head, record)


def authorization_digest(value: dict[str, Any]) -> str:
    unsigned = deepcopy(value)
    unsigned.pop("authorizationDigest", None)
    return digest_object(unsigned)


def validate_authorization(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "authorizationId",
            "taskId",
            "repository",
            "baseBranch",
            "baseSha",
            "taskBranch",
            "planVersion",
            "materialDigest",
            "mode",
            "allowedActions",
            "decisionRef",
            "recordedAt",
            "authorizationDigest",
        },
        "INVALID_AUTHORIZATION",
    )
    if value["schemaVersion"] != TASK_SCHEMA_VERSION:
        raise TaskError("INVALID_AUTHORIZATION")
    require_sha256(value["authorizationId"], "INVALID_AUTHORIZATION")
    require_string(value["taskId"], "INVALID_AUTHORIZATION")
    require_string(value["repository"], "INVALID_AUTHORIZATION")
    require_string(value["baseBranch"], "INVALID_AUTHORIZATION")
    require_sha1(value["baseSha"], "INVALID_AUTHORIZATION")
    require_string(value["taskBranch"], "INVALID_AUTHORIZATION")
    if not isinstance(value["planVersion"], int) or value["planVersion"] < 1:
        raise TaskError("INVALID_AUTHORIZATION")
    require_sha256(value["materialDigest"], "INVALID_AUTHORIZATION")
    if value["mode"] not in ACTION_MODES:
        raise TaskError("INVALID_AUTHORIZATION")
    if (
        not isinstance(value["allowedActions"], list)
        or value["allowedActions"] != sorted(set(value["allowedActions"]))
        or not set(value["allowedActions"]).issubset(KNOWN_ACTIONS)
    ):
        raise TaskError("INVALID_AUTHORIZATION")
    if value["mode"] == "implement_only" and "conditional_merge" in value["allowedActions"]:
        raise TaskError("INVALID_AUTHORIZATION")
    require_string(value["decisionRef"], "INVALID_AUTHORIZATION")
    require_utc(value["recordedAt"], "INVALID_AUTHORIZATION")
    require_sha256(value["authorizationDigest"], "INVALID_AUTHORIZATION")
    if authorization_digest(value) != value["authorizationDigest"]:
        raise TaskError("AUTHORIZATION_TAMPERED")


def validate_offer(value: dict[str, Any]) -> None:
    legacy_keys = {
            "schemaVersion",
            "offerId",
            "status",
            "epoch",
            "taskId",
            "repository",
            "taskBranch",
            "expectedHead",
            "expectedRevision",
            "route",
            "planVersion",
            "planMaterialDigest",
            "authorizationDigest",
            "allowedActions",
            "roleDigest",
            "configDigest",
            "capabilityDigest",
            "createdAt",
            "expiresAt",
            "consumedByDigest",
        }
    if value.get("schemaVersion") == 2:
        require_keys(value, legacy_keys | {"roleName", "bundleDigest"}, "INVALID_OFFER")
        require_string(value["roleName"], "INVALID_OFFER")
        require_sha256(value["bundleDigest"], "INVALID_OFFER")
    else:
        require_keys(value, legacy_keys, "INVALID_OFFER")
    if value["schemaVersion"] not in {TASK_SCHEMA_VERSION, 2} or value["status"] not in {"active", "consumed", "revoked"}:
        raise TaskError("INVALID_OFFER")
    for field in ("offerId", "planMaterialDigest", "authorizationDigest", "roleDigest", "configDigest", "capabilityDigest"):
        require_sha256(value[field], "INVALID_OFFER")
    require_string(value["taskId"], "INVALID_OFFER")
    require_string(value["repository"], "INVALID_OFFER")
    require_string(value["taskBranch"], "INVALID_OFFER")
    require_sha1(value["expectedHead"], "INVALID_OFFER")
    if not isinstance(value["expectedRevision"], int) or value["expectedRevision"] < 0:
        raise TaskError("INVALID_OFFER")
    if not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_OFFER")
    require_string(value["route"], "INVALID_OFFER")
    if not isinstance(value["planVersion"], int) or value["planVersion"] < 1:
        raise TaskError("INVALID_OFFER")
    if (
        not isinstance(value["allowedActions"], list)
        or any(not isinstance(action, str) for action in value["allowedActions"])
        or value["allowedActions"] != sorted(set(value["allowedActions"]))
        or not set(value["allowedActions"]).issubset(KNOWN_ACTIONS)
    ):
        raise TaskError("INVALID_OFFER")
    require_utc(value["createdAt"], "INVALID_OFFER")
    require_utc(value["expiresAt"], "INVALID_OFFER")
    if value["consumedByDigest"] is not None:
        require_sha256(value["consumedByDigest"], "INVALID_OFFER")


def validate_runtime_evidence(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "provider", "writerId", "sessionDigest", "roleDigest", "configDigest", "route", "status", "observedAt", "evidenceDigest"},
        "INVALID_RUNTIME_EVIDENCE",
    )
    if value["schemaVersion"] != TASK_SCHEMA_VERSION or value["status"] not in {"active", "terminal", "missing"}:
        raise TaskError("INVALID_RUNTIME_EVIDENCE")
    for field in ("provider", "writerId", "route"):
        require_string(value[field], "INVALID_RUNTIME_EVIDENCE")
    for field in ("sessionDigest", "roleDigest", "configDigest", "evidenceDigest"):
        require_sha256(value[field], "INVALID_RUNTIME_EVIDENCE")
    require_utc(value["observedAt"], "INVALID_RUNTIME_EVIDENCE")
    unsigned = deepcopy(value)
    actual = unsigned.pop("evidenceDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_RUNTIME_EVIDENCE")
