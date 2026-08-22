"""Narrow read-only GitHub observation adapter."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import re
import subprocess
import time
from typing import Any, Callable

from gkd_task.canonical import require_sha1
from gkd_task.errors import TaskError

from .policy import _valid_branch


FULL_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$")
PENDING_CHECK_STATUSES = {"pending", "queued", "in_progress", "waiting", "requested"}
FAILED_CHECK_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "neutral",
    "skipped",
    "stale",
    "startup_failure",
    "timed_out",
}
FAILED_STATUS_STATES = {"error", "failure"}


@dataclass(frozen=True)
class GitHubObservation:
    base_branch: str
    checks: tuple[tuple[str, str], ...]
    head_branch: str
    head_sha: str
    pull_request: int
    repository: str
    state: str


def _full_name(value: Any) -> str:
    if not isinstance(value, str) or not FULL_NAME_RE.fullmatch(value):
        raise TaskError("GITHUB_RESPONSE_INVALID")
    return value


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("GITHUB_RESPONSE_INVALID")
    return value


def _string(value: Any) -> str:
    if not isinstance(value, str):
        raise TaskError("GITHUB_RESPONSE_INVALID")
    return value


class GitHubClient:
    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        deadline: float | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.runner = runner
        self.deadline = deadline
        self.monotonic = monotonic

    def _request(self, endpoint: str) -> Any:
        timeout = 30.0
        deadline_bounded = False
        if self.deadline is not None:
            remaining = self.deadline - self.monotonic()
            if remaining <= 0:
                raise TaskError("GITHUB_DEADLINE_EXHAUSTED")
            deadline_bounded = remaining <= timeout
            timeout = min(timeout, remaining)
        try:
            result = self.runner(
                (
                    "gh",
                    "api",
                    "--method",
                    "GET",
                    "-H",
                    "Accept: application/vnd.github+json",
                    endpoint,
                ),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            if deadline_bounded:
                raise TaskError("GITHUB_DEADLINE_EXHAUSTED") from None
            raise TaskError("GITHUB_QUERY_FAILED") from None
        except OSError:
            raise TaskError("GITHUB_QUERY_FAILED") from None
        if result.returncode != 0 or len(result.stdout.encode("utf-8")) > 4 * 1024 * 1024:
            raise TaskError("GITHUB_QUERY_FAILED")
        try:
            return json.loads(result.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TaskError("GITHUB_RESPONSE_INVALID") from None

    def _pages(self, endpoint: str, key: str | None) -> list[Any]:
        values: list[Any] = []
        expected_total: int | None = None
        for page in range(1, 101):
            separator = "&" if "?" in endpoint else "?"
            response = self._request(f"{endpoint}{separator}per_page=100&page={page}")
            if key is None:
                if not isinstance(response, list):
                    raise TaskError("GITHUB_RESPONSE_INVALID")
                page_values = response
            else:
                document = _object(response)
                if set(document) != {key, "total_count"}:
                    raise TaskError("GITHUB_RESPONSE_INVALID")
                page_values = document[key]
                total = document["total_count"]
                if not isinstance(page_values, list) or isinstance(total, bool) or not isinstance(total, int) or total < 0:
                    raise TaskError("GITHUB_RESPONSE_INVALID")
                if expected_total is None:
                    expected_total = total
                elif expected_total != total:
                    raise TaskError("GITHUB_RESPONSE_INVALID")
            values.extend(page_values)
            if len(page_values) < 100:
                break
        else:
            raise TaskError("GITHUB_RESPONSE_INVALID")
        if expected_total is not None and len(values) != expected_total:
            raise TaskError("GITHUB_RESPONSE_INVALID")
        return values

    def read_file(self, repository: str, path: str, ref: str) -> bytes:
        """Read one small repository file at one immutable GitHub commit."""

        if (
            not isinstance(repository, str)
            or not repository.startswith("github.com/")
            or not isinstance(path, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", path)
        ):
            raise TaskError("GITHUB_RESPONSE_INVALID")
        repository_path = _full_name(repository.removeprefix("github.com/"))
        require_sha1(ref, "GITHUB_RESPONSE_INVALID")
        document = _object(
            self._request(f"repos/{repository_path}/contents/{path}?ref={ref}")
        )
        content = document.get("content")
        encoded = content.replace("\n", "") if isinstance(content, str) else None
        if (
            document.get("type") != "file"
            or document.get("encoding") != "base64"
            or document.get("path") != path
            or document.get("name") != path.rsplit("/", 1)[-1]
            or not isinstance(document.get("size"), int)
            or isinstance(document.get("size"), bool)
            or not isinstance(encoded, str)
            or not re.fullmatch(r"[A-Za-z0-9+/=]*", encoded)
        ):
            raise TaskError("GITHUB_RESPONSE_INVALID")
        require_sha1(document.get("sha"), "GITHUB_RESPONSE_INVALID")
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except ValueError:
            raise TaskError("GITHUB_RESPONSE_INVALID") from None
        if len(decoded) != document["size"] or len(decoded) > 64 * 1024:
            raise TaskError("GITHUB_RESPONSE_INVALID")
        return decoded

    def observe(
        self,
        repository: str,
        pull_request: int,
        expected_head: str,
        required_checks: tuple[str, ...],
    ) -> GitHubObservation:
        repository_path = repository.removeprefix("github.com/")
        pull = _object(self._request(f"repos/{repository_path}/pulls/{pull_request}"))
        number = pull.get("number")
        state = pull.get("state")
        base = _object(pull.get("base"))
        head = _object(pull.get("head"))
        base_repo = _object(base.get("repo"))
        head_repo = _object(head.get("repo"))
        base_branch = _string(base.get("ref"))
        head_branch = _string(head.get("ref"))
        head_sha = _string(head.get("sha"))
        require_sha1(head_sha, "GITHUB_RESPONSE_INVALID")
        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or number != pull_request
            or state not in {"open", "closed"}
            or not _valid_branch(base_branch)
            or not _valid_branch(head_branch)
            or f"github.com/{_full_name(base_repo.get('full_name'))}".casefold() != repository.casefold()
        ):
            raise TaskError("GITHUB_RESPONSE_INVALID")
        _full_name(head_repo.get("full_name"))

        if head_sha != expected_head:
            return GitHubObservation(
                base_branch=base_branch,
                checks=(),
                head_branch=head_branch,
                head_sha=head_sha,
                pull_request=number,
                repository=f"github.com/{base_repo['full_name']}",
                state=state,
            )

        check_runs = self._pages(
            f"repos/{repository_path}/commits/{head_sha}/check-runs?",
            "check_runs",
        )
        statuses = self._pages(
            f"repos/{repository_path}/commits/{head_sha}/statuses?",
            None,
        )
        collected: dict[str, list[str]] = {name: [] for name in required_checks}
        for raw in check_runs:
            item = _object(raw)
            name = _string(item.get("name"))
            status = _string(item.get("status"))
            conclusion = item.get("conclusion")
            run_head = _string(item.get("head_sha"))
            require_sha1(run_head, "GITHUB_RESPONSE_INVALID")
            if run_head != head_sha:
                raise TaskError("GITHUB_RESPONSE_INVALID")
            if status in PENDING_CHECK_STATUSES and conclusion is None:
                normalized = "pending"
            elif status == "completed" and conclusion == "success":
                normalized = "success"
            elif status == "completed" and conclusion in FAILED_CHECK_CONCLUSIONS:
                normalized = "failure"
            else:
                raise TaskError("GITHUB_RESPONSE_INVALID")
            if name in collected:
                collected[name].append(normalized)
        for raw in statuses:
            item = _object(raw)
            name = _string(item.get("context"))
            status_head = _string(item.get("sha"))
            status = _string(item.get("state"))
            require_sha1(status_head, "GITHUB_RESPONSE_INVALID")
            if status_head != head_sha or status not in {"pending", "success", *FAILED_STATUS_STATES}:
                raise TaskError("GITHUB_RESPONSE_INVALID")
            normalized = "failure" if status in FAILED_STATUS_STATES else status
            if name in collected:
                collected[name].append(normalized)
        normalized_checks = []
        for name in required_checks:
            matches = collected[name]
            if len(matches) > 1:
                raise TaskError("REQUIRED_CHECK_AMBIGUOUS")
            if matches:
                normalized_checks.append((name, matches[0]))
        return GitHubObservation(
            base_branch=base_branch,
            checks=tuple(normalized_checks),
            head_branch=head_branch,
            head_sha=head_sha,
            pull_request=number,
            repository=f"github.com/{base_repo['full_name']}",
            state=state,
        )
