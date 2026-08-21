"""Repository-neutral, side-effect-free finalization records."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from gkd_task.canonical import digest_object, relative_path, require_keys, require_sha1, require_sha256, require_string
from gkd_task.errors import TaskError


SCHEMA_VERSION = 1
MODES = {"closeout-only", "release"}
VERSION_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
ASSET_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _pr(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(value, {"number", "headSha"}, "INVALID_FINALIZATION")
    if not isinstance(value["number"], int) or value["number"] < 1:
        raise TaskError("INVALID_FINALIZATION")
    require_sha1(value["headSha"], "INVALID_FINALIZATION")


def _metadata(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(
        value,
        {"version", "sourceSha", "mainSha", "bundleDigest", "lockDigest", "changelogPath", "changelogDigest"},
        "INVALID_FINALIZATION",
    )
    if not isinstance(value["version"], str) or not VERSION_RE.fullmatch(value["version"]):
        raise TaskError("INVALID_FINALIZATION")
    require_sha1(value["sourceSha"], "INVALID_FINALIZATION")
    require_sha1(value["mainSha"], "INVALID_FINALIZATION")
    for field in ("bundleDigest", "lockDigest", "changelogDigest"):
        require_sha256(value[field], "INVALID_FINALIZATION")
    relative_path(value["changelogPath"], "INVALID_FINALIZATION")


def _evidence(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(value, {"sourceSha", "bundleDigest", "path", "digest"}, "INVALID_FINALIZATION")
    require_sha1(value["sourceSha"], "INVALID_FINALIZATION")
    for field in ("bundleDigest", "digest"):
        require_sha256(value[field], "INVALID_FINALIZATION")
    relative_path(value["path"], "INVALID_FINALIZATION")


def _assets(value: Any) -> None:
    if not isinstance(value, list):
        raise TaskError("INVALID_FINALIZATION")
    names: list[str] = []
    for asset in value:
        if not isinstance(asset, dict):
            raise TaskError("INVALID_FINALIZATION")
        require_keys(asset, {"name", "sourceSha", "bundleDigest", "sha256"}, "INVALID_FINALIZATION")
        name = asset["name"]
        if not isinstance(name, str) or not ASSET_NAME_RE.fullmatch(name):
            raise TaskError("INVALID_FINALIZATION")
        names.append(name)
        require_sha1(asset["sourceSha"], "INVALID_FINALIZATION")
        for field in ("bundleDigest", "sha256"):
            require_sha256(asset[field], "INVALID_FINALIZATION")
    if names != sorted(set(names)):
        raise TaskError("INVALID_FINALIZATION")


def _release_intent(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(
        value,
        {"mode", "version", "sourceSha", "adapterDigest", "authorizationDigest", "intentDigest"},
        "INVALID_FINALIZATION",
    )
    if value["mode"] not in MODES or not isinstance(value["version"], str) or not VERSION_RE.fullmatch(value["version"]):
        raise TaskError("INVALID_FINALIZATION")
    require_sha1(value["sourceSha"], "INVALID_FINALIZATION")
    for field in ("adapterDigest", "authorizationDigest"):
        if value[field] is not None:
            require_sha256(value[field], "INVALID_FINALIZATION")
    require_sha256(value["intentDigest"], "INVALID_FINALIZATION")
    unsigned = dict(value)
    actual = unsigned.pop("intentDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("FINALIZATION_TAMPERED")


def _provenance(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(
        value,
        {
            "sourceSha", "mainSha", "bundleDigest", "version", "lockDigest", "changelogDigest",
            "intentDigest", "evidenceDigest", "assetsDigest", "provenanceDigest",
        },
        "INVALID_FINALIZATION",
    )
    require_sha1(value["sourceSha"], "INVALID_FINALIZATION")
    require_sha1(value["mainSha"], "INVALID_FINALIZATION")
    if not isinstance(value["version"], str) or not VERSION_RE.fullmatch(value["version"]):
        raise TaskError("INVALID_FINALIZATION")
    for field in (
        "bundleDigest", "lockDigest", "changelogDigest", "intentDigest", "evidenceDigest",
        "assetsDigest", "provenanceDigest",
    ):
        require_sha256(value[field], "INVALID_FINALIZATION")
    unsigned = dict(value)
    actual = unsigned.pop("provenanceDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("FINALIZATION_TAMPERED")


def _input(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(
        value,
        {
            "taskId", "taskPr", "finalizationPr", "mode", "productLogic", "releaseSideEffects",
            "metadata", "evidence", "adapterDigest", "authorizationDigest", "assets",
        },
        "INVALID_FINALIZATION",
    )
    require_string(value["taskId"], "INVALID_FINALIZATION")
    _pr(value["taskPr"])
    if value["finalizationPr"] is not None:
        _pr(value["finalizationPr"])
    if value["mode"] not in MODES or not isinstance(value["productLogic"], bool) or not isinstance(value["releaseSideEffects"], bool):
        raise TaskError("INVALID_FINALIZATION")
    _metadata(value["metadata"])
    _evidence(value["evidence"])
    _assets(value["assets"])
    for field in ("adapterDigest", "authorizationDigest"):
        if value[field] is not None:
            require_sha256(value[field], "INVALID_FINALIZATION")


def _intent(value: dict[str, Any]) -> dict[str, Any]:
    metadata = value["metadata"]
    result = {
        "mode": value["mode"],
        "version": metadata["version"],
        "sourceSha": metadata["sourceSha"],
        "adapterDigest": value["adapterDigest"],
        "authorizationDigest": value["authorizationDigest"],
    }
    result["intentDigest"] = digest_object(result)
    return result


def _provenance_for(metadata: dict[str, Any], intent: dict[str, Any], evidence: dict[str, Any], assets: list[dict[str, Any]]) -> dict[str, Any]:
    result = {
        "sourceSha": metadata["sourceSha"],
        "mainSha": metadata["mainSha"],
        "bundleDigest": metadata["bundleDigest"],
        "version": metadata["version"],
        "lockDigest": metadata["lockDigest"],
        "changelogDigest": metadata["changelogDigest"],
        "intentDigest": intent["intentDigest"],
        "evidenceDigest": evidence["digest"],
        "assetsDigest": digest_object(assets),
    }
    result["provenanceDigest"] = digest_object(result)
    return result


def build_finalization(value: dict[str, Any]) -> dict[str, Any]:
    """Create one canonical record without calling a release adapter."""

    _input(value)
    task_pr = deepcopy(value["taskPr"])
    finalization_pr = deepcopy(value["finalizationPr"])
    metadata = deepcopy(value["metadata"])
    evidence = deepcopy(value["evidence"])
    assets = deepcopy(value["assets"])
    source_sha = metadata["sourceSha"]
    if metadata["mainSha"] != source_sha or task_pr["headSha"] != source_sha or (finalization_pr is not None and finalization_pr["headSha"] != source_sha):
        raise TaskError("FINALIZATION_SHA_SPLIT")
    if finalization_pr is not None and finalization_pr["number"] == task_pr["number"]:
        raise TaskError("FINALIZATION_PR_INVALID")
    if evidence["sourceSha"] != source_sha or evidence["bundleDigest"] != metadata["bundleDigest"]:
        raise TaskError("FINALIZATION_EVIDENCE_SPLIT")
    if any(asset["sourceSha"] != source_sha or asset["bundleDigest"] != metadata["bundleDigest"] for asset in assets):
        raise TaskError("FINALIZATION_ASSET_SPLIT")
    mode = value["mode"]
    if mode == "closeout-only":
        if value["productLogic"] or value["releaseSideEffects"] or value["adapterDigest"] is not None or value["authorizationDigest"] is not None or assets:
            raise TaskError("CLOSEOUT_SCOPE_VIOLATION")
        phase = "closeout-ready"
    else:
        if value["adapterDigest"] is None or value["authorizationDigest"] is None or not assets:
            raise TaskError("RELEASE_AUTHORIZATION_REQUIRED")
        phase = "promotion-ready"
    intent = _intent(value)
    provenance = _provenance_for(metadata, intent, evidence, assets)
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "task": {"taskId": value["taskId"], "taskPr": task_pr, "finalizationPr": finalization_pr},
        "finalization": {
            "mode": mode,
            "phase": phase,
            "productLogic": value["productLogic"],
            "releaseSideEffects": value["releaseSideEffects"],
        },
        "metadata": metadata,
        "releaseIntent": intent,
        "evidence": evidence,
        "assets": assets,
        "provenance": provenance,
    }
    result["recordDigest"] = digest_object(result)
    validate_finalization(result)
    return result


def validate_finalization(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "task", "finalization", "metadata", "releaseIntent", "evidence", "assets", "provenance", "recordDigest"},
        "INVALID_FINALIZATION",
    )
    if value["schemaVersion"] != SCHEMA_VERSION:
        raise TaskError("INVALID_FINALIZATION")
    task = value["task"]
    if not isinstance(task, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(task, {"taskId", "taskPr", "finalizationPr"}, "INVALID_FINALIZATION")
    require_string(task["taskId"], "INVALID_FINALIZATION")
    _pr(task["taskPr"])
    if task["finalizationPr"] is not None:
        _pr(task["finalizationPr"])
    finalization = value["finalization"]
    if not isinstance(finalization, dict):
        raise TaskError("INVALID_FINALIZATION")
    require_keys(finalization, {"mode", "phase", "productLogic", "releaseSideEffects"}, "INVALID_FINALIZATION")
    if (
        finalization["mode"] not in MODES
        or finalization["phase"] not in {"closeout-ready", "promotion-ready"}
        or not isinstance(finalization["productLogic"], bool)
        or not isinstance(finalization["releaseSideEffects"], bool)
    ):
        raise TaskError("INVALID_FINALIZATION")
    _metadata(value["metadata"])
    _release_intent(value["releaseIntent"])
    _evidence(value["evidence"])
    _assets(value["assets"])
    _provenance(value["provenance"])
    require_sha256(value["recordDigest"], "INVALID_FINALIZATION")
    unsigned = dict(value)
    actual = unsigned.pop("recordDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("FINALIZATION_TAMPERED")

    metadata = value["metadata"]
    intent = value["releaseIntent"]
    evidence = value["evidence"]
    assets = value["assets"]
    source_sha = metadata["sourceSha"]
    if (
        task["taskPr"]["headSha"] != source_sha
        or metadata["mainSha"] != source_sha
        or (task["finalizationPr"] is not None and task["finalizationPr"]["headSha"] != source_sha)
        or (task["finalizationPr"] is not None and task["finalizationPr"]["number"] == task["taskPr"]["number"])
        or evidence["sourceSha"] != source_sha
        or evidence["bundleDigest"] != metadata["bundleDigest"]
        or intent["mode"] != finalization["mode"]
        or intent["version"] != metadata["version"]
        or intent["sourceSha"] != source_sha
        or any(asset["sourceSha"] != source_sha or asset["bundleDigest"] != metadata["bundleDigest"] for asset in assets)
    ):
        raise TaskError("FINALIZATION_SHA_SPLIT")
    expected_provenance = _provenance_for(metadata, intent, evidence, assets)
    if value["provenance"] != expected_provenance:
        raise TaskError("FINALIZATION_PROVENANCE_SPLIT")
    if finalization["mode"] == "closeout-only":
        if (
            finalization["phase"] != "closeout-ready"
            or finalization["productLogic"]
            or finalization["releaseSideEffects"]
            or intent["adapterDigest"] is not None
            or intent["authorizationDigest"] is not None
            or assets
        ):
            raise TaskError("CLOSEOUT_SCOPE_VIOLATION")
    elif (
        finalization["phase"] != "promotion-ready"
        or intent["adapterDigest"] is None
        or intent["authorizationDigest"] is None
        or not assets
    ):
        raise TaskError("RELEASE_AUTHORIZATION_REQUIRED")


def promotion_plan(record: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an exact-SHA promotion request; no tag or release is created here."""

    validate_finalization(record)
    if record["finalization"]["mode"] != "release":
        raise TaskError("RELEASE_AUTHORIZATION_REQUIRED")
    metadata = record["metadata"]
    provenance = record["provenance"]
    request = {
        "schemaVersion": SCHEMA_VERSION,
        "tagName": f"v{metadata['version']}",
        "targetSha": metadata["sourceSha"],
        "releaseSha": metadata["sourceSha"],
        "assets": deepcopy(record["assets"]),
        "provenanceDigest": provenance["provenanceDigest"],
    }
    if existing is None:
        return {"status": "promotion-ready", "request": request}
    if not isinstance(existing, dict):
        raise TaskError("INVALID_PROMOTION_RECEIPT")
    require_keys(existing, {"tagName", "targetSha", "releaseSha", "assetsDigest", "provenanceDigest"}, "INVALID_PROMOTION_RECEIPT")
    if (
        existing["tagName"] != request["tagName"]
        or existing["targetSha"] != request["targetSha"]
        or existing["releaseSha"] != request["releaseSha"]
        or existing["assetsDigest"] != digest_object(request["assets"])
        or existing["provenanceDigest"] != request["provenanceDigest"]
    ):
        raise TaskError("PROMOTION_CONFLICT")
    return {"status": "already-promoted", "request": request}
