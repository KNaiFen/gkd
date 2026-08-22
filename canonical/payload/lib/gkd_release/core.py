"""Release-candidate records remain side-effect free."""

from __future__ import annotations

import re
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256
from gkd_task.errors import TaskError


DECISIONS = tuple(f"GKD-{number:03d}" for number in range(1, 17))
LAYERS = {"L0", "L1", "L2", "L3", "L4"}


def _trace_entry(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TRACEABILITY")
    require_keys(value, {"decisionId", "positive", "negative", "mutation"}, "INVALID_TRACEABILITY")
    if value["decisionId"] not in DECISIONS or not all(isinstance(value[key], list) and value[key] for key in ("positive", "negative")):
        raise TaskError("INVALID_TRACEABILITY")
    if value["mutation"] is not None and not isinstance(value["mutation"], str):
        raise TaskError("INVALID_TRACEABILITY")


def validate_traceability(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TRACEABILITY")
    require_keys(value, {"schemaVersion", "decisions"}, "INVALID_TRACEABILITY")
    if value["schemaVersion"] != 1 or not isinstance(value["decisions"], list):
        raise TaskError("INVALID_TRACEABILITY")
    for entry in value["decisions"]:
        _trace_entry(entry)
    if tuple(entry["decisionId"] for entry in value["decisions"]) != DECISIONS:
        raise TaskError("TRACEABILITY_INCOMPLETE")
    if any(entry["mutation"] is None for entry in value["decisions"][:4]):
        raise TaskError("TRACEABILITY_MUTATION_MISSING")


def build_release_candidate(value: dict[str, Any]) -> dict[str, Any]:
    require_keys(value, {"version", "sourceSha", "bundleDigest", "evidenceDigest", "traceability", "layers", "sandboxRepository"}, "INVALID_RELEASE_CANDIDATE")
    if value["version"] != "0.1.0" or not isinstance(value["sandboxRepository"], str) or not re.fullmatch(r"github\.com/[A-Za-z0-9_.-]+/gkd-sandbox", value["sandboxRepository"]):
        raise TaskError("INVALID_RELEASE_CANDIDATE")
    require_sha1(value["sourceSha"], "INVALID_RELEASE_CANDIDATE")
    for key in ("bundleDigest", "evidenceDigest"):
        require_sha256(value[key], "INVALID_RELEASE_CANDIDATE")
    validate_traceability(value["traceability"])
    if not isinstance(value["layers"], list) or set(value["layers"]) != LAYERS:
        raise TaskError("RELEASE_LAYERS_INVALID")
    result = dict(value)
    result["provenance"] = {"sourceSha": value["sourceSha"], "bundleDigest": value["bundleDigest"], "evidenceDigest": value["evidenceDigest"], "traceabilityDigest": digest_object(value["traceability"])}
    result["recordDigest"] = digest_object(result)
    return result


def promotion_request(record: dict[str, Any]) -> dict[str, Any]:
    expected = dict(record)
    actual = expected.pop("recordDigest", None)
    if actual != digest_object(expected):
        raise TaskError("RELEASE_RECORD_TAMPERED")
    rebuilt = build_release_candidate({key: record[key] for key in ("version", "sourceSha", "bundleDigest", "evidenceDigest", "traceability", "layers", "sandboxRepository")})
    if rebuilt != record:
        raise TaskError("RELEASE_RECORD_TAMPERED")
    return {"tagName": "v0.1.0", "targetSha": record["sourceSha"], "bundleDigest": record["bundleDigest"], "provenanceDigest": digest_object(record["provenance"])}
