"""Deterministic release-verification contracts with no GitHub write surface."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from gkd_ci.github import GitHubClient
from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256
from gkd_task.errors import TaskError

from .core import DECISIONS, validate_traceability


CANARY_CHECK = "GKD Canary"
SANDBOX_REPOSITORY_RE = re.compile(r"github\.com/[A-Za-z0-9_.-]+/gkd-sandbox")
L3_STAGES = (
    ("fresh-agent", "started"),
    ("approved-scope", "read"),
    ("authorization-boundary", "reported"),
    ("terminal", "complete"),
)


def _is_sha256(value: Any) -> bool:
    try:
        require_sha256(value, "INVALID_RELEASE_VERIFICATION")
    except TaskError:
        return False
    return True


def _release_fixture(traceability: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "0.1.0",
        "sourceSha": "a" * 40,
        "bundleDigest": "b" * 64,
        "evidenceDigest": "c" * 64,
        "traceability": traceability,
        "layers": ["L0", "L1", "L2", "L3", "L4"],
        "sandboxRepository": "github.com/example/gkd-sandbox",
    }


def _expect_traceability_failure(value: dict[str, Any]) -> None:
    try:
        validate_traceability(value)
    except TaskError:
        return
    raise TaskError("L1_PROPERTY_NOT_KILLED")


def run_l1_properties(traceability: dict[str, Any]) -> dict[str, Any]:
    """Execute property counterexamples for every approved decision entry."""

    validate_traceability(traceability)
    from .core import build_release_candidate, promotion_request

    record = build_release_candidate(_release_fixture(traceability))
    if promotion_request(record)["targetSha"] != "a" * 40:
        raise TaskError("L1_PROPERTY_FAILED")

    results = []
    for index, decision in enumerate(DECISIONS):
        entry = traceability["decisions"][index]
        if entry["decisionId"] != decision:
            raise TaskError("L1_PROPERTY_FAILED")
        negative = deepcopy(traceability)
        negative["decisions"][index]["negative"] = ["unbound-negative"]
        _expect_traceability_failure(negative)
        mutation = deepcopy(traceability)
        mutation["decisions"][index]["mutation"] = "unbound-mutation"
        _expect_traceability_failure(mutation)
        results.append(
            {
                "decisionId": decision,
                "positive": "pass",
                "negative": "pass",
                "mutation": "pass",
            }
        )
    evidence = {"layer": "L1", "properties": results, "schemaVersion": 1}
    return {**evidence, "evidenceDigest": digest_object(evidence)}


def validate_l2_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L2_REQUEST_INVALID")
    require_keys(
        value,
        {"baseBranch", "expectedHead", "pullRequest", "repository", "requiredCheck", "schemaVersion"},
        "L2_REQUEST_INVALID",
    )
    if (
        value["schemaVersion"] != 1
        or not isinstance(value["repository"], str)
        or not SANDBOX_REPOSITORY_RE.fullmatch(value["repository"])
        or value["baseBranch"] != "main"
        or value["requiredCheck"] != CANARY_CHECK
        or isinstance(value["pullRequest"], bool)
        or not isinstance(value["pullRequest"], int)
        or value["pullRequest"] < 1
    ):
        raise TaskError("L2_REQUEST_INVALID")
    require_sha1(value["expectedHead"], "L2_REQUEST_INVALID")
    return value


def run_l2_probe(value: Any, github: GitHubClient | None = None) -> dict[str, Any]:
    request = validate_l2_request(value)
    observation = (github or GitHubClient()).observe(
        request["repository"],
        request["pullRequest"],
        request["expectedHead"],
        (request["requiredCheck"],),
    )
    if (
        observation.repository != request["repository"]
        or observation.base_branch != request["baseBranch"]
        or observation.head_sha != request["expectedHead"]
        or observation.state != "open"
        or observation.checks != ((CANARY_CHECK, "success"),)
    ):
        raise TaskError("L2_CANARY_OBSERVATION_INVALID")
    evidence = {
        "expectedHead": request["expectedHead"],
        "layer": "L2",
        "outcome": "pass",
        "pullRequest": request["pullRequest"],
        "repository": request["repository"],
        "schemaVersion": 1,
    }
    return {**evidence, "evidenceDigest": digest_object(evidence)}


def validate_forward_eval_trace(value: Any, expected_source_sha: str | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L3_TRACE_INVALID")
    require_keys(
        value,
        {"contextDigest", "events", "promptDigest", "roleName", "schemaVersion", "sourceSha"},
        "L3_TRACE_INVALID",
    )
    if value["schemaVersion"] != 1 or value["roleName"] != "gkd_executor" or not isinstance(value["events"], list):
        raise TaskError("L3_TRACE_INVALID")
    require_sha1(value["sourceSha"], "L3_TRACE_INVALID")
    if expected_source_sha is not None and value["sourceSha"] != expected_source_sha:
        raise TaskError("L3_SOURCE_SHA_MISMATCH")
    if not _is_sha256(value["contextDigest"]) or not _is_sha256(value["promptDigest"]):
        raise TaskError("L3_TRACE_INVALID")
    expected_events = []
    for stage, result in L3_STAGES:
        expected_events.append({"result": result, "stage": stage})
    if value["events"] != expected_events:
        raise TaskError("L3_TRACE_INVALID")
    return value


def build_l4_canary_request(record: dict[str, Any]) -> dict[str, Any]:
    from .core import promotion_request

    promotion = promotion_request(record)
    if not SANDBOX_REPOSITORY_RE.fullmatch(record["sandboxRepository"]):
        raise TaskError("L4_SANDBOX_INVALID")
    request = {
        "branch": f"gkd-canary/{record['sourceSha'][:12]}",
        "bundleDigest": record["bundleDigest"],
        "operation": "sandbox-canary",
        "repository": record["sandboxRepository"],
        "requiredCheck": CANARY_CHECK,
        "schemaVersion": 1,
        "sourceSha": promotion["targetSha"],
    }
    return {**request, "requestDigest": digest_object(request)}


def validate_l4_canary_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    require_keys(
        value,
        {"branch", "bundleDigest", "operation", "repository", "requestDigest", "requiredCheck", "schemaVersion", "sourceSha"},
        "L4_CANARY_REQUEST_INVALID",
    )
    request = dict(value)
    actual = request.pop("requestDigest")
    if actual != digest_object(request):
        raise TaskError("L4_CANARY_REQUEST_TAMPERED")
    if (
        request["schemaVersion"] != 1
        or request["operation"] != "sandbox-canary"
        or not isinstance(request["repository"], str)
        or not SANDBOX_REPOSITORY_RE.fullmatch(request["repository"])
        or request["requiredCheck"] != CANARY_CHECK
    ):
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    require_sha1(request["sourceSha"], "L4_CANARY_REQUEST_INVALID")
    require_sha256(request["bundleDigest"], "L4_CANARY_REQUEST_INVALID")
    if request["branch"] != f"gkd-canary/{request['sourceSha'][:12]}":
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    return value


def validate_l4_canary_result(request: dict[str, Any], value: Any) -> dict[str, Any]:
    validate_l4_canary_request(request)
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_RESULT_INVALID")
    require_keys(
        value,
        {"branch", "eventDigest", "outcome", "pullRequest", "repository", "requestDigest", "schemaVersion", "sourceSha"},
        "L4_CANARY_RESULT_INVALID",
    )
    if (
        value["schemaVersion"] != 1
        or value["repository"] != request["repository"]
        or value["branch"] != request["branch"]
        or value["sourceSha"] != request["sourceSha"]
        or value["requestDigest"] != request["requestDigest"]
        or value["outcome"] not in {"failure", "success"}
        or isinstance(value["pullRequest"], bool)
        or not isinstance(value["pullRequest"], int)
        or value["pullRequest"] < 1
        or not _is_sha256(value["eventDigest"])
    ):
        raise TaskError("L4_CANARY_RESULT_INVALID")
    return value
