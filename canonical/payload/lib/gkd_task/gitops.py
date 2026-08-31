"""Verified Git identity and worktree operations."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any
from urllib.parse import urlsplit

from .canonical import relative_path, require_sha1
from .errors import TaskError


def git(root: Path, *args: str, code: str = "GIT_OPERATION_FAILED", input_data: bytes | None = None) -> bytes:
    try:
        environment = dict(os.environ)
        environment["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(
            ["git", "-C", os.fspath(root), *args],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            env=environment,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise TaskError(code) from None
    if result.returncode != 0:
        raise TaskError(code)
    return result.stdout


def reject_symlink_ancestors(path: Path, code: str) -> Path:
    """Reject symlinks in the lexical path before any physical resolution."""

    absolute = path if path.is_absolute() else Path.cwd() / path
    parts = absolute.parts
    temporary_aliases = {Path(os.sep, "var"), Path(os.sep, "tmp")}
    if len(parts) > 1 and Path(parts[0], parts[1]) in temporary_aliases:
        absolute = Path(parts[0], parts[1]).resolve().joinpath(*parts[2:])
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            raise TaskError(code) from None
        if stat.S_ISLNK(metadata.st_mode):
            raise TaskError(code)
    return absolute


def git_root(path: Path) -> Path:
    raw = git(path, "rev-parse", "--show-toplevel", code="INVALID_GIT_ROOT")
    try:
        root = Path(raw.decode("utf-8").strip()).resolve()
    except (UnicodeDecodeError, OSError):
        raise TaskError("INVALID_GIT_ROOT") from None
    if root.is_symlink() or not root.is_dir():
        raise TaskError("INVALID_GIT_ROOT")
    return root


def common_dir(root: Path) -> Path:
    raw = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", code="INVALID_GIT_ROOT")
    try:
        value = Path(raw.decode("utf-8").strip()).resolve()
    except (UnicodeDecodeError, OSError):
        raise TaskError("INVALID_GIT_ROOT") from None
    if not value.is_dir():
        raise TaskError("INVALID_GIT_ROOT")
    return value


def head(root: Path) -> str:
    try:
        value = git(root, "rev-parse", "HEAD", code="INVALID_GIT_HEAD").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("INVALID_GIT_HEAD") from None
    return require_sha1(value, "INVALID_GIT_HEAD")


def branch(root: Path) -> str:
    try:
        value = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", code="INVALID_GIT_BRANCH").decode("utf-8").strip()
    except UnicodeDecodeError:
        raise TaskError("INVALID_GIT_BRANCH") from None
    if not value or value.startswith("-") or any(part in {".", ".."} for part in value.split("/")):
        raise TaskError("INVALID_GIT_BRANCH")
    return value


def is_clean(root: Path) -> bool:
    return git(root, "status", "--porcelain=v1", "--untracked-files=all", code="GIT_STATUS_FAILED") == b""


def require_clean(root: Path) -> None:
    if not is_clean(root):
        raise TaskError("WORKTREE_NOT_CLEAN")


def normalize_remote(value: str) -> str:
    if "\x00" in value or any(character.isspace() for character in value):
        raise TaskError("INVALID_REPOSITORY_IDENTITY")
    host = ""
    path = ""
    if re.fullmatch(r"[^/@:]+@[^/:]+:.+", value):
        _, remainder = value.split("@", 1)
        host, path = remainder.split(":", 1)
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "ssh"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise TaskError("INVALID_REPOSITORY_IDENTITY")
        host = parsed.hostname
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not host or not path or path.startswith("/") or "//" in path or any(part in {"", ".", ".."} for part in path.split("/")):
        raise TaskError("INVALID_REPOSITORY_IDENTITY")
    identity = f"{host.lower()}/{path}"
    if not re.fullmatch(r"[a-z0-9.-]+/[A-Za-z0-9._/-]+", identity):
        raise TaskError("INVALID_REPOSITORY_IDENTITY")
    return identity


def repository_identity(root: Path) -> str:
    configured = subprocess.run(
        ["git", "-C", os.fspath(root), "config", "--get", "remote.origin.gkdIdentity"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if configured.returncode == 0:
        try:
            identity = configured.stdout.decode("utf-8").strip()
        except UnicodeDecodeError:
            raise TaskError("INVALID_REPOSITORY_IDENTITY") from None
        if not re.fullmatch(r"[a-z0-9.-]+/[A-Za-z0-9._/-]+", identity):
            raise TaskError("INVALID_REPOSITORY_IDENTITY")
        return identity
    if configured.returncode not in {0, 1}:
        raise TaskError("INVALID_REPOSITORY_IDENTITY")
    try:
        remote = git(root, "remote", "get-url", "origin", code="INVALID_REPOSITORY_IDENTITY").decode("utf-8").strip()
    except UnicodeDecodeError:
        raise TaskError("INVALID_REPOSITORY_IDENTITY") from None
    return normalize_remote(remote)


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    require_sha1(ancestor, "INVALID_GIT_HEAD")
    process = subprocess.run(
        ["git", "-C", os.fspath(root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if process.returncode not in {0, 1}:
        raise TaskError("GIT_OPERATION_FAILED")
    return process.returncode == 0


def verify_identity(
    root: Path,
    expected_repository: str,
    expected_branch: str,
    expected_common_dir: Path | None = None,
) -> Path:
    reject_symlink_ancestors(root, "CANDIDATE_SYMLINK")
    if root.is_symlink():
        raise TaskError("CANDIDATE_SYMLINK")
    if not root.is_dir():
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    actual = git_root(root)
    if actual != root.resolve() or repository_identity(actual) != expected_repository or branch(actual) != expected_branch:
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    if expected_common_dir is not None and common_dir(actual) != expected_common_dir.resolve():
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    return actual


def verified_relative_path(root: Path, value: str, code: str = "INVALID_TASK_PATH") -> Path:
    relative_path(value, code)
    current = root.resolve()
    for part in PurePosixPath(value).parts:
        current = current / part
        if current.is_symlink():
            raise TaskError(code)
    try:
        current.resolve(strict=False).relative_to(root.resolve())
    except (OSError, ValueError):
        raise TaskError(code) from None
    return current


def worktrees(root: Path) -> list[dict[str, str]]:
    try:
        text = git(root, "worktree", "list", "--porcelain", code="WORKTREE_DISCOVERY_FAILED").decode("utf-8")
    except UnicodeDecodeError:
        raise TaskError("WORKTREE_DISCOVERY_FAILED") from None
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"worktree", "HEAD", "branch"}:
            current[key] = value
    return records


def unique_branch_worktree(root: Path, expected_branch: str) -> Path:
    full = f"refs/heads/{expected_branch}"
    matches = [record for record in worktrees(root) if record.get("branch") == full]
    if not matches:
        raise TaskError("worktree_missing")
    if len(matches) != 1:
        raise TaskError("worktree_ambiguous")
    candidate = Path(matches[0]["worktree"])
    if candidate.is_symlink() or not candidate.is_dir():
        raise TaskError("worktree_missing")
    return candidate.resolve()


def read_tree_file(root: Path, commit: str, path: str) -> bytes:
    require_sha1(commit, "INVALID_GIT_HEAD")
    relative_path(path, "INVALID_FIXED_TREE_PATH")
    if PurePosixPath(path).is_absolute():
        raise TaskError("INVALID_FIXED_TREE_PATH")
    try:
        size_text = git(root, "cat-file", "-s", f"{commit}:{path}", code="CANDIDATE_INVALID").decode("ascii").strip()
        size = int(size_text)
    except (UnicodeDecodeError, ValueError):
        raise TaskError("CANDIDATE_INVALID") from None
    if size < 0 or size > 4 * 1024 * 1024:
        raise TaskError("CANDIDATE_INVALID")
    content = git(root, "show", f"{commit}:{path}", code="CANDIDATE_INVALID")
    if len(content) != size:
        raise TaskError("CANDIDATE_INVALID")
    return content


def require_regular_tree_file(root: Path, commit: str, path: str, code: str = "CANDIDATE_INVALID") -> None:
    require_sha1(commit, "INVALID_GIT_HEAD")
    relative_path(path, "INVALID_FIXED_TREE_PATH")
    raw = git(root, "ls-tree", "-z", commit, "--", path, code=code)
    entry = raw.rstrip(b"\x00")
    if not entry or entry.split(b" ", 1)[0] != b"100644":
        raise TaskError(code)


def changed_paths(root: Path, commit: str) -> list[str]:
    require_sha1(commit, "INVALID_GIT_HEAD")
    try:
        text = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode("utf-8")
    except UnicodeDecodeError:
        raise TaskError("GIT_OPERATION_FAILED") from None
    return sorted(line for line in text.splitlines() if line)


def commit_exact(root: Path, paths: list[str], message: str) -> str:
    normalized = sorted(set(relative_path(path, "INVALID_COORDINATION_PATH") for path in paths))
    if not normalized:
        raise TaskError("INVALID_COORDINATION_PATH")
    git(root, "add", "--all", "--", *normalized, code="GIT_STAGE_FAILED")
    try:
        staged = git(root, "diff", "--cached", "--name-only", "-z", code="GIT_STAGE_FAILED").decode("utf-8")
    except UnicodeDecodeError:
        raise TaskError("GIT_STAGE_FAILED") from None
    actual = sorted(value for value in staged.split("\x00") if value)
    if actual != normalized:
        raise TaskError("UNEXPECTED_STAGED_PATH")
    git(root, "commit", "-m", message, "--", *normalized, code="GIT_COMMIT_FAILED")
    return head(root)
