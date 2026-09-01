"""Strict request and result models for the watcher tool."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping

from .constants import (
    APPROVED_RUNTIME_DIGESTS,
    MAX_HEALTH_INTERVAL_MS,
    MAX_WAIT_MS,
    SCHEMA_VERSION,
)


ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CREDENTIAL_PATTERN = re.compile(
    r"(?:"
    r"gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|"
    r"glpat-[A-Za-z0-9_-]{20,}|"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,}"
    r")",
    re.IGNORECASE,
)
CREDENTIAL_SCHEMA_PATTERN = (
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"glpat-[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,})"
)
REQUEST_FIELDS = frozenset(
    {
        "schemaVersion",
        "taskId",
        "offerId",
        "sessionId",
        "childThreadId",
        "childTurnId",
        "parentThreadId",
        "expectedParentTurnId",
        "runtimeEvidenceDigest",
        "maxWaitMs",
        "healthIntervalMs",
    }
)
OUTCOMES = frozenset(
    {
        "normal_terminal",
        "abnormal_child",
        "deadline",
        "cancelled",
        "parent_steer_rejected",
        "protocol_error",
        "orchestrator_error",
    }
)


class RequestValidationError(ValueError):
    """A request failed before any external side effect was allowed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _require_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RequestValidationError(f"{field} must be an integer")
    return value


def _require_id(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not ID_PATTERN.fullmatch(value)
        or CREDENTIAL_PATTERN.search(value)
    ):
        raise RequestValidationError(f"{field} is invalid")
    return value


@dataclass(frozen=True)
class WatchRequest:
    schema_version: int
    task_id: str
    offer_id: str
    session_id: str
    child_thread_id: str
    child_turn_id: str
    parent_thread_id: str
    expected_parent_turn_id: str
    runtime_evidence_digest: str
    max_wait_ms: int
    health_interval_ms: int

    def __post_init__(self) -> None:
        _require_integer(self.schema_version, "schemaVersion")
        _require_integer(self.max_wait_ms, "maxWaitMs")
        _require_integer(self.health_interval_ms, "healthIntervalMs")
        if self.schema_version != SCHEMA_VERSION:
            raise RequestValidationError("unsupported schemaVersion")
        for field, value in (
            ("taskId", self.task_id),
            ("offerId", self.offer_id),
            ("sessionId", self.session_id),
            ("childThreadId", self.child_thread_id),
            ("childTurnId", self.child_turn_id),
            ("parentThreadId", self.parent_thread_id),
            ("expectedParentTurnId", self.expected_parent_turn_id),
        ):
            _require_id(value, field)
        if self.child_thread_id == self.parent_thread_id:
            raise RequestValidationError("parent and child thread IDs must differ")
        if self.runtime_evidence_digest not in APPROVED_RUNTIME_DIGESTS:
            raise RequestValidationError("runtimeEvidenceDigest is invalid")
        if not 0 < self.max_wait_ms <= MAX_WAIT_MS:
            raise RequestValidationError("maxWaitMs is outside the allowed range")
        if not 0 < self.health_interval_ms <= MAX_HEALTH_INTERVAL_MS:
            raise RequestValidationError(
                "healthIntervalMs is outside the allowed range"
            )

    @classmethod
    def parse(cls, raw: Any) -> "WatchRequest":
        if not isinstance(raw, Mapping):
            raise RequestValidationError("request must be an object")
        keys = set(raw)
        if keys != REQUEST_FIELDS:
            raise RequestValidationError("request fields do not match schema")

        schema_version = _require_integer(raw["schemaVersion"], "schemaVersion")
        if schema_version != SCHEMA_VERSION:
            raise RequestValidationError("unsupported schemaVersion")

        max_wait_ms = _require_integer(raw["maxWaitMs"], "maxWaitMs")
        health_interval_ms = _require_integer(
            raw["healthIntervalMs"], "healthIntervalMs"
        )
        if not 0 < max_wait_ms <= MAX_WAIT_MS:
            raise RequestValidationError("maxWaitMs is outside the allowed range")
        if not 0 < health_interval_ms <= MAX_HEALTH_INTERVAL_MS:
            raise RequestValidationError(
                "healthIntervalMs is outside the allowed range"
            )

        digest = raw["runtimeEvidenceDigest"]
        if (
            not isinstance(digest, str)
            or not DIGEST_PATTERN.fullmatch(digest)
            or digest not in APPROVED_RUNTIME_DIGESTS
        ):
            raise RequestValidationError("runtimeEvidenceDigest is invalid")

        child_thread_id = _require_id(raw["childThreadId"], "childThreadId")
        parent_thread_id = _require_id(raw["parentThreadId"], "parentThreadId")
        if child_thread_id == parent_thread_id:
            raise RequestValidationError("parent and child thread IDs must differ")

        return cls(
            schema_version=schema_version,
            task_id=_require_id(raw["taskId"], "taskId"),
            offer_id=_require_id(raw["offerId"], "offerId"),
            session_id=_require_id(raw["sessionId"], "sessionId"),
            child_thread_id=child_thread_id,
            child_turn_id=_require_id(raw["childTurnId"], "childTurnId"),
            parent_thread_id=parent_thread_id,
            expected_parent_turn_id=_require_id(
                raw["expectedParentTurnId"], "expectedParentTurnId"
            ),
            runtime_evidence_digest=digest,
            max_wait_ms=max_wait_ms,
            health_interval_ms=health_interval_ms,
        )

    def identity(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "taskId": self.task_id,
            "offerId": self.offer_id,
            "sessionId": self.session_id,
            "childThreadId": self.child_thread_id,
            "childTurnId": self.child_turn_id,
            "parentThreadId": self.parent_thread_id,
            "expectedParentTurnId": self.expected_parent_turn_id,
            "runtimeEvidenceDigest": self.runtime_evidence_digest,
        }


@dataclass(frozen=True)
class WatchResult:
    request: WatchRequest
    outcome: str
    reason: str
    health_checks: int
    elapsed_ms: int
    transcript_digest: str

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError("unsupported watcher outcome")
        if not ID_PATTERN.fullmatch(self.reason):
            raise ValueError("invalid watcher reason")
        if self.health_checks < 0 or self.elapsed_ms < 0:
            raise ValueError("watcher counters must be non-negative")
        if not DIGEST_PATTERN.fullmatch(self.transcript_digest):
            raise ValueError("invalid transcript digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.request.identity(),
            "outcome": self.outcome,
            "reason": self.reason,
            "healthChecks": self.health_checks,
            "elapsedMs": self.elapsed_ms,
            "transcriptDigest": self.transcript_digest,
        }


WATCH_REQUEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(REQUEST_FIELDS),
    "properties": {
        "schemaVersion": {"type": "integer", "const": SCHEMA_VERSION},
        "taskId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "offerId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "sessionId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "childThreadId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "childTurnId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "parentThreadId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "expectedParentTurnId": {
            "type": "string",
            "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
            "not": {"pattern": CREDENTIAL_SCHEMA_PATTERN},
        },
        "runtimeEvidenceDigest": {
            "type": "string",
            "enum": sorted(APPROVED_RUNTIME_DIGESTS),
        },
        "maxWaitMs": {"type": "integer", "minimum": 1, "maximum": MAX_WAIT_MS},
        "healthIntervalMs": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_HEALTH_INTERVAL_MS,
        },
    },
}
