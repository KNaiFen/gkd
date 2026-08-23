"""GitHub-only subprocess adapter for trusted task acceptance."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any

from .acceptance import validate_snapshot
from .canonical import CHECK_NAME_RE, canonical_bytes, require_sha1, require_string


MAX_INPUT_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$"
)
PENDING_CHECK_STATUSES = {"pending", "queued", "in_progress", "waiting", "requested"}
FAILED_CHECK_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "neutral",
    "stale",
    "startup_failure",
    "timed_out",
}


class AdapterError(Exception):
    """The GitHub response cannot satisfy the narrow acceptance contract."""


class MergeIndeterminate(Exception):
    """The single GitHub merge write may have taken effect."""


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterError
    return value


def _repository(value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or not value.startswith("github.com/"):
        raise AdapterError
    name = value.removeprefix("github.com/")
    if not REPOSITORY_RE.fullmatch(name):
        raise AdapterError
    return value, name


def _request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise AdapterError
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdapterError from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise AdapterError
    operation = value.get("operation")
    expected = {"operation", "repository", "prNumber"}
    if operation == "merge":
        expected.add("expectedHead")
    if operation not in {"snapshot", "merge"} or set(value) != expected:
        raise AdapterError
    _repository(value["repository"])
    if isinstance(value["prNumber"], bool) or not isinstance(value["prNumber"], int) or value["prNumber"] < 1:
        raise AdapterError
    if operation == "merge":
        require_sha1(value["expectedHead"], "INVALID_GITHUB_REQUEST")
    return value


def _gh_json(method: str, endpoint: str, *arguments: str, merge: bool = False) -> Any:
    try:
        result = subprocess.run(
            ("gh", "api", "--method", method, "-H", "Accept: application/vnd.github+json", endpoint, *arguments),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise AdapterError from None
    if merge and result.returncode == 75:
        raise MergeIndeterminate
    if result.returncode != 0 or len(result.stdout) > MAX_RESPONSE_BYTES:
        raise AdapterError
    try:
        return json.loads(result.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AdapterError from None


def _pull_snapshot(repository: str, name: str, pr_number: int) -> tuple[dict[str, Any], str]:
    pull = _object(_gh_json("GET", f"repos/{name}/pulls/{pr_number}"))
    base = _object(pull.get("base"))
    head = _object(pull.get("head"))
    base_repository = _object(base.get("repo"))
    head_repository = _object(head.get("repo"))
    base_name = base_repository.get("full_name")
    head_name = head_repository.get("full_name")
    if not isinstance(base_name, str) or not isinstance(head_name, str) or not REPOSITORY_RE.fullmatch(base_name) or not REPOSITORY_RE.fullmatch(head_name):
        raise AdapterError
    if base_name.casefold() != name.casefold():
        raise AdapterError
    number = pull.get("number")
    state = pull.get("state")
    draft = pull.get("draft")
    merged = pull.get("merged")
    mergeable = pull.get("mergeable")
    base_branch = base.get("ref")
    head_branch = head.get("ref")
    head_sha = head.get("sha")
    if (
        isinstance(number, bool)
        or not isinstance(number, int)
        or number != pr_number
        or state not in {"open", "closed"}
        or not isinstance(draft, bool)
        or not isinstance(merged, bool)
        or not isinstance(base_branch, str)
        or not isinstance(head_branch, str)
    ):
        raise AdapterError
    require_string(base_branch, "INVALID_GITHUB_RESPONSE")
    require_string(head_branch, "INVALID_GITHUB_RESPONSE")
    require_sha1(head_sha, "INVALID_GITHUB_RESPONSE")
    return {
        "repository": repository,
        "prNumber": pr_number,
        "baseBranch": base_branch,
        "headBranch": head_branch,
        "headSha": head_sha,
        "state": "merged" if merged else state,
        "draft": draft,
        "mergeable": mergeable is True,
        "checks": [],
        "mergedHead": head_sha if merged else None,
    }, head_sha


def _check_status(value: dict[str, Any], expected_head: str) -> tuple[str, str]:
    name = value.get("name")
    status = value.get("status")
    conclusion = value.get("conclusion")
    head_sha = value.get("head_sha")
    require_string(name, "INVALID_GITHUB_RESPONSE", CHECK_NAME_RE)
    require_sha1(head_sha, "INVALID_GITHUB_RESPONSE")
    if head_sha != expected_head or not isinstance(status, str):
        raise AdapterError
    if status in PENDING_CHECK_STATUSES and conclusion is None:
        return name, "pending"
    if status != "completed":
        raise AdapterError
    if conclusion == "success":
        return name, "success"
    if conclusion == "skipped":
        return name, "skipped"
    if conclusion in FAILED_CHECK_CONCLUSIONS:
        return name, "failure"
    raise AdapterError


def _checks(name: str, head_sha: str) -> list[dict[str, str]]:
    checks: dict[str, str] = {}
    expected_total: int | None = None
    for page in range(1, 101):
        response = _object(
            _gh_json("GET", f"repos/{name}/commits/{head_sha}/check-runs?per_page=100&page={page}")
        )
        if set(response) != {"check_runs", "total_count"}:
            raise AdapterError
        raw_checks = response["check_runs"]
        total = response["total_count"]
        if not isinstance(raw_checks, list) or isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise AdapterError
        if expected_total is None:
            expected_total = total
        elif expected_total != total:
            raise AdapterError
        for raw_check in raw_checks:
            check_name, status = _check_status(_object(raw_check), head_sha)
            if check_name in checks:
                raise AdapterError
            checks[check_name] = status
        if len(raw_checks) < 100:
            break
    else:
        raise AdapterError
    if expected_total is None or len(checks) != expected_total:
        raise AdapterError
    return [{"name": check_name, "status": checks[check_name]} for check_name in sorted(checks)]


def snapshot(request: dict[str, Any]) -> dict[str, Any]:
    repository, name = _repository(request["repository"])
    result, head_sha = _pull_snapshot(repository, name, request["prNumber"])
    if result["state"] == "open":
        result["checks"] = _checks(name, head_sha)
    validate_snapshot(result)
    return result


def merge(request: dict[str, Any]) -> dict[str, Any]:
    _, name = _repository(request["repository"])
    expected_head = request["expectedHead"]
    response = _object(
        _gh_json(
            "PUT",
            f"repos/{name}/pulls/{request['prNumber']}/merge",
            "-f",
            "merge_method=squash",
            "-f",
            f"sha={expected_head}",
            merge=True,
        )
    )
    if response.get("merged") is True:
        return {"status": "merged", "mergedHead": expected_head}
    if response.get("merged") is False:
        return {"status": "rejected", "mergedHead": None}
    raise AdapterError


def main() -> int:
    try:
        request = _request()
        result = snapshot(request) if request["operation"] == "snapshot" else merge(request)
    except MergeIndeterminate:
        return 75
    except (AdapterError, OSError, TypeError, ValueError):
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
