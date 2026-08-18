"""Bounded JSON-RPC client and subprocess transport for Codex app-server."""

from __future__ import annotations

from collections import deque
import hashlib
import json
import math
import os
import select
import subprocess
import threading
import time
from typing import Any, Callable, Mapping, Protocol, Sequence

from .constants import MAX_MESSAGE_BYTES, MAX_RPC_ID, RPC_TIMEOUT_MS
from .model import canonical_json


KNOWN_REMOTE_CLASSES = frozenset(
    {
        "notFound",
        "systemError",
        "errored",
        "interrupted",
        "expectedTurnMismatch",
        "invalidParams",
    }
)
KNOWN_STATUSES = frozenset(
    {
        "active",
        "idle",
        "notLoaded",
        "systemError",
        "completed",
        "failed",
        "inProgress",
        "interrupted",
        "errored",
        "notFound",
    }
)
TRANSCRIPT_METHODS = frozenset(
    {
        "initialize",
        "thread/read",
        "thread/status/changed",
        "turn/completed",
        "turn/interrupt",
        "turn/steer",
    }
)
TRANSCRIPT_FIELDS = frozenset(
    {
        "capabilities",
        "clientInfo",
        "expectedTurnId",
        "includeTurns",
        "input",
        "parentThreadId",
        "sessionId",
        "status",
        "threadId",
        "turn",
        "turnId",
    }
)


class AppServerError(RuntimeError):
    reason = "app_server_protocol_error"


class AppServerEOF(AppServerError):
    reason = "app_server_eof"


class AppServerMalformedJSON(AppServerError):
    reason = "app_server_malformed_json"


class AppServerMessageTooLarge(AppServerError):
    reason = "app_server_message_too_large"


class AppServerUnknownResponse(AppServerError):
    reason = "app_server_unknown_response"


class AppServerDuplicateResponse(AppServerError):
    reason = "app_server_duplicate_response"


class AppServerResponseTimeout(AppServerError):
    reason = "app_server_response_timeout"


class AppServerRemoteError(AppServerError):
    reason = "app_server_remote_error"

    def __init__(self, classification: str) -> None:
        super().__init__(classification)
        self.classification = classification


class AppServerStartError(AppServerError):
    reason = "app_server_start_failed"


class MessageTransport(Protocol):
    def write_message(self, message: Mapping[str, Any]) -> None: ...

    def read_message(self, timeout_ms: int) -> dict[str, Any] | None: ...

    def close(self) -> None: ...


class SubprocessTransport:
    """Newline JSON transport with one writer and deterministic shutdown."""

    def __init__(
        self,
        argv: Sequence[str],
        *,
        popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not argv or any(not isinstance(part, str) or not part for part in argv):
            raise AppServerStartError()
        self._clock = clock
        self._buffer = bytearray()
        self._writer_lock = threading.Lock()
        self._closed = False
        try:
            self._process = popen(
                tuple(argv),
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
        except (OSError, ValueError) as exc:
            raise AppServerStartError() from exc
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise AppServerStartError()

    def write_message(self, message: Mapping[str, Any]) -> None:
        payload = (canonical_json(message) + "\n").encode("utf-8")
        if len(payload) > MAX_MESSAGE_BYTES:
            raise AppServerMessageTooLarge()
        with self._writer_lock:
            if self._closed or self._process.stdin is None:
                raise AppServerEOF()
            try:
                self._process.stdin.write(payload)
                self._process.stdin.flush()
            except (BrokenPipeError, OSError, ValueError) as exc:
                raise AppServerEOF() from exc

    def read_message(self, timeout_ms: int) -> dict[str, Any] | None:
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be non-negative")
        deadline = self._clock() + timeout_ms / 1000
        while True:
            line = self._pop_line()
            if line is not None:
                return self._decode(line)
            remaining = deadline - self._clock()
            if remaining <= 0:
                return None
            if self._closed or self._process.stdout is None:
                raise AppServerEOF()
            ready, _, _ = select.select(
                [self._process.stdout.fileno()], [], [], remaining
            )
            if not ready:
                return None
            try:
                chunk = os.read(self._process.stdout.fileno(), 4096)
            except OSError as exc:
                raise AppServerEOF() from exc
            if not chunk:
                if self._buffer:
                    raise AppServerMalformedJSON()
                raise AppServerEOF()
            self._buffer.extend(chunk)
            if len(self._buffer) > MAX_MESSAGE_BYTES:
                raise AppServerMessageTooLarge()

    def _pop_line(self) -> bytes | None:
        try:
            end = self._buffer.index(10)
        except ValueError:
            return None
        line = bytes(self._buffer[:end])
        del self._buffer[: end + 1]
        if len(line) > MAX_MESSAGE_BYTES:
            raise AppServerMessageTooLarge()
        return line

    @staticmethod
    def _decode(line: bytes) -> dict[str, Any]:
        try:
            value = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AppServerMalformedJSON() from exc
        if not isinstance(value, dict):
            raise AppServerMalformedJSON()
        return value

    def close(self) -> None:
        with self._writer_lock:
            if getattr(self, "_closed", True):
                return
            self._closed = True
            process = getattr(self, "_process", None)
            if process is not None and process.stdin is not None:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass
        if process is None:
            return
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        if process.stdout is not None:
            try:
                process.stdout.close()
            except (OSError, ValueError):
                pass


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_strings(nested)


def classify_remote_error(error: Any) -> str:
    for value in _walk_strings(error):
        if value in KNOWN_REMOTE_CLASSES:
            return value
    return "remoteError"


def _safe_status(params: Any) -> str | None:
    if not isinstance(params, Mapping):
        return None
    candidates = [params.get("status")]
    turn = params.get("turn")
    if isinstance(turn, Mapping):
        candidates.append(turn.get("status"))
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            candidate = candidate.get("type")
        if isinstance(candidate, str) and candidate in KNOWN_STATUSES:
            return candidate
    return None


def _safe_fields(params: Mapping[str, Any]) -> list[str]:
    return sorted(field for field in params if field in TRANSCRIPT_FIELDS)


class JsonRpcClient:
    def __init__(
        self,
        transport: MessageTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_queued_notifications: int = 1_024,
    ) -> None:
        if max_queued_notifications <= 0:
            raise ValueError("max_queued_notifications must be positive")
        self._transport = transport
        self._clock = clock
        self._max_queued_notifications = max_queued_notifications
        self._next_id = 1
        self._pending: set[int] = set()
        self._completed: set[int] = set()
        self._notifications: deque[dict[str, Any]] = deque()
        self._transcript: list[dict[str, Any]] = []
        self._request_lock = threading.Lock()

    @property
    def transcript(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(entry) for entry in self._transcript)

    def transcript_digest(self) -> str:
        return hashlib.sha256(canonical_json(self._transcript).encode("utf-8")).hexdigest()

    def request(
        self,
        method: str,
        params: Mapping[str, Any],
        *,
        timeout_ms: int = RPC_TIMEOUT_MS,
    ) -> Any:
        with self._request_lock:
            request_id = self._allocate_id()
            self._pending.add(request_id)
            self._record(
                direction="request",
                method=method,
                request_id=request_id,
                params=params,
            )
            self._transport.write_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": dict(params),
                }
            )
            deadline = self._clock() + timeout_ms / 1000
            while True:
                remaining = deadline - self._clock()
                remaining_ms = max(0, math.ceil(remaining * 1000))
                message = self._transport.read_message(remaining_ms)
                if message is None:
                    self._pending.discard(request_id)
                    raise AppServerResponseTimeout()
                response = self._accept(message)
                if response is None:
                    continue
                response_id, result, error = response
                if response_id != request_id:
                    raise AppServerUnknownResponse()
                if error is not None:
                    raise AppServerRemoteError(classify_remote_error(error))
                return result

    def next_notification(self, timeout_ms: int) -> dict[str, Any] | None:
        if self._notifications:
            return self._notifications.popleft()
        message = self._transport.read_message(timeout_ms)
        if message is None:
            return None
        response = self._accept(message)
        if response is not None:
            raise AppServerUnknownResponse()
        return self._notifications.popleft() if self._notifications else None

    def close(self) -> None:
        self._transport.close()

    def _allocate_id(self) -> int:
        if self._next_id > MAX_RPC_ID:
            raise AppServerError()
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def _accept(self, message: Mapping[str, Any]) -> tuple[int, Any, Any] | None:
        if "jsonrpc" in message and message["jsonrpc"] != "2.0":
            raise AppServerMalformedJSON()
        if "id" in message:
            response_id = message["id"]
            if isinstance(response_id, bool) or not isinstance(response_id, int):
                raise AppServerUnknownResponse()
            if response_id in self._completed:
                raise AppServerDuplicateResponse()
            if response_id not in self._pending:
                raise AppServerUnknownResponse()
            if ("result" in message) == ("error" in message):
                raise AppServerMalformedJSON()
            self._pending.remove(response_id)
            self._completed.add(response_id)
            self._transcript.append(
                {
                    "direction": "response",
                    "id": response_id,
                    "status": "error" if "error" in message else "ok",
                }
            )
            return response_id, message.get("result"), message.get("error")

        method = message.get("method")
        params = message.get("params", {})
        if not isinstance(method, str) or not isinstance(params, Mapping):
            raise AppServerMalformedJSON()
        entry: dict[str, Any] = {
            "direction": "notification",
            "method": method if method in TRANSCRIPT_METHODS else "other_notification",
            "fieldNames": _safe_fields(params),
        }
        status = _safe_status(params)
        if status is not None:
            entry["status"] = status
        self._transcript.append(entry)
        if len(self._notifications) >= self._max_queued_notifications:
            raise AppServerError()
        self._notifications.append({"method": method, "params": dict(params)})
        return None

    def _record(
        self,
        *,
        direction: str,
        method: str,
        request_id: int,
        params: Mapping[str, Any],
    ) -> None:
        self._transcript.append(
            {
                "direction": direction,
                "id": request_id,
                "method": method,
                "fieldNames": _safe_fields(params),
            }
        )
