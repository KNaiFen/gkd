"""Fixed-tree validation for automatic-delivery artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes, digest_object, require_sha1, require_sha256, sha256_bytes
from .errors import TaskError
from .gitops import changed_paths, read_tree_file, require_regular_tree_file
from .model import validate_result_manifest, validate_result_manifest_binding
from .results import LEGACY_SCOPE_NAMES


def artifact_paths(task_path: str) -> dict[str, str]:
    return {
        "manifest": f"{task_path}/result-manifest.json",
        "results": f"{task_path}/verification-results.json",
        "evidence": f"{task_path}/verification-evidence.json",
    }


def _fixed_json(root: Path, commit: str, path: str, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        require_regular_tree_file(root, commit, path, code)
        raw = read_tree_file(root, commit, path)
        value = json.loads(raw)
    except (TaskError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError(code) from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError(code)
    return value, raw


def _validate_verifier_results(
    value: dict[str, Any],
    base_sha: str,
    manifest_schema_version: int,
    scope_names: tuple[str, ...],
    lane: str | None,
    profile: str | None,
) -> None:
    keys = {
        "baseSha",
        "dependenciesInstalled",
        "outcome",
        "schemaVersion",
        "scopes",
        "tests",
    }
    if "canonicalResultsDigest" in value:
        keys.add("canonicalResultsDigest")
    if manifest_schema_version == 2:
        keys |= {"lane", "profile"}
    if set(value) != keys:
        raise TaskError("INVALID_VERIFIER_RESULTS")
    if (
        value["schemaVersion"] != manifest_schema_version
        or value["baseSha"] != base_sha
        or value["dependenciesInstalled"] is not False
        or value["outcome"] != "pass"
        or not isinstance(value["tests"], int)
        or isinstance(value["tests"], bool)
        or value["tests"] < 1
        or not isinstance(value["scopes"], dict)
        or set(value["scopes"]) != set(scope_names)
    ):
        raise TaskError("INVALID_VERIFIER_RESULTS")
    if manifest_schema_version == 1:
        if scope_names != LEGACY_SCOPE_NAMES:
            raise TaskError("INVALID_VERIFIER_RESULTS")
    elif value["lane"] != lane or value["profile"] != profile:
        raise TaskError("INVALID_VERIFIER_RESULTS")
    counts = list(value["scopes"].values())
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 1 for count in counts) or sum(counts) != value["tests"]:
        raise TaskError("INVALID_VERIFIER_RESULTS")
    if "canonicalResultsDigest" in value:
        require_sha256(value["canonicalResultsDigest"], "INVALID_VERIFIER_RESULTS")


def _validate_evidence(value: dict[str, Any], candidate_digest: str, verifier_digest: str) -> None:
    expected = {
        "schemaVersion",
        "kind",
        "outcome",
        "candidateOutputBundleDigest",
        "verifierResultDigest",
        "evidenceDigest",
    }
    if set(value) != expected or value["schemaVersion"] != 1 or value["kind"] != "automatic-delivery-evidence" or value["outcome"] != "pass":
        raise TaskError("INVALID_DELIVERY_EVIDENCE")
    require_sha256(value["candidateOutputBundleDigest"], "INVALID_DELIVERY_EVIDENCE")
    require_sha256(value["verifierResultDigest"], "INVALID_DELIVERY_EVIDENCE")
    require_sha256(value["evidenceDigest"], "INVALID_DELIVERY_EVIDENCE")
    unsigned = dict(value)
    digest = unsigned.pop("evidenceDigest")
    if (
        value["candidateOutputBundleDigest"] != candidate_digest
        or value["verifierResultDigest"] != verifier_digest
        or digest != digest_object(unsigned)
    ):
        raise TaskError("DELIVERY_EVIDENCE_BINDING_MISMATCH")


def load_automatic_delivery_artifacts(
    root: Path,
    implementation_head: str,
    state: dict[str, Any],
    candidate_output_bundle_digest: str,
    verifier_results_path: str,
    evidence_path: str,
) -> dict[str, str]:
    """Read, validate, and hash automatic-delivery artifacts from one fixed tree."""

    require_sha1(implementation_head, "RESULT_MANIFEST_REQUIRED")
    require_sha256(candidate_output_bundle_digest, "INVALID_CANDIDATE_OUTPUT_BUNDLE")
    paths = artifact_paths(state["repository"]["taskPath"])
    if verifier_results_path != paths["results"] or evidence_path != paths["evidence"]:
        raise TaskError("INVALID_DELIVERY_ARTIFACT_PATH")
    if not set(paths.values()).issubset(changed_paths(root, implementation_head)):
        raise TaskError("AUTOMATIC_DELIVERY_ARTIFACT_REQUIRED")
    manifest, _ = _fixed_json(root, implementation_head, paths["manifest"], "INVALID_RESULT_MANIFEST")
    scope_names = validate_result_manifest(manifest)
    manifest_schema_version = manifest["schemaVersion"]
    lane = manifest.get("lane")
    profile = manifest.get("profile")
    results, results_raw = _fixed_json(root, implementation_head, paths["results"], "INVALID_VERIFIER_RESULTS")
    _validate_verifier_results(
        results,
        state["repository"]["baseSha"],
        manifest_schema_version,
        scope_names,
        lane,
        profile,
    )
    verifier_digest = sha256_bytes(results_raw)
    evidence, evidence_raw = _fixed_json(root, implementation_head, paths["evidence"], "INVALID_DELIVERY_EVIDENCE")
    _validate_evidence(evidence, candidate_output_bundle_digest, verifier_digest)
    evidence_digest = sha256_bytes(evidence_raw)
    repository = state["repository"]
    validate_result_manifest_binding(
        manifest,
        state["taskId"],
        repository["identity"],
        repository["taskBranch"],
        repository["taskPath"],
        repository["baseSha"],
        candidate_output_bundle_digest,
        verifier_digest,
        evidence_digest,
    )
    return {"verifierResultDigest": verifier_digest, "evidenceDigest": evidence_digest}
