"""Strict repository-local CI policy and GitHub origin validation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any
from urllib.parse import urlsplit

from gkd_task.canonical import digest_object, read_canonical_json, require_keys
from gkd_task.errors import TaskError


POLICY_PATH = ".gkd/policy.json"
REPOSITORY_RE = re.compile(
    r"^github\.com/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$"
)
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
CHECK_RE = re.compile(r"^[^\x00-\x20\x7f]{1}[^\x00-\x1f\x7f]{0,126}[^\x00-\x20\x7f]$|^[^\x00-\x20\x7f]$")


@dataclass(frozen=True)
class RepositoryPolicy:
    base_branch: str
    digest: str
    provider: str
    repository: str
    required_checks: tuple[str, ...]


def _valid_repository(value: Any) -> bool:
    if not isinstance(value, str) or not REPOSITORY_RE.fullmatch(value):
        return False
    owner, name = value.removeprefix("github.com/").split("/", 1)
    return ".." not in owner and ".." not in name and not name.casefold().endswith(".git")


def _valid_branch(value: Any) -> bool:
    return (
        isinstance(value, str)
        and BRANCH_RE.fullmatch(value) is not None
        and ".." not in value
        and "@{" not in value
        and not value.endswith((".", "/", ".lock"))
        and not value.startswith("/")
        and "//" not in value
    )


def _validate_policy(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"baseBranch", "provider", "repository", "requiredChecks", "schemaVersion"},
        "POLICY_INVALID",
    )
    checks = value["requiredChecks"]
    if (
        value["schemaVersion"] != 1
        or value["provider"] != "github"
        or not _valid_repository(value["repository"])
        or not _valid_branch(value["baseBranch"])
        or not isinstance(checks, list)
        or not checks
        or len(checks) > 64
        or any(not isinstance(check, str) or not CHECK_RE.fullmatch(check) for check in checks)
        or checks != sorted(checks)
        or len(checks) != len(set(checks))
    ):
        raise TaskError("POLICY_INVALID")


def _lexical_root(value: Path) -> Path:
    if ".." in value.parts:
        raise TaskError("CHECKOUT_PATH_INVALID")
    root = value if value.is_absolute() else Path.cwd() / value
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current /= part
        try:
            metadata = os.lstat(current)
        except OSError:
            raise TaskError("CHECKOUT_INVALID") from None
        if stat.S_ISLNK(metadata.st_mode):
            raise TaskError("CHECKOUT_PATH_SYMLINK")
    if not root.is_dir():
        raise TaskError("CHECKOUT_INVALID")
    return root


def _policy_file(checkout: Path, policy_path: str) -> Path:
    path = PurePosixPath(policy_path)
    if policy_path != POLICY_PATH or path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise TaskError("POLICY_PATH_UNSUPPORTED")
    current = checkout
    for part in path.parts:
        current /= part
        try:
            metadata = os.lstat(current)
        except OSError:
            raise TaskError("POLICY_INVALID") from None
        if stat.S_ISLNK(metadata.st_mode):
            raise TaskError("POLICY_PATH_SYMLINK")
    if not stat.S_ISREG(metadata.st_mode):
        raise TaskError("POLICY_INVALID")
    return current


def _git(checkout: Path, *arguments: str, code: str) -> list[str]:
    try:
        result = subprocess.run(
            ("git", *arguments),
            cwd=checkout,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise TaskError(code) from None
    if result.returncode != 0:
        raise TaskError(code)
    return result.stdout.splitlines()


def parse_github_remote(value: str) -> str:
    owner_repo: str | None = None
    if value.startswith("git@github.com:"):
        owner_repo = value.removeprefix("git@github.com:")
    else:
        parsed = urlsplit(value)
        if (
            parsed.scheme == "https"
            and parsed.hostname == "github.com"
            and parsed.username is None
            and parsed.password is None
            and parsed.port is None
            and not parsed.query
            and not parsed.fragment
        ):
            owner_repo = parsed.path.removeprefix("/")
        elif (
            parsed.scheme == "ssh"
            and parsed.hostname == "github.com"
            and parsed.username == "git"
            and parsed.password is None
            and parsed.port is None
            and not parsed.query
            and not parsed.fragment
        ):
            owner_repo = parsed.path.removeprefix("/")
    if owner_repo is None:
        raise TaskError("ORIGIN_UNSUPPORTED")
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    repository = f"github.com/{owner_repo}"
    if not _valid_repository(repository):
        raise TaskError("ORIGIN_UNSUPPORTED")
    return repository


def load_validated_policy(
    checkout_value: Path,
    repository: str,
    policy_path: str = POLICY_PATH,
) -> RepositoryPolicy:
    if not _valid_repository(repository):
        raise TaskError("REPOSITORY_INVALID")
    checkout = _lexical_root(checkout_value)
    top_levels = _git(checkout, "rev-parse", "--show-toplevel", code="CHECKOUT_INVALID")
    if len(top_levels) != 1 or Path(top_levels[0]).resolve() != checkout.resolve():
        raise TaskError("CHECKOUT_INVALID")
    path = _policy_file(checkout, policy_path)
    value = read_canonical_json(path, "POLICY_INVALID", _validate_policy)
    remote_values = _git(checkout, "config", "--get-all", "remote.origin.url", code="ORIGIN_MISSING")
    if len(remote_values) != 1:
        raise TaskError("ORIGIN_AMBIGUOUS")
    origin = parse_github_remote(remote_values[0])
    policy = RepositoryPolicy(
        base_branch=value["baseBranch"],
        digest=digest_object(value),
        provider=value["provider"],
        repository=value["repository"],
        required_checks=tuple(value["requiredChecks"]),
    )
    if origin.casefold() != policy.repository.casefold():
        raise TaskError("REPOSITORY_MISMATCH")
    if repository.casefold() != policy.repository.casefold():
        raise TaskError("REPOSITORY_MISMATCH")
    _git(
        checkout,
        "show-ref",
        "--verify",
        f"refs/remotes/origin/{policy.base_branch}",
        code="BASE_BRANCH_MISMATCH",
    )
    return policy
