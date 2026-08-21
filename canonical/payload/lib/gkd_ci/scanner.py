"""Fixed-scope, redacted secret scanner for declared CI surfaces."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, canonical_bytes, require_keys, require_sha256, sha256_bytes
from gkd_task.errors import TaskError


SURFACES = ("diff", "pull-request", "artifact")
MAX_DIFF_BYTES = 2 * 1024 * 1024
MAX_PULL_REQUEST_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_ARTIFACT_FILES = 256

_PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|auth(?:orization)?|password|secret|token)\b\s*[:=]\s*([^\s,;]+)"
)


def _bounded_text(value: Any, code: str, maximum: int) -> str:
    if not isinstance(value, str) or len(value.encode("utf-8")) > maximum or "\x00" in value:
        raise TaskError(code)
    return value


def _relative_surface_path(value: Any) -> str:
    if value is None:
        return "<surface>"
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")) or "\x00" in value:
        raise TaskError("SCANNER_INPUT_INVALID")
    parts = value.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in parts) or ":" in value:
        raise TaskError("SCANNER_INPUT_INVALID")
    return "/".join(parts)


def _candidate_rules(line: str) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for match in CREDENTIAL_RE.finditer(line):
        matches.append(("credential", match.group(0)))
    if _PRIVATE_KEY_RE.search(line):
        matches.append(("private-key", _PRIVATE_KEY_RE.search(line).group(0)))
    for match in _ASSIGNMENT_RE.finditer(line):
        value = match.group(1)
        if value not in {"", "null", "none", "redacted", "placeholder", "example"}:
            matches.append(("credential-assignment", value))
    return matches


def _scan_text(text: str, path: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for rule, candidate in _candidate_rules(line):
            del candidate
            findings.append(
                {
                    "line": line_number,
                    "path": path,
                    "rule": rule,
                    "redaction": "full-value",
                }
            )
    return findings


def _result(surface: str, input_digest: str, findings: list[dict[str, Any]], files: int) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "surface": surface,
        "inputDigest": input_digest,
        "filesScanned": files,
        "findings": findings,
        "outcome": "terminal" if findings else "clean",
        "terminal": bool(findings),
    }


def scan_diff(diff: str, path: str | None = None) -> dict[str, Any]:
    text = _bounded_text(diff, "SCANNER_INPUT_INVALID", MAX_DIFF_BYTES)
    safe_path = _relative_surface_path(path)
    return _result("diff", sha256_bytes(text.encode("utf-8")), _scan_text(text, safe_path), 1)


def scan_pull_request(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"title", "body", "files"}:
        raise TaskError("SCANNER_INPUT_INVALID")
    title = _bounded_text(value["title"], "SCANNER_INPUT_INVALID", MAX_PULL_REQUEST_BYTES)
    body = _bounded_text(value["body"], "SCANNER_INPUT_INVALID", MAX_PULL_REQUEST_BYTES)
    files = value["files"]
    if not isinstance(files, list) or len(files) > MAX_ARTIFACT_FILES:
        raise TaskError("SCANNER_INPUT_INVALID")
    total = len(title.encode("utf-8")) + len(body.encode("utf-8"))
    findings = _scan_text(title, "<title>") + _scan_text(body, "<body>")
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "patch"}:
            raise TaskError("SCANNER_INPUT_INVALID")
        safe_path = _relative_surface_path(item["path"])
        patch = _bounded_text(item["patch"], "SCANNER_INPUT_INVALID", MAX_PULL_REQUEST_BYTES)
        total += len(patch.encode("utf-8"))
        if total > MAX_PULL_REQUEST_BYTES:
            raise TaskError("SCANNER_INPUT_INVALID")
        findings.extend(_scan_text(patch, safe_path))
    return _result("pull-request", sha256_bytes(canonical_bytes(value)), findings, len(files) + 2)


def scan_artifact(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"files"}:
        raise TaskError("SCANNER_INPUT_INVALID")
    files = value["files"]
    if not isinstance(files, list) or not files or len(files) > MAX_ARTIFACT_FILES:
        raise TaskError("SCANNER_INPUT_INVALID")
    total = 0
    findings: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            raise TaskError("SCANNER_INPUT_INVALID")
        safe_path = _relative_surface_path(item["path"])
        content = _bounded_text(item["content"], "SCANNER_INPUT_INVALID", MAX_ARTIFACT_BYTES)
        total += len(content.encode("utf-8"))
        if total > MAX_ARTIFACT_BYTES:
            raise TaskError("SCANNER_INPUT_INVALID")
        findings.extend(_scan_text(content, safe_path))
    return _result("artifact", sha256_bytes(canonical_bytes(value)), findings, len(files))


def scan_surface(surface: str, value: Any, path: str | None = None) -> dict[str, Any]:
    if surface == "diff":
        if not isinstance(value, str):
            raise TaskError("SCANNER_INPUT_INVALID")
        return scan_diff(value, path)
    if surface == "pull-request":
        return scan_pull_request(value)
    if surface == "artifact":
        return scan_artifact(value)
    raise TaskError("SCANNER_SURFACE_INVALID")


def validate_scanner_result(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "surface", "inputDigest", "filesScanned", "findings", "outcome", "terminal"},
        "SCANNER_RESULT_INVALID",
    )
    if (
        value["schemaVersion"] != 1
        or value["surface"] not in SURFACES
        or not isinstance(value["inputDigest"], str)
        or not isinstance(value["filesScanned"], int)
        or value["filesScanned"] < 1
        or not isinstance(value["findings"], list)
        or value["outcome"] not in {"clean", "terminal"}
        or value["terminal"] != bool(value["findings"])
    ):
        raise TaskError("SCANNER_RESULT_INVALID")
    require_sha256(value["inputDigest"], "SCANNER_RESULT_INVALID")
    for finding in value["findings"]:
        if not isinstance(finding, dict) or set(finding) != {"line", "path", "rule", "redaction"}:
            raise TaskError("SCANNER_RESULT_INVALID")
        if (
            isinstance(finding["line"], bool)
            or not isinstance(finding["line"], int)
            or finding["line"] < 1
            or not isinstance(finding["path"], str)
            or not isinstance(finding["rule"], str)
            or finding["redaction"] != "full-value"
        ):
            raise TaskError("SCANNER_RESULT_INVALID")


def scanner_result_digest(value: dict[str, Any]) -> str:
    validate_scanner_result(value)
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
