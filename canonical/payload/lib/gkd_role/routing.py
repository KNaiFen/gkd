"""Pure manual-default routing decisions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_ci.policy import validate_policy_binding
from gkd_task.canonical import digest_object, require_keys, require_sha256
from gkd_task.errors import TaskError


GATES = (
    "activationProviderReady",
    "bundleFixed",
    "offerClaimReady",
    "roleAvailable",
    "roleConfigFixed",
    "waitGateReady",
)


def decide_route(request: dict[str, Any]) -> dict[str, Any]:
    keys = {"schemaVersion", "requestedRoute", "bundleDigest", "gates"}
    if request.get("schemaVersion") == 2:
        keys.add("projectPolicy")
    require_keys(request, keys, "INVALID_ROUTE_REQUEST")
    if request["schemaVersion"] not in {1, 2} or request["requestedRoute"] not in {None, "manual", "automatic"}:
        raise TaskError("INVALID_ROUTE_REQUEST")
    require_sha256(request["bundleDigest"], "INVALID_ROUTE_REQUEST")
    gates = request["gates"]
    if not isinstance(gates, dict) or tuple(sorted(gates)) != GATES or any(not isinstance(gates[name], bool) for name in GATES):
        raise TaskError("INVALID_ROUTE_REQUEST")
    if request["schemaVersion"] == 2:
        validate_policy_binding(request["projectPolicy"])
    requested = request["requestedRoute"] or "manual"
    if requested == "manual":
        outcome = "manual"
        refusal = None
    else:
        missing = [name for name in GATES if not gates[name]]
        if missing:
            outcome = "manual_only"
            refusal = {"code": "AUTOMATIC_ROUTE_GATES_INCOMPLETE", "failedGates": missing}
        else:
            outcome = "automatic"
            refusal = None
    result = {
        "schemaVersion": request["schemaVersion"],
        "requestedRoute": requested,
        "outcome": outcome,
        "bundleDigest": request["bundleDigest"],
        "gates": deepcopy(gates),
        "selectedRole": "gkd_executor" if outcome == "automatic" else None,
        "fallbackAttempted": False,
        "refusal": refusal,
    }
    if request["schemaVersion"] == 2:
        result["projectPolicy"] = deepcopy(request["projectPolicy"])
    result["decisionDigest"] = digest_object(result)
    return result


def validate_route_decision(value: dict[str, Any], require_automatic: bool = False) -> None:
    keys = {
        "schemaVersion", "requestedRoute", "outcome", "bundleDigest", "gates",
        "selectedRole", "fallbackAttempted", "refusal", "decisionDigest",
    }
    if value.get("schemaVersion") == 2:
        keys.add("projectPolicy")
    require_keys(value, keys, "INVALID_ROUTE_DECISION")
    if value["schemaVersion"] not in {1, 2}:
        raise TaskError("INVALID_ROUTE_DECISION")
    require_sha256(value["bundleDigest"], "INVALID_ROUTE_DECISION")
    require_sha256(value["decisionDigest"], "INVALID_ROUTE_DECISION")
    gates = value["gates"]
    if not isinstance(gates, dict) or tuple(sorted(gates)) != GATES or any(not isinstance(gates[name], bool) for name in GATES):
        raise TaskError("INVALID_ROUTE_DECISION")
    if value["schemaVersion"] == 2:
        validate_policy_binding(value["projectPolicy"])
    unsigned = deepcopy(value)
    digest = unsigned.pop("decisionDigest")
    if digest_object(unsigned) != digest:
        raise TaskError("INVALID_ROUTE_DECISION")
    if require_automatic and (
        value["schemaVersion"] != 2
        or value["requestedRoute"] != "automatic"
        or value["outcome"] != "automatic"
        or value["selectedRole"] != "gkd_executor"
        or value["fallbackAttempted"] is not False
        or value["refusal"] is not None
        or not all(gates.values())
    ):
        raise TaskError("AUTOMATIC_ROUTE_GATES_INCOMPLETE")


def m2a_route_evidence(bundle_digest: str) -> dict[str, Any]:
    return decide_route(
        {
            "schemaVersion": 1,
            "requestedRoute": "automatic",
            "bundleDigest": bundle_digest,
            "gates": {
                "activationProviderReady": True,
                "bundleFixed": True,
                "offerClaimReady": True,
                "roleAvailable": True,
                "roleConfigFixed": True,
                "waitGateReady": False,
            },
        }
    )
