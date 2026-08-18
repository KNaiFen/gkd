from __future__ import annotations

from collections import deque
import hashlib
import threading
import time
from typing import Any, Mapping

from gkd_watchdog.constants import EXPECTED_SCHEMA_DIGEST
from gkd_watchdog.jsonrpc import AppServerRemoteError
from gkd_watchdog.model import WatchRequest, canonical_json


def valid_request(**overrides: Any) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "taskId": "GKD-M-1B",
        "offerId": "offer-1",
        "sessionId": "session-1",
        "childThreadId": "child-thread-1",
        "childTurnId": "child-turn-1",
        "parentThreadId": "parent-thread-1",
        "expectedParentTurnId": "parent-turn-1",
        "runtimeEvidenceDigest": EXPECTED_SCHEMA_DIGEST,
        "maxWaitMs": 43_200_000,
        "healthIntervalMs": 3_600_000,
    }
    value.update(overrides)
    return value


def parsed_request(**overrides: Any) -> WatchRequest:
    return WatchRequest.parse(valid_request(**overrides))


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance_ms(self, milliseconds: int) -> None:
        self.now += milliseconds / 1000


class ScriptedSession:
    def __init__(
        self,
        clock: FakeClock,
        *,
        statuses: list[str] | None = None,
        notifications: list[tuple[int, dict[str, Any]]] | None = None,
        remote_errors: Mapping[str, str] | None = None,
    ) -> None:
        self.clock = clock
        self.statuses = deque(statuses or ["active"])
        self.last_status = self.statuses[-1]
        self.notifications = deque(
            sorted(notifications or [], key=lambda item: item[0])
        )
        self.remote_errors = dict(remote_errors or {})
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False
        self._safe_transcript: list[dict[str, Any]] = []

    @property
    def transcript(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(entry) for entry in self._safe_transcript)

    def transcript_digest(self) -> str:
        return hashlib.sha256(
            canonical_json(self._safe_transcript).encode("utf-8")
        ).hexdigest()

    def request(
        self, method: str, params: Mapping[str, Any], *, timeout_ms: int
    ) -> Any:
        copied = dict(params)
        self.calls.append((method, copied))
        self._safe_transcript.append(
            {"method": method, "fieldNames": sorted(copied), "status": "request"}
        )
        if method in self.remote_errors:
            raise AppServerRemoteError(self.remote_errors[method])
        if method == "thread/read":
            thread_id = params["threadId"]
            is_child = thread_id == "child-thread-1"
            if is_child and self.statuses:
                self.last_status = self.statuses.popleft()
            return {
                "thread": {
                    "id": thread_id,
                    "sessionId": "session-1",
                    "parentThreadId": "parent-thread-1" if is_child else None,
                    "status": {"type": self.last_status if is_child else "active"},
                    "turns": [],
                    "updatedAt": 1,
                }
            }
        if method == "turn/interrupt":
            return {}
        if method == "turn/steer":
            return {"turnId": params["expectedTurnId"]}
        if method == "initialize":
            return {}
        raise AssertionError(f"unexpected method: {method}")

    def next_notification(self, timeout_ms: int) -> dict[str, Any] | None:
        if self.notifications:
            at_ms, notification = self.notifications[0]
            current_ms = int(round((self.clock.now - 100.0) * 1000))
            if at_ms <= current_ms + timeout_ms:
                self.clock.advance_ms(max(0, at_ms - current_ms))
                self.notifications.popleft()
                self._safe_transcript.append(
                    {
                        "method": notification["method"],
                        "fieldNames": sorted(notification["params"]),
                        "status": "notification",
                    }
                )
                return notification
        self.clock.advance_ms(timeout_ms)
        return None

    def close(self) -> None:
        self.closed = True


class RealTimeActiveSession(ScriptedSession):
    def __init__(self) -> None:
        super().__init__(FakeClock())
        self.health_reads = 0
        self.health_event = threading.Event()

    def request(
        self, method: str, params: Mapping[str, Any], *, timeout_ms: int
    ) -> Any:
        if method == "thread/read":
            self.health_reads += 1
            if self.health_reads >= 3:
                self.health_event.set()
        return super().request(method, params, timeout_ms=timeout_ms)

    def next_notification(self, timeout_ms: int) -> dict[str, Any] | None:
        time.sleep(timeout_ms / 1000)
        return None
