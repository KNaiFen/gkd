"""Strict, repository-neutral adapter facts for multi-repository reviews."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, canonical_bytes, digest_object, require_keys, require_sha256
from gkd_task.errors import TaskError


PROVIDERS = ("bitbucket", "github", "gitlab", "unknown")
CAPABILITIES = ("artifacts", "checks", "diff", "pullRequest")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
POLICY_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]{1,255}$")


def _text(value: Any, code: str, pattern: re.Pattern[str], maximum: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum:
        raise TaskError(code)
    if not pattern.fullmatch(value) or CREDENTIAL_RE.search(value):
        raise TaskError(code)
    if value.startswith(("/", "\\")) or "\x00" in value or ":\\" in value:
        raise TaskError(code)
    return value


def _repository(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"id", "identity", "provider", "defaultBranch", "policyPath", "capabilities"}:
        raise TaskError("ADAPTER_REPOSITORY_INVALID")
    repository = {
        "id": _text(value["id"], "ADAPTER_REPOSITORY_INVALID", ID_RE, 64),
        "identity": _text(value["identity"], "ADAPTER_REPOSITORY_INVALID", IDENTITY_RE, 192),
        "provider": value["provider"],
        "defaultBranch": _text(value["defaultBranch"], "ADAPTER_REPOSITORY_INVALID", BRANCH_RE, 128),
        "policyPath": _text(value["policyPath"], "ADAPTER_REPOSITORY_INVALID", POLICY_PATH_RE, 256),
        "capabilities": value["capabilities"],
    }
    if repository["provider"] not in PROVIDERS:
        raise TaskError("ADAPTER_REPOSITORY_INVALID")
    if any(part in {"", ".", ".."} for part in repository["policyPath"].split("/")):
        raise TaskError("ADAPTER_REPOSITORY_INVALID")
    if not isinstance(repository["capabilities"], dict) or set(repository["capabilities"]) != set(CAPABILITIES):
        raise TaskError("ADAPTER_REPOSITORY_INVALID")
    if any(not isinstance(repository["capabilities"][name], bool) for name in CAPABILITIES):
        raise TaskError("ADAPTER_REPOSITORY_INVALID")
    return repository


def _without_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop("adapterDigest", None)
    return result


def validate_adapter(value: dict[str, Any]) -> None:
    require_keys(value, {"schemaVersion", "adapterName", "repositories", "adapterDigest"}, "ADAPTER_INVALID")
    if value["schemaVersion"] != 1:
        raise TaskError("ADAPTER_INVALID")
    _text(value["adapterName"], "ADAPTER_INVALID", ID_RE, 64)
    repositories = value["repositories"]
    if not isinstance(repositories, list) or not repositories:
        raise TaskError("ADAPTER_INVALID")
    normalized = [_repository(item) for item in repositories]
    if [item["id"] for item in normalized] != sorted({item["id"] for item in normalized}):
        raise TaskError("ADAPTER_INVALID")
    require_sha256(value["adapterDigest"], "ADAPTER_INVALID")
    if value["adapterDigest"] != digest_object(_without_digest(value)):
        raise TaskError("ADAPTER_INVALID")


def build_adapter(adapter_name: str, repositories: list[dict[str, Any]]) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "adapterName": _text(adapter_name, "ADAPTER_INVALID", ID_RE, 64),
        "repositories": sorted((_repository(item) for item in repositories), key=lambda item: item["id"]),
    }
    value["adapterDigest"] = digest_object(value)
    validate_adapter(value)
    return value


def adapter_digest(value: dict[str, Any]) -> str:
    validate_adapter(value)
    return value["adapterDigest"]


def canonical_adapter(value: dict[str, Any]) -> bytes:
    validate_adapter(value)
    return canonical_bytes(value)
