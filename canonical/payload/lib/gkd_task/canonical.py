"""Canonical encoding, strict reads, and deterministic internal seams."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import tempfile
from typing import Any, Callable

from .errors import TaskError


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CREDENTIAL_RE = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|Bearer\s+\S+)", re.IGNORECASE)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_object(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def require_keys(value: dict[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise TaskError(code)


def require_string(value: Any, code: str, pattern: re.Pattern[str] = IDENTIFIER_RE) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value) or CREDENTIAL_RE.search(value):
        raise TaskError(code)
    return value


def require_sha1(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA1_RE.fullmatch(value):
        raise TaskError(code)
    return value


def require_sha256(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise TaskError(code)
    return value


def require_utc(value: Any, code: str) -> str:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise TaskError(code)
    return value


def relative_path(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
        raise TaskError(code)
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {".", ".."} for part in path.parts):
        raise TaskError(code)
    return value


def regular_file(path: Path, code: str) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError:
        raise TaskError(code) from None
    if not stat.S_ISREG(metadata.st_mode):
        raise TaskError(code)
    return metadata


def read_canonical_json(
    path: Path,
    code: str,
    validator: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    metadata = regular_file(path, code)
    if metadata.st_size > 4 * 1024 * 1024:
        raise TaskError(code)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError(code) from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError(code)
    if validator is not None:
        validator(value)
    return value


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def atomic_write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def unlink_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError:
        raise TaskError("FILESYSTEM_ERROR") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise TaskError("FILESYSTEM_ERROR")
    path.unlink()
    fsync_directory(path.parent)


class SystemClock:
    def now(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


class SystemNonce:
    def token(self, size: int = 32) -> str:
        return secrets.token_urlsafe(size)


class FixedClock:
    """Internal deterministic seam used only by contract fixtures."""

    def __init__(self, value: str) -> None:
        self.value = require_utc(value, "INVALID_TEST_CLOCK")

    def now(self) -> str:
        return self.value


class FixedNonce:
    """Internal deterministic seam used only by contract fixtures."""

    def __init__(self, values: list[str]) -> None:
        self.values = iter(values)

    def token(self, size: int = 32) -> str:
        del size
        try:
            return next(self.values)
        except StopIteration:
            raise TaskError("TEST_NONCE_EXHAUSTED") from None
