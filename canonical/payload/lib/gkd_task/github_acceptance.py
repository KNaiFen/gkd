"""Narrow GitHub REST adapter for trusted acceptance."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any, Callable

from .acceptance import MergeIndeterminate, validate_snapshot
from .canonical import CHECK_NAME_RE, canonical_bytes, require_sha1, require_string
from .errors import TaskError


REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$"
)
MAX_BYTES = 4 * 1024 * 1024
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


def _repository_path(repository: Any) -> str:
    if not isinstance(repository, str) or not repository.startswith("github.com/"):
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    value = repository.removeprefix("github.com/")
    if not REPOSITORY_RE.fullmatch(value):
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    return value


def _request(value: Any) -> tuple[str, str, int, str | None]:
    if not isinstance(value, dict):
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    operation = value.get("operation")
    if operation == "snapshot":
        expected = {"operation", "repository", "prNumber"}
        expected_head = None
    elif operation == "merge":
        expected = {"operation", "repository", "prNumber", "expectedHead"}
        expected_head = value.get("expectedHead")
        require_sha1(expected_head, "INVALID_GITHUB_ADAPTER_REQUEST")
    else:
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    if set(value) != expected:
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    number = value.get("prNumber")
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    repository = value["repository"]
    return operation, repository, number, expected_head


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("INVALID_GITHUB_RESPONSE")
    return value


class GitHubAcceptanceAdapter:
    def __init__(self, runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run) -> None:
        self._runner = runner

    def _api(self, method: str, endpoint: str, fields: tuple[tuple[str, str], ...] = ()) -> Any:
        command = [
            "gh",
            "api",
            "--method",
            method,
            "-H",
            "Accept: application/vnd.github+json",
            endpoint,
        ]
        for name, value in fields:
            command.extend(("--raw-field", f"{name}={value}"))
        try:
            result = self._runner(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise TaskError("GITHUB_ADAPTER_FAILED") from None
        if result.returncode == 75 and method == "PUT":
            raise MergeIndeterminate()
        if result.returncode != 0 or len(result.stdout) > MAX_BYTES:
            raise TaskError("GITHUB_ADAPTER_FAILED")
        try:
            return json.loads(result.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TaskError("INVALID_GITHUB_RESPONSE") from None

    def _pages(self, endpoint: str, key: str | None) -> list[Any]:
        values: list[Any] = []
        expected_total: int | None = None
        for page in range(1, 101):
            response = self._api("GET", f"{endpoint}?per_page=100&page={page}")
            if key is None:
                if not isinstance(response, list):
                    raise TaskError("INVALID_GITHUB_RESPONSE")
                page_values = response
            else:
                document = _object(response)
                page_values = document.get(key)
                total = document.get("total_count")
                if (
                    not isinstance(page_values, list)
                    or isinstance(total, bool)
                    or not isinstance(total, int)
                    or total < 0
                ):
                    raise TaskError("INVALID_GITHUB_RESPONSE")
                if expected_total is None:
                    expected_total = total
                elif expected_total != total:
                    raise TaskError("INVALID_GITHUB_RESPONSE")
            values.extend(page_values)
            if len(page_values) < 100:
                break
        else:
            raise TaskError("INVALID_GITHUB_RESPONSE")
        if expected_total is not None and len(values) != expected_total:
            raise TaskError("INVALID_GITHUB_RESPONSE")
        return values

    @staticmethod
    def _add_check(checks: dict[str, str], name: Any, status: str) -> None:
        name = require_string(name, "INVALID_GITHUB_RESPONSE", CHECK_NAME_RE)
        if name in checks:
            raise TaskError("INVALID_GITHUB_RESPONSE")
        checks[name] = status

    def _checks(self, repository_path: str, head_sha: str) -> list[dict[str, str]]:
        checks: dict[str, str] = {}
        for raw in self._pages(f"repos/{repository_path}/commits/{head_sha}/check-runs", "check_runs"):
            item = _object(raw)
            name = item.get("name")
            status = item.get("status")
            conclusion = item.get("conclusion")
            run_head = item.get("head_sha")
            require_sha1(run_head, "INVALID_GITHUB_RESPONSE")
            if run_head != head_sha or not isinstance(status, str):
                raise TaskError("INVALID_GITHUB_RESPONSE")
            if status in PENDING_CHECK_STATUSES and conclusion is None:
                normalized = "pending"
            elif status == "completed" and conclusion == "success":
                normalized = "success"
            elif status == "completed" and conclusion == "skipped":
                normalized = "skipped"
            elif status == "completed" and conclusion in FAILED_CHECK_CONCLUSIONS:
                normalized = "failure"
            else:
                raise TaskError("INVALID_GITHUB_RESPONSE")
            self._add_check(checks, name, normalized)
        for raw in self._pages(f"repos/{repository_path}/commits/{head_sha}/statuses", None):
            item = _object(raw)
            name = item.get("context")
            status_head = item.get("sha")
            status = item.get("state")
            require_sha1(status_head, "INVALID_GITHUB_RESPONSE")
            if status_head != head_sha or status not in {"pending", "success", "error", "failure"}:
                raise TaskError("INVALID_GITHUB_RESPONSE")
            self._add_check(checks, name, "failure" if status in {"error", "failure"} else status)
        return [{"name": name, "status": checks[name]} for name in sorted(checks)]

    def snapshot(self, repository: str, pr_number: int) -> dict[str, Any]:
        repository_path = _repository_path(repository)
        pull = _object(self._api("GET", f"repos/{repository_path}/pulls/{pr_number}"))
        base = _object(pull.get("base"))
        head = _object(pull.get("head"))
        base_repository = _object(base.get("repo"))
        _object(head.get("repo"))
        number = pull.get("number")
        raw_state = pull.get("state")
        merged_at = pull.get("merged_at")
        draft = pull.get("draft")
        mergeable = pull.get("mergeable")
        base_branch = base.get("ref")
        head_branch = head.get("ref")
        head_sha = head.get("sha")
        full_name = base_repository.get("full_name")
        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or number != pr_number
            or raw_state not in {"open", "closed"}
            or merged_at is not None and not isinstance(merged_at, str)
            or not isinstance(draft, bool)
            or (mergeable is not True and mergeable is not False and mergeable is not None)
        ):
            raise TaskError("INVALID_GITHUB_RESPONSE")
        base_branch = require_string(base_branch, "INVALID_GITHUB_RESPONSE")
        head_branch = require_string(head_branch, "INVALID_GITHUB_RESPONSE")
        require_sha1(head_sha, "INVALID_GITHUB_RESPONSE")
        if not isinstance(full_name, str) or not REPOSITORY_RE.fullmatch(full_name):
            raise TaskError("INVALID_GITHUB_RESPONSE")
        state = "merged" if merged_at is not None else raw_state
        snapshot = {
            "repository": f"github.com/{full_name}",
            "prNumber": number,
            "baseBranch": base_branch,
            "headBranch": head_branch,
            "headSha": head_sha,
            "state": state,
            "draft": draft,
            "mergeable": mergeable is True,
            "checks": [] if state != "open" else self._checks(repository_path, head_sha),
            "mergedHead": head_sha if state == "merged" else None,
        }
        validate_snapshot(snapshot)
        return snapshot

    def merge(self, repository: str, pr_number: int, expected_head: str) -> dict[str, Any]:
        repository_path = _repository_path(repository)
        require_sha1(expected_head, "INVALID_GITHUB_ADAPTER_REQUEST")
        result = _object(
            self._api(
                "PUT",
                f"repos/{repository_path}/pulls/{pr_number}/merge",
                (("sha", expected_head), ("merge_method", "squash")),
            )
        )
        if result.get("merged") is True:
            return {"status": "merged", "mergedHead": expected_head}
        if result.get("merged") is False:
            return {"status": "rejected", "mergedHead": None}
        raise TaskError("INVALID_GITHUB_RESPONSE")


def _read_request() -> tuple[str, str, int, str | None]:
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST") from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError("INVALID_GITHUB_ADAPTER_REQUEST")
    return _request(value)


def main() -> int:
    try:
        operation, repository, pr_number, expected_head = _read_request()
        adapter = GitHubAcceptanceAdapter()
        result = (
            adapter.snapshot(repository, pr_number)
            if operation == "snapshot"
            else adapter.merge(repository, pr_number, expected_head)
        )
    except MergeIndeterminate:
        return 75
    except (TaskError, OSError, UnicodeDecodeError, ValueError, TypeError, KeyError):
        return 1
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
