"""Versioned canonical scope results shared by verifier and evidence runners."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any


SCHEMA_VERSION = 1
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_SCOPE_NAMES = (
    "m5-release-candidate",
    "m4-finalization",
    "m3-ci-policy",
    "task-core",
    "role-routing",
    "runtime-bridge",
    "p1-production-migration",
    "foundation",
)

# O6 moves these two scopes to explicit optional lanes.  The current producer
# remains on the full default surface; consumers accept this fixed future core.
O6_CORE_SCOPE_NAMES = (
    "m5-release-candidate",
    "m4-finalization",
    "m3-ci-policy",
    "task-core",
    "role-routing",
    "runtime-bridge",
    "p1-production-migration",
    "foundation",
)

HISTORICAL_SCOPE_NAMES = (
    "watcher-core-and-live-negative",
)

CI_ADVICE_SCOPE_NAMES = ("m3-resource-scanner",)
REVIEW_REMEDIATION_SCOPE_NAMES = ("m3-review-core",)
OPTIONAL_PACK_SCOPE_NAMES = CI_ADVICE_SCOPE_NAMES + REVIEW_REMEDIATION_SCOPE_NAMES

LEGACY_SCOPE_NAMES = (
    "m5-release-candidate",
    "m4-finalization",
    "m3-ci-policy",
    "m3-resource-scanner",
    "m3-review-core",
    "task-core",
    "role-routing",
    "runtime-bridge",
    "p1-production-migration",
    "foundation",
    "watcher-core-and-live-negative",
)

# Existing result consumers retain this name for the default verifier contract.
SCOPE_NAMES = DEFAULT_SCOPE_NAMES

DEFAULT_LANE = "default"
DEFAULT_PROFILE = "core"
HISTORICAL_LANE = "historical"
HISTORICAL_PROFILE = "watcher"
CI_ADVICE_LANE = "optional-ci-advice"
CI_ADVICE_PROFILE = "ci-advice"
REVIEW_REMEDIATION_LANE = "optional-review-remediation"
REVIEW_REMEDIATION_PROFILE = "review-remediation"
OPTIONAL_PACK_LANE = "optional-packs"
OPTIONAL_PACK_PROFILE = "all"
LANE_PROFILES = {
    (DEFAULT_LANE, DEFAULT_PROFILE): DEFAULT_SCOPE_NAMES,
    (HISTORICAL_LANE, HISTORICAL_PROFILE): HISTORICAL_SCOPE_NAMES,
    (CI_ADVICE_LANE, CI_ADVICE_PROFILE): CI_ADVICE_SCOPE_NAMES,
    (REVIEW_REMEDIATION_LANE, REVIEW_REMEDIATION_PROFILE): REVIEW_REMEDIATION_SCOPE_NAMES,
    (OPTIONAL_PACK_LANE, OPTIONAL_PACK_PROFILE): OPTIONAL_PACK_SCOPE_NAMES,
}


class CanonicalResultError(ValueError):
    """A canonical result is missing, malformed, or not bound to this run."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def digest_object(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def environment_summary() -> dict[str, Any]:
    version = sys.version_info
    return {
        "dependenciesInstalled": False,
        "platform": platform.system().lower(),
        "pythonVersion": f"{version.major}.{version.minor}.{version.micro}",
    }


def current_head(root: Path) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), "rev-parse", "HEAD"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or not SHA1_RE.fullmatch(value):
        raise CanonicalResultError("CANONICAL_RESULT_HEAD_UNAVAILABLE")
    return value


def _is_ancestor(root: Path, base_sha: str, head_sha: str) -> bool:
    result = subprocess.run(
        ("git", "-C", str(root), "merge-base", "--is-ancestor", base_sha, head_sha),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CanonicalResultError(code)


def _read(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    _require(path.is_file() and not path.is_symlink(), code)
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CanonicalResultError(code) from error
    _require(isinstance(value, dict) and raw == canonical_bytes(value), "CANONICAL_RESULT_TAMPERED")
    return value, raw


def lane_profile_scopes(lane: str, profile: str) -> tuple[str, ...] | None:
    return LANE_PROFILES.get((lane, profile))


def valid_lane_profile_scopes(lane: str, profile: str) -> tuple[tuple[str, ...], ...]:
    """Return every strict scope contract accepted for a lane/profile pair."""

    current = lane_profile_scopes(lane, profile)
    if current is None:
        return ()
    if (lane, profile) == (DEFAULT_LANE, DEFAULT_PROFILE):
        return (DEFAULT_SCOPE_NAMES, O6_CORE_SCOPE_NAMES)
    return (current,)


def _validate_manifest(value: dict[str, Any]) -> tuple[str, ...]:
    legacy_keys = {"baseSha", "environment", "headSha", "manifestDigest", "schemaVersion", "scopes", "verifierDigest"}
    lane_keys = legacy_keys | {"lane", "profile"}
    if value.get("schemaVersion") == SCHEMA_VERSION:
        _require(set(value) == legacy_keys, "CANONICAL_RESULT_SCHEMA_INVALID")
        scope_names = LEGACY_SCOPE_NAMES
    elif value.get("schemaVersion") == 2:
        _require(set(value) == lane_keys, "CANONICAL_RESULT_SCHEMA_INVALID")
        _require(isinstance(value["lane"], str) and isinstance(value["profile"], str), "CANONICAL_RESULT_SCHEMA_INVALID")
        contracts = valid_lane_profile_scopes(value["lane"], value["profile"])
        _require(contracts, "CANONICAL_RESULT_SCHEMA_INVALID")
        _require(isinstance(value["scopes"], list), "CANONICAL_RESULT_SCOPE_MISMATCH")
        scope_names = tuple(value["scopes"])
        _require(scope_names in contracts, "CANONICAL_RESULT_SCOPE_MISMATCH")
    else:
        raise CanonicalResultError("CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["baseSha"], str) and SHA1_RE.fullmatch(value["baseSha"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["headSha"], str) and SHA1_RE.fullmatch(value["headSha"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["verifierDigest"], str) and SHA256_RE.fullmatch(value["verifierDigest"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(value["environment"] == environment_summary(), "CANONICAL_RESULT_ENVIRONMENT_MISMATCH")
    _require(value["scopes"] == list(scope_names), "CANONICAL_RESULT_SCOPE_MISMATCH")
    digest = value["manifestDigest"]
    unsigned = dict(value)
    unsigned.pop("manifestDigest")
    _require(isinstance(digest, str) and SHA256_RE.fullmatch(digest) and digest_object(unsigned) == digest, "CANONICAL_RESULT_DIGEST_MISMATCH")
    return scope_names


def _validate_scope(value: dict[str, Any], scope: str, manifest: dict[str, Any], verifier_digest: str) -> None:
    _require(set(value) == {"baseSha", "environment", "headSha", "resultDigest", "schemaVersion", "scope", "status", "tests", "verifierDigest"}, "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(value["schemaVersion"] == SCHEMA_VERSION and value["scope"] == scope, "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(value["baseSha"] == manifest["baseSha"] and value["headSha"] == manifest["headSha"], "CANONICAL_RESULT_HEAD_MISMATCH")
    _require(value["verifierDigest"] == verifier_digest, "CANONICAL_RESULT_DIGEST_MISMATCH")
    _require(value["environment"] == manifest["environment"], "CANONICAL_RESULT_ENVIRONMENT_MISMATCH")
    _require(value["status"] in {"pass", "fail"}, "CANONICAL_RESULT_SCHEMA_INVALID")
    tests = value["tests"]
    _require(isinstance(tests, list) and tests, "CANONICAL_RESULT_SCHEMA_INVALID")
    ids: list[str] = []
    for item in tests:
        _require(isinstance(item, dict) and set(item) == {"id", "status"}, "CANONICAL_RESULT_SCHEMA_INVALID")
        _require(isinstance(item["id"], str) and item["id"], "CANONICAL_RESULT_SCHEMA_INVALID")
        _require(item["status"] in {"pass", "fail", "error", "skip"}, "CANONICAL_RESULT_SCHEMA_INVALID")
        ids.append(item["id"])
    _require(ids == sorted(ids) and len(ids) == len(set(ids)), "CANONICAL_RESULT_TEST_IDS_INVALID")
    digest = value["resultDigest"]
    unsigned = dict(value)
    unsigned.pop("resultDigest")
    _require(isinstance(digest, str) and SHA256_RE.fullmatch(digest) and digest_object(unsigned) == digest, "CANONICAL_RESULT_DIGEST_MISMATCH")


def _strict_test_ids(test_ids: list[str]) -> list[str]:
    _require(isinstance(test_ids, list) and all(isinstance(test_id, str) and test_id for test_id in test_ids), "CANONICAL_RESULT_TEST_IDS_INVALID")
    ordered = sorted(test_ids)
    _require(len(ordered) == len(set(ordered)), "CANONICAL_RESULT_TEST_IDS_INVALID")
    return ordered


def load_canonical_results(results_dir: Path, scope: str, repository: Path, expected_ids: list[str] | None = None) -> dict[str, Any]:
    """Load and validate one scope result against this checkout's fixed head."""
    _require(results_dir.is_dir() and not results_dir.is_symlink(), "CANONICAL_RESULT_MISSING")
    manifest, _ = _read(results_dir / "manifest.json", "CANONICAL_RESULT_MISSING")
    scope_names = _validate_manifest(manifest)
    _require(scope in scope_names, "CANONICAL_RESULT_SCOPE_INVALID")
    _require(manifest["headSha"] == current_head(repository), "CANONICAL_RESULT_HEAD_MISMATCH")
    _require(_is_ancestor(repository, manifest["baseSha"], manifest["headSha"]), "CANONICAL_RESULT_BASE_MISMATCH")
    result, _ = _read(results_dir / f"{scope}.json", "CANONICAL_RESULT_MISSING")
    _validate_scope(result, scope, manifest, manifest["verifierDigest"])
    ids = [item["id"] for item in result["tests"]]
    if expected_ids is not None:
        expected = _strict_test_ids(expected_ids)
        _require(ids == expected, "CANONICAL_RESULT_TEST_IDS_MISMATCH")
    _require(result["status"] == "pass" and all(item["status"] == "pass" for item in result["tests"]), "CANONICAL_RESULT_TEST_FAILURE")
    return result


def select_canonical_results(
    results_dir: Path,
    scope: str,
    repository: Path,
    expected_ids: list[str],
    selected_ids: list[str],
) -> dict[str, Any]:
    """Return selected passing tests after validating the complete scope result."""

    expected = _strict_test_ids(expected_ids)
    selected = _strict_test_ids(selected_ids)
    _require(selected, "CANONICAL_RESULT_TEST_IDS_INVALID")
    result = load_canonical_results(results_dir, scope, repository, expected)
    available = {item["id"]: item for item in result["tests"]}
    _require(all(test_id in available for test_id in selected), "CANONICAL_RESULT_TEST_IDS_MISMATCH")
    return {
        "baseSha": result["baseSha"],
        "environment": result["environment"],
        "headSha": result["headSha"],
        "resultDigest": result["resultDigest"],
        "scope": result["scope"],
        "tests": [available[test_id] for test_id in selected],
        "verifierDigest": result["verifierDigest"],
    }


def write_scope_result(path: Path, *, base_sha: str, head_sha: str, scope: str, tests: list[dict[str, str]], verifier_digest: str) -> dict[str, Any]:
    value: dict[str, Any] = {
        "baseSha": base_sha,
        "environment": environment_summary(),
        "headSha": head_sha,
        "schemaVersion": SCHEMA_VERSION,
        "scope": scope,
        "status": "pass" if all(item["status"] == "pass" for item in tests) else "fail",
        "tests": sorted(tests, key=lambda item: item["id"]),
        "verifierDigest": verifier_digest,
    }
    value["resultDigest"] = digest_object(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))
    return value


def write_manifest(
    path: Path,
    *,
    base_sha: str,
    head_sha: str,
    verifier_digest: str,
    lane: str = DEFAULT_LANE,
    profile: str = DEFAULT_PROFILE,
) -> dict[str, Any]:
    scope_names = lane_profile_scopes(lane, profile)
    _require(scope_names is not None, "CANONICAL_RESULT_SCHEMA_INVALID")
    value: dict[str, Any] = {
        "baseSha": base_sha,
        "environment": environment_summary(),
        "headSha": head_sha,
        "lane": lane,
        "profile": profile,
        "schemaVersion": 2,
        "scopes": list(scope_names),
        "verifierDigest": verifier_digest,
    }
    value["manifestDigest"] = digest_object(value)
    path.write_bytes(canonical_bytes(value))
    return value
