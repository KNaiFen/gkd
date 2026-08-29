"""Shared fail-closed helpers for the GKD-M-1C live probe."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Mapping

from gkd_watchdog.constants import EXPECTED_SCHEMA_DIGEST, MAX_WAIT_MS
from gkd_watchdog.model import RequestValidationError, WatchRequest, canonical_json


LIVE_SCHEMA_VERSION = 1
LIVE_SCENARIOS = (
    "normal",
    "abnormal",
    "cas_reject",
    "orchestrator_failure",
)
STATE_FIELDS = frozenset(
    {
        "schemaVersion",
        "scenario",
        "taskId",
        "offerId",
        "sessionId",
        "parentThreadId",
        "parentTurnId",
        "childThreadId",
        "childTurnId",
        "wrongParentTurnId",
        "maxWaitMs",
        "healthIntervalMs",
    }
)
SAFE_NOTIFICATION_METHODS = frozenset(
    {
        "thread/started",
        "thread/status/changed",
        "turn/started",
        "turn/completed",
        "item/started",
        "item/completed",
    }
)
SAFE_ITEM_TYPES = frozenset(
    {
        "agentMessage",
        "collabAgentToolCall",
        "mcpToolCall",
        "reasoning",
    }
)
SAFE_STATUSES = frozenset(
    {
        "active",
        "completed",
        "failed",
        "idle",
        "inProgress",
        "interrupted",
        "notLoaded",
        "systemError",
    }
)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:(?<![A-Za-z0-9])/(?!/)[^\s\"']+|"
    r"(?:^|[\s\"'=])[A-Za-z]:[\\/][^\s\"']*|"
    r"(?:^|[\s\"'=])\\\\[^\\\s\"']+\\[^\s\"']+)"
)
CREDENTIAL_PATTERN = re.compile(
    r"(?:Authorization|Bearer\s+|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_|glpat-|sk-(?:proj-)?|xox[baprs]-|BEGIN PRIVATE KEY)",
    re.IGNORECASE,
)


class LiveProbeError(RuntimeError):
    """The probe cannot safely establish a required live fact."""


@dataclass(frozen=True)
class LiveBinding:
    scenario: str
    task_id: str
    offer_id: str
    session_id: str
    parent_thread_id: str
    parent_turn_id: str
    child_thread_id: str
    child_turn_id: str
    wrong_parent_turn_id: str
    max_wait_ms: int
    health_interval_ms: int

    @classmethod
    def parse(cls, value: Any) -> "LiveBinding":
        if not isinstance(value, Mapping) or set(value) != STATE_FIELDS:
            raise LiveProbeError("state_schema_mismatch")
        if value.get("schemaVersion") != LIVE_SCHEMA_VERSION:
            raise LiveProbeError("state_version_mismatch")
        scenario = value.get("scenario")
        if scenario not in LIVE_SCENARIOS:
            raise LiveProbeError("state_scenario_invalid")
        if value.get("maxWaitMs") != MAX_WAIT_MS:
            raise LiveProbeError("state_max_wait_mismatch")
        health_interval_ms = value.get("healthIntervalMs")
        if (
            isinstance(health_interval_ms, bool)
            or not isinstance(health_interval_ms, int)
            or not 0 < health_interval_ms <= 1_000
        ):
            raise LiveProbeError("state_health_interval_invalid")

        expected_parent_turn = (
            value["wrongParentTurnId"]
            if scenario == "cas_reject"
            else value["parentTurnId"]
        )
        try:
            request = WatchRequest.parse(
                {
                    "schemaVersion": 1,
                    "taskId": value["taskId"],
                    "offerId": value["offerId"],
                    "sessionId": value["sessionId"],
                    "childThreadId": value["childThreadId"],
                    "childTurnId": value["childTurnId"],
                    "parentThreadId": value["parentThreadId"],
                    "expectedParentTurnId": expected_parent_turn,
                    "runtimeEvidenceDigest": EXPECTED_SCHEMA_DIGEST,
                    "maxWaitMs": value["maxWaitMs"],
                    "healthIntervalMs": health_interval_ms,
                }
            )
        except RequestValidationError as exc:
            raise LiveProbeError("state_identity_ambiguity") from exc
        identities = {
            request.parent_thread_id,
            request.parent_thread_id if scenario == "cas_reject" else "",
            request.child_thread_id,
            request.child_turn_id,
            request.expected_parent_turn_id,
        }
        required_unique = {
            request.parent_thread_id,
            request.child_thread_id,
            request.child_turn_id,
            request.expected_parent_turn_id,
        }
        if len(required_unique) != 4 or "" in identities:
            raise LiveProbeError("state_identity_ambiguity")
        if scenario == "cas_reject" and value["wrongParentTurnId"] == value["parentTurnId"]:
            raise LiveProbeError("state_expected_turn_not_wrong")
        return cls(
            scenario=scenario,
            task_id=request.task_id,
            offer_id=request.offer_id,
            session_id=request.session_id,
            parent_thread_id=request.parent_thread_id,
            parent_turn_id=value["parentTurnId"],
            child_thread_id=request.child_thread_id,
            child_turn_id=request.child_turn_id,
            wrong_parent_turn_id=value["wrongParentTurnId"],
            max_wait_ms=request.max_wait_ms,
            health_interval_ms=request.health_interval_ms,
        )

    def watch_request(self) -> WatchRequest:
        expected = (
            self.wrong_parent_turn_id
            if self.scenario == "cas_reject"
            else self.parent_turn_id
        )
        return WatchRequest.parse(
            {
                "schemaVersion": 1,
                "taskId": self.task_id,
                "offerId": self.offer_id,
                "sessionId": self.session_id,
                "childThreadId": self.child_thread_id,
                "childTurnId": self.child_turn_id,
                "parentThreadId": self.parent_thread_id,
                "expectedParentTurnId": expected,
                "runtimeEvidenceDigest": EXPECTED_SCHEMA_DIGEST,
                "maxWaitMs": self.max_wait_ms,
                "healthIntervalMs": self.health_interval_ms,
            }
        )


def read_binding(path: Path, *, timeout_seconds: float = 20.0) -> LiveBinding:
    deadline = time.monotonic() + timeout_seconds
    last_reason = "state_unavailable"
    while time.monotonic() < deadline:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return LiveBinding.parse(raw)
        except FileNotFoundError:
            last_reason = "state_unavailable"
        except json.JSONDecodeError:
            last_reason = "state_malformed"
        except LiveProbeError as exc:
            last_reason = str(exc)
            if last_reason not in {
                "state_schema_mismatch",
                "state_unavailable",
            }:
                raise
        time.sleep(0.025)
    raise LiveProbeError(last_reason)


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(canonical_json(value) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def identity_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _status(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("type")
    return value if isinstance(value, str) and value in SAFE_STATUSES else None


class NotificationTrace:
    """Reduce raw app-server notifications to enum/count-only evidence."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._item_counts: Counter[str] = Counter()
        self._status_counts: Counter[str] = Counter()
        self._terminal_keys: set[tuple[str, str]] = set()

    def accept(self, notification: Mapping[str, Any]) -> dict[str, Any]:
        method_value = notification.get("method")
        method = (
            method_value
            if isinstance(method_value, str)
            and method_value in SAFE_NOTIFICATION_METHODS
            else "other_notification"
        )
        params = notification.get("params")
        if not isinstance(params, Mapping):
            raise LiveProbeError("notification_params_invalid")
        self._counts[method] += 1

        item = params.get("item")
        item_type = item.get("type") if isinstance(item, Mapping) else None
        safe_item_type = item_type if item_type in SAFE_ITEM_TYPES else None
        if safe_item_type is not None:
            self._item_counts[f"{method}:{safe_item_type}"] += 1

        status = _status(params.get("status"))
        turn = params.get("turn")
        if status is None and isinstance(turn, Mapping):
            status = _status(turn.get("status"))
        if status is None and isinstance(item, Mapping):
            status = _status(item.get("status"))
        if status is not None:
            self._status_counts[f"{method}:{status}"] += 1

        if method == "turn/completed":
            thread_id = params.get("threadId")
            turn_id = turn.get("id") if isinstance(turn, Mapping) else None
            if not isinstance(thread_id, str) or not isinstance(turn_id, str):
                raise LiveProbeError("terminal_identity_missing")
            terminal_key = (thread_id, turn_id)
            if terminal_key in self._terminal_keys:
                raise LiveProbeError("duplicate_terminal")
            self._terminal_keys.add(terminal_key)

        return {
            "method": method,
            "itemType": safe_item_type,
            "status": status,
            "fieldNames": sorted(
                field
                for field in params
                if field in {"item", "status", "thread", "threadId", "turn"}
            ),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "methodCounts": dict(sorted(self._counts.items())),
            "itemCounts": dict(sorted(self._item_counts.items())),
            "statusCounts": dict(sorted(self._status_counts.items())),
            "terminalCount": len(self._terminal_keys),
        }


def assert_evidence_safe(value: Any, *, prohibited: tuple[str, ...] = ()) -> None:
    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, nested in node.items():
                visit(key)
                visit(nested)
        elif isinstance(node, list):
            for nested in node:
                visit(nested)
        elif isinstance(node, str):
            if ABSOLUTE_PATH_PATTERN.search(node) or CREDENTIAL_PATTERN.search(node):
                raise LiveProbeError("evidence_sensitive_value")
            if any(secret and secret in node for secret in prohibited):
                raise LiveProbeError("evidence_raw_identity")

    visit(value)


def normalized_digest(evidence: Mapping[str, Any]) -> str:
    gates = evidence.get("gates", {})
    normalized = {
        "schemaVersion": evidence.get("schemaVersion"),
        "outcome": evidence.get("outcome"),
        "runtime": evidence.get("runtime"),
        "m1bContracts": evidence.get("m1bContracts"),
        "productionConfig": {
            "beforeAfterMatch": evidence.get("productionConfig", {}).get(
                "beforeAfterMatch"
            )
        },
        "cleanup": evidence.get("cleanup"),
        "security": evidence.get("security"),
        "wallClockSoakClaimed": evidence.get("wallClockSoakClaimed"),
        "normalization": evidence.get("normalization"),
        "gates": {
            key: {
                "status": value.get("status"),
                "reason": value.get("reason"),
            }
            for key, value in sorted(gates.items())
            if isinstance(value, Mapping)
        },
    }
    return hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
