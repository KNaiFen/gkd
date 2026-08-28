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
SCOPE_NAMES = (
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
)
HISTORICAL_SCOPE_NAMES = ("watcher-core-and-live-negative",)
ALL_SCOPE_NAMES = SCOPE_NAMES + HISTORICAL_SCOPE_NAMES


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


def _validate_manifest(value: dict[str, Any]) -> None:
    _require(set(value) == {"baseSha", "environment", "headSha", "manifestDigest", "schemaVersion", "scopes", "verifierDigest"}, "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(value["schemaVersion"] == SCHEMA_VERSION, "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["baseSha"], str) and SHA1_RE.fullmatch(value["baseSha"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["headSha"], str) and SHA1_RE.fullmatch(value["headSha"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(isinstance(value["verifierDigest"], str) and SHA256_RE.fullmatch(value["verifierDigest"]), "CANONICAL_RESULT_SCHEMA_INVALID")
    _require(value["environment"] == environment_summary(), "CANONICAL_RESULT_ENVIRONMENT_MISMATCH")
    _require(value["scopes"] in (list(SCOPE_NAMES), list(HISTORICAL_SCOPE_NAMES)), "CANONICAL_RESULT_SCOPE_MISMATCH")
    digest = value["manifestDigest"]
    unsigned = dict(value)
    unsigned.pop("manifestDigest")
    _require(isinstance(digest, str) and SHA256_RE.fullmatch(digest) and digest_object(unsigned) == digest, "CANONICAL_RESULT_DIGEST_MISMATCH")


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


def load_canonical_results(results_dir: Path, scope: str, repository: Path, expected_ids: list[str] | None = None) -> dict[str, Any]:
    """Load and validate one scope result against this checkout's fixed head."""
    _require(scope in ALL_SCOPE_NAMES, "CANONICAL_RESULT_SCOPE_INVALID")
    _require(results_dir.is_dir() and not results_dir.is_symlink(), "CANONICAL_RESULT_MISSING")
    manifest, _ = _read(results_dir / "manifest.json", "CANONICAL_RESULT_MISSING")
    _validate_manifest(manifest)
    _require(scope in manifest["scopes"], "CANONICAL_RESULT_SCOPE_MISMATCH")
    _require(manifest["headSha"] == current_head(repository), "CANONICAL_RESULT_HEAD_MISMATCH")
    _require(_is_ancestor(repository, manifest["baseSha"], manifest["headSha"]), "CANONICAL_RESULT_BASE_MISMATCH")
    result, _ = _read(results_dir / f"{scope}.json", "CANONICAL_RESULT_MISSING")
    _validate_scope(result, scope, manifest, manifest["verifierDigest"])
    ids = [item["id"] for item in result["tests"]]
    if expected_ids is not None:
        expected = sorted(expected_ids)
        _require(len(expected) == len(set(expected)), "CANONICAL_RESULT_TEST_IDS_INVALID")
        _require(ids == expected, "CANONICAL_RESULT_TEST_IDS_MISMATCH")
    _require(result["status"] == "pass" and all(item["status"] == "pass" for item in result["tests"]), "CANONICAL_RESULT_TEST_FAILURE")
    return result


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


def write_manifest(path: Path, *, base_sha: str, head_sha: str, verifier_digest: str, scopes: list[str] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "baseSha": base_sha,
        "environment": environment_summary(),
        "headSha": head_sha,
        "schemaVersion": SCHEMA_VERSION,
        "scopes": list(SCOPE_NAMES) if scopes is None else list(scopes),
        "verifierDigest": verifier_digest,
    }
    value["manifestDigest"] = digest_object(value)
    path.write_bytes(canonical_bytes(value))
    return value
