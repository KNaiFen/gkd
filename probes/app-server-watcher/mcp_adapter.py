#!/usr/bin/env python3
"""Fixed MCP adapter used only by the GKD-M-1C live canary."""

from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from gkd_watchdog.jsonrpc import JsonRpcClient, SubprocessTransport
from gkd_watchdog.model import canonical_json
from gkd_watchdog.runtime import (
    AppServerFactory,
    DefaultCommandResolver,
    SubprocessRuntimeVerifier,
)
from gkd_watchdog.watcher import WatchService
from live_support import LIVE_SCENARIOS, LiveBinding, LiveProbeError, atomic_write_json


PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "gkd-live-gate"
SERVER_VERSION = "1"
GATE_TOOL = "gkd_live_gate"
HOLD_TOOL = "gkd_canary_hold"
GATE_FIELDS = frozenset({"scenario"})
HOLD_FIELDS = frozenset({"mode"})
CALL_FIELDS = frozenset({"name", "arguments", "_meta"})
CHILD_STATE_FIELDS = frozenset(
    {"schemaVersion", "sessionId", "childThreadId", "childTurnId", "mode"}
)


def _required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value or "\0" in value or "\n" in value:
        raise LiveProbeError("adapter_environment_invalid")
    return Path(value)


def _required_value(name: str) -> str:
    value = os.environ.get(name)
    if not value or "\0" in value or "\n" in value:
        raise LiveProbeError("adapter_environment_invalid")
    return value


def _correlation(metadata: Any) -> dict[str, str]:
    if not isinstance(metadata, Mapping):
        raise LiveProbeError("mcp_correlation_missing")
    turn_metadata = metadata.get("x-codex-turn-metadata")
    if not isinstance(turn_metadata, Mapping):
        raise LiveProbeError("mcp_turn_correlation_missing")
    thread_id = metadata.get("threadId")
    nested_thread_id = turn_metadata.get("thread_id")
    session_id = turn_metadata.get("session_id")
    turn_id = turn_metadata.get("turn_id")
    if (
        not isinstance(thread_id, str)
        or thread_id != nested_thread_id
        or not isinstance(session_id, str)
        or not isinstance(turn_id, str)
    ):
        raise LiveProbeError("mcp_correlation_invalid")
    if turn_metadata.get("model") != "gpt-5.6-sol":
        raise LiveProbeError("mcp_model_mismatch")
    if turn_metadata.get("reasoning_effort") != "xhigh":
        raise LiveProbeError("mcp_reasoning_mismatch")
    return {"sessionId": session_id, "threadId": thread_id, "turnId": turn_id}


def _wait_child_state(path: Path, *, timeout_seconds: float = 20.0) -> Mapping[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.025)
            continue
        if not isinstance(value, Mapping) or set(value) != CHILD_STATE_FIELDS:
            raise LiveProbeError("child_state_schema_mismatch")
        if value.get("schemaVersion") != 1:
            raise LiveProbeError("child_state_version_mismatch")
        return value
    raise LiveProbeError("child_state_timeout")


def _append_pid(path: Path) -> None:
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
    finally:
        os.close(descriptor)


class RecordingTransport(SubprocessTransport):
    def __init__(self, argv: Sequence[str], *, pid_path: Path) -> None:
        super().__init__(argv)
        pid_path.write_text(f"{self._process.pid}\n", encoding="ascii")


class SafeTraceClient:
    """Record target roles and enums without retaining protocol bodies."""

    def __init__(
        self,
        client: JsonRpcClient,
        binding: LiveBinding,
        *,
        health_path: Path,
    ) -> None:
        self._client = client
        self._binding = binding
        self._health_path = health_path
        self._counts: Counter[str] = Counter()
        self._statuses: Counter[str] = Counter()
        self._control_sequence: list[dict[str, Any]] = []
        self._child_reads = 0
        self._parent_reads = 0
        self._read_matches: Counter[str] = Counter()
        self._include_turns_false = True
        self._terminal_seen = False

    @property
    def transcript(self):
        return self._client.transcript

    def transcript_digest(self) -> str:
        return self._client.transcript_digest()

    def _role(self, thread_id: Any) -> str:
        if thread_id == self._binding.child_thread_id:
            return "child"
        if thread_id == self._binding.parent_thread_id:
            return "parent"
        return "other"

    def request(self, method: str, params: Mapping[str, Any], *, timeout_ms: int):
        role = self._role(params.get("threadId"))
        self._counts[f"request:{method}:{role}"] += 1
        if method == "thread/read":
            if params.get("includeTurns") is not False:
                self._include_turns_false = False
                raise LiveProbeError("include_turns_not_false")
            if role == "child":
                self._child_reads += 1
                self._health_path.write_text(
                    f"{self._child_reads}\n", encoding="ascii"
                )
            elif role == "parent":
                self._parent_reads += 1
        if method in {"turn/interrupt", "turn/steer", "turn/start"}:
            entry = {
                "method": method,
                "targetRole": role,
                "targetThreadMatches": role
                == ("child" if method == "turn/interrupt" else "parent"),
            }
            if method == "turn/interrupt":
                entry["targetTurnMatches"] = (
                    params.get("turnId") == self._binding.child_turn_id
                )
            if method == "turn/steer":
                entry["expectedTurnMatches"] = (
                    params.get("expectedTurnId") == self._binding.parent_turn_id
                )
            self._control_sequence.append(entry)
        result = self._client.request(method, params, timeout_ms=timeout_ms)
        if method == "thread/read":
            self._record_read_validation(role, params.get("threadId"), result)
        return result

    def _record_read_validation(
        self, role: str, requested_thread_id: Any, result: Any
    ) -> None:
        thread = result.get("thread") if isinstance(result, Mapping) else None
        if not isinstance(thread, Mapping):
            return
        status = thread.get("status")
        status_type = status.get("type") if isinstance(status, Mapping) else None
        turns = thread.get("turns")
        expected_thread_id = (
            self._binding.child_thread_id
            if role == "child"
            else self._binding.parent_thread_id
        )
        checks = {
            "thread": requested_thread_id == expected_thread_id
            and thread.get("id") == expected_thread_id,
            "session": thread.get("sessionId") == self._binding.session_id,
            "turnsEmpty": isinstance(turns, list) and not turns,
            "active": status_type == "active",
        }
        if role == "child":
            checks["parent"] = (
                thread.get("parentThreadId") == self._binding.parent_thread_id
            )
        for name, matched in checks.items():
            if matched:
                self._read_matches[f"{role}:{name}"] += 1

    def next_notification(self, timeout_ms: int):
        notification = self._client.next_notification(timeout_ms)
        if notification is None:
            return None
        method = notification.get("method")
        params = notification.get("params")
        role = self._role(params.get("threadId")) if isinstance(params, Mapping) else "other"
        self._counts[f"notification:{method if isinstance(method, str) else 'invalid'}:{role}"] += 1
        status = None
        if isinstance(params, Mapping):
            raw_status = params.get("status")
            if isinstance(raw_status, Mapping):
                status = raw_status.get("type")
            turn = params.get("turn")
            if isinstance(turn, Mapping):
                status = turn.get("status", status)
        if isinstance(status, str):
            self._statuses[f"{method}:{role}:{status}"] += 1
        if method == "turn/completed" and role == "child":
            if self._terminal_seen:
                raise LiveProbeError("duplicate_terminal")
            self._terminal_seen = True
            turn = params.get("turn") if isinstance(params, Mapping) else None
            self._control_sequence.append(
                {
                    "method": "turn/completed",
                    "targetRole": "child",
                    "targetThreadMatches": params.get("threadId")
                    == self._binding.child_thread_id,
                    "targetTurnMatches": isinstance(turn, Mapping)
                    and turn.get("id") == self._binding.child_turn_id,
                    "status": status,
                }
            )
        return notification

    def close(self) -> None:
        self._client.close()

    def safe_trace(self) -> dict[str, Any]:
        child_reads = self._child_reads
        parent_reads = self._parent_reads
        return {
            "methodCounts": dict(sorted(self._counts.items())),
            "statusCounts": dict(sorted(self._statuses.items())),
            "controlSequence": list(self._control_sequence),
            "readValidation": {
                "childReadCount": child_reads,
                "parentReadCount": parent_reads,
                "includeTurnsFalse": self._include_turns_false,
                "childThreadAllMatch": child_reads > 0
                and self._read_matches["child:thread"] == child_reads,
                "childSessionAllMatch": child_reads > 0
                and self._read_matches["child:session"] == child_reads,
                "childParentAllMatch": child_reads > 0
                and self._read_matches["child:parent"] == child_reads,
                "childTurnsEmpty": child_reads > 0
                and self._read_matches["child:turnsEmpty"] == child_reads,
                "childActiveObserved": self._read_matches["child:active"] > 0,
                "parentThreadAllMatch": parent_reads > 0
                and self._read_matches["parent:thread"] == parent_reads,
                "parentSessionAllMatch": parent_reads > 0
                and self._read_matches["parent:session"] == parent_reads,
                "parentTurnsEmpty": parent_reads > 0
                and self._read_matches["parent:turnsEmpty"] == parent_reads,
                "parentActiveObserved": self._read_matches["parent:active"] > 0,
            },
            "rawPayloadStored": False,
        }


class CapturingFactory:
    def __init__(self, binding: LiveBinding, inner_pid: Path, health_path: Path) -> None:
        self.binding = binding
        self.inner_pid = inner_pid
        self.health_path = health_path
        self.client: SafeTraceClient | None = None

    def __call__(self, request, cancellation):
        factory = AppServerFactory(
            DefaultCommandResolver(),
            SubprocessRuntimeVerifier(),
            transport_factory=lambda argv: RecordingTransport(
                argv, pid_path=self.inner_pid
            ),
        )
        raw_client = factory(request, cancellation)
        self.client = SafeTraceClient(
            raw_client,
            self.binding,
            health_path=self.health_path,
        )
        return self.client


class Adapter:
    def __init__(self) -> None:
        self.state_path = _required_path("GKD_LIVE_STATE_PATH")
        self.child_state_path = _required_path("GKD_LIVE_CHILD_STATE_PATH")
        self.inner_pid_path = _required_path("GKD_LIVE_INNER_PID_PATH")
        self.health_path = _required_path("GKD_LIVE_HEALTH_PATH")
        self.trace_path = _required_path("GKD_LIVE_WATCH_TRACE_PATH")
        self.result_path = _required_path("GKD_LIVE_WATCH_RESULT_PATH")
        self.hold_ready_path = _required_path("GKD_LIVE_HOLD_READY_PATH")
        self.task_id = _required_value("GKD_LIVE_TASK_ID")
        self.offer_id = _required_value("GKD_LIVE_OFFER_ID")
        self.wrong_parent_turn_id = _required_value("GKD_LIVE_WRONG_PARENT_TURN_ID")
        _append_pid(_required_path("GKD_LIVE_ADAPTER_PIDS_PATH"))
        self._write_lock = threading.Lock()

    def write(self, value: Mapping[str, Any]) -> None:
        payload = canonical_json(value)
        with self._write_lock:
            sys.stdout.write(payload + "\n")
            sys.stdout.flush()

    def serve(self) -> int:
        for line in sys.stdin:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._error(None, -32700, "invalid JSON-RPC message")
                continue
            self._handle(message)
        return 0

    def _handle(self, message: Any) -> None:
        if not isinstance(message, Mapping) or message.get("jsonrpc") != "2.0":
            self._error(None, -32600, "invalid JSON-RPC request")
            return
        method = message.get("method")
        if "id" not in message:
            return
        request_id = message.get("id")
        params = message.get("params", {})
        if method == "initialize":
            self._result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        elif method == "tools/list":
            self._list_tools(request_id)
        elif method == "tools/call":
            self._call(request_id, params)
        else:
            self._error(request_id, -32601, "method not found")

    def _list_tools(self, request_id: Any) -> None:
        self._result(
            request_id,
            {
                "tools": [
                    {
                        "name": GATE_TOOL,
                        "description": "Run one fixed GKD live watcher scenario.",
                        "inputSchema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["scenario"],
                            "properties": {
                                "scenario": {"type": "string", "enum": list(LIVE_SCENARIOS)}
                            },
                        },
                    },
                    {
                        "name": HOLD_TOOL,
                        "description": "Run the fixed controlled child hold fixture.",
                        "inputSchema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["mode"],
                            "properties": {
                                "mode": {
                                    "type": "string",
                                    "enum": ["complete", "transport_failure"],
                                }
                            },
                        },
                    },
                ]
            },
        )

    def _call(self, request_id: Any, params: Any) -> None:
        if not isinstance(params, Mapping) or set(params) != CALL_FIELDS:
            self._error(request_id, -32602, "invalid tool call")
            return
        name = params.get("name")
        arguments = params.get("arguments")
        if name == GATE_TOOL:
            self._run_gate(request_id, arguments, params.get("_meta"))
        elif name == HOLD_TOOL:
            self._run_hold(request_id, arguments, params.get("_meta"))
        else:
            self._error(request_id, -32602, "unknown tool")

    def _run_gate(self, request_id: Any, arguments: Any, metadata: Any) -> None:
        if (
            not isinstance(arguments, Mapping)
            or set(arguments) != GATE_FIELDS
            or arguments.get("scenario") not in LIVE_SCENARIOS
        ):
            self._error(request_id, -32602, "invalid live scenario")
            return
        try:
            parent = _correlation(metadata)
            child = _wait_child_state(self.child_state_path)
            if child.get("sessionId") != parent["sessionId"]:
                raise LiveProbeError("child_session_mismatch")
            if child.get("childThreadId") == parent["threadId"]:
                raise LiveProbeError("child_parent_alias")
            state = {
                "schemaVersion": 1,
                "scenario": arguments["scenario"],
                "taskId": self.task_id,
                "offerId": self.offer_id,
                "sessionId": parent["sessionId"],
                "parentThreadId": parent["threadId"],
                "parentTurnId": parent["turnId"],
                "childThreadId": child.get("childThreadId"),
                "childTurnId": child.get("childTurnId"),
                "wrongParentTurnId": self.wrong_parent_turn_id,
                "maxWaitMs": 43_200_000,
                "healthIntervalMs": 200,
            }
            atomic_write_json(self.state_path, state)
            binding = LiveBinding.parse(state)
            factory = CapturingFactory(
                binding,
                self.inner_pid_path,
                self.health_path,
            )
            result = WatchService(
                factory,
                cancel_poll_ms=50,
                interrupt_confirm_timeout_ms=5_000,
            ).watch(binding.watch_request())
            safe_result = {
                "outcome": result.outcome,
                "reason": result.reason,
                "healthChecks": result.health_checks,
                "elapsedMs": result.elapsed_ms,
            }
            trace = factory.client.safe_trace() if factory.client is not None else {
                "methodCounts": {},
                "statusCounts": {},
                "controlSequence": [],
                "readValidation": {
                    "childReadCount": 0,
                    "parentReadCount": 0,
                    "includeTurnsFalse": False,
                },
                "rawPayloadStored": False,
            }
            atomic_write_json(self.trace_path, trace)
            atomic_write_json(self.result_path, safe_result)
            self._result(
                request_id,
                {
                    "content": [{"type": "text", "text": canonical_json(safe_result)}],
                    "structuredContent": safe_result,
                    "isError": result.outcome in {
                        "orchestrator_error",
                        "parent_steer_rejected",
                        "protocol_error",
                    },
                },
            )
        except (LiveProbeError, OSError, RuntimeError, ValueError):
            self._error(request_id, -32603, "live gate failed closed")

    def _run_hold(self, request_id: Any, arguments: Any, metadata: Any) -> None:
        if (
            not isinstance(arguments, Mapping)
            or set(arguments) != HOLD_FIELDS
            or arguments.get("mode") not in {"complete", "transport_failure"}
        ):
            self._error(request_id, -32602, "invalid hold mode")
            return
        try:
            child = _correlation(metadata)
        except LiveProbeError:
            self._error(request_id, -32603, "child correlation failed closed")
            return
        atomic_write_json(
            self.child_state_path,
            {
                "schemaVersion": 1,
                "sessionId": child["sessionId"],
                "childThreadId": child["threadId"],
                "childTurnId": child["turnId"],
                "mode": arguments["mode"],
            },
        )
        self.hold_ready_path.write_text("ready\n", encoding="ascii")
        if arguments["mode"] == "transport_failure":
            time.sleep(2.0)
            os._exit(72)
        scenario = os.environ.get("GKD_LIVE_SCENARIO")
        duration = 15.0 if scenario in {"cas_reject", "orchestrator_failure"} else 2.0
        time.sleep(duration)
        result = {"completed": True, "mode": "complete"}
        self._result(
            request_id,
            {
                "content": [{"type": "text", "text": canonical_json(result)}],
                "structuredContent": result,
                "isError": False,
            },
        )

    def _result(self, request_id: Any, result: Any) -> None:
        self.write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _error(self, request_id: Any, code: int, message: str) -> None:
        self.write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )


def main() -> int:
    try:
        return Adapter().serve()
    except (LiveProbeError, OSError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
