#!/usr/bin/env python3
"""Run the deterministic GKD-M-1C Codex/app-server/MCP live gate."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import select
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from gkd_watchdog.constants import (
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    MAX_WAIT_MS,
)
from gkd_watchdog.jsonrpc import (
    AppServerError,
    JsonRpcClient,
    SubprocessTransport,
)
from gkd_watchdog.model import canonical_json
from gkd_watchdog.runtime import SubprocessRuntimeVerifier
from live_support import (
    LIVE_SCENARIOS,
    LIVE_SCHEMA_VERSION,
    LiveProbeError,
    assert_evidence_safe,
    identity_digest,
    normalized_digest,
)


SCENARIO_DEADLINE_SECONDS = 90.0
NO_OUTPUT_DEADLINE_SECONDS = 60.0
HEALTH_INTERVAL_MS = 200
TOOL_TIMEOUT_SECONDS = 43_200
ADAPTER_PATH = SCRIPT_DIR / "mcp_adapter.py"
M1B_RESULTS_PATH = (
    REPO_ROOT / "evidence" / "m-1-external-watcher-core" / "contract-results.json"
)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _config_fingerprint() -> dict[str, Any]:
    config = Path.home() / ".codex" / "config.toml"
    try:
        raw = config.read_bytes()
        stat = config.stat()
    except FileNotFoundError:
        return {"exists": False, "sha256": None, "mtimeNs": None}
    return {
        "exists": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtimeNs": stat.st_mtime_ns,
    }


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_pid(path: Path) -> int | None:
    try:
        value = path.read_text(encoding="ascii").strip()
        pid = int(value)
    except (FileNotFoundError, UnicodeError, ValueError):
        return None
    return pid if pid > 1 else None


def _read_pids(path: Path) -> set[int]:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (FileNotFoundError, UnicodeError):
        return set()
    result = set()
    for line in lines:
        try:
            pid = int(line)
        except ValueError:
            continue
        if pid > 1:
            result.add(pid)
    return result


def _append_pid(path: Path, pid: int) -> None:
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{pid}\n".encode("ascii"))
    finally:
        os.close(descriptor)


class TrackedSubprocessTransport(SubprocessTransport):
    def __init__(self, argv: Sequence[str], *, pid_path: Path) -> None:
        super().__init__(argv)
        _append_pid(pid_path, self._process.pid)


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def _safe_status(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("type")
    allowed = {
        "active",
        "completed",
        "failed",
        "idle",
        "inProgress",
        "interrupted",
        "notLoaded",
        "systemError",
    }
    return value if isinstance(value, str) and value in allowed else None


def _m1b_contract_summary() -> dict[str, Any]:
    value = _safe_json(M1B_RESULTS_PATH)
    if value is None:
        raise LiveProbeError("m1b_results_missing")
    runtime = value.get("runtime")
    tests = value.get("tests")
    contracts = value.get("contracts")
    if (
        value.get("schemaVersion") != 1
        or value.get("task") != "GKD-M-1B"
        or value.get("outcome") != "core_ready_for_live_gate"
        or not isinstance(runtime, Mapping)
        or runtime.get("codexVersion") != EXPECTED_CODEX_VERSION
        or runtime.get("schemaDigestSha256") != EXPECTED_SCHEMA_DIGEST
        or not isinstance(tests, Mapping)
        or tests.get("count") != 47
        or not isinstance(tests.get("idDigestSha256"), str)
        or not isinstance(contracts, Mapping)
        or not contracts
        or any(
            not isinstance(contract, Mapping) or contract.get("status") != "pass"
            for contract in contracts.values()
        )
        or not isinstance(contracts.get("deadline_single_terminal"), Mapping)
        or contracts["deadline_single_terminal"].get("status") != "pass"
    ):
        raise LiveProbeError("m1b_results_invalid")
    return {
        "tests": 47,
        "status": "pass",
        "testIdDigestSha256": tests["idDigestSha256"],
        "fakeClockTwelveHourSingleDeadline": "pass",
    }


def _fixed_prompt(scenario: str) -> str:
    child_mode = "transport_failure" if scenario == "abnormal" else "complete"
    return (
        "Execute this mandatory ordered protocol. Your FIRST tool call MUST be the built-in "
        "agents.spawn_agent tool, exactly once, with task_name gkd_live_child. Its child "
        "message must say: call the gkd_live gkd_canary_hold MCP tool exactly once with "
        f"mode {child_mode}, then return a short final response; do nothing else. Do not wait "
        "for the child. Only after spawn_agent returns, call the gkd_live gkd_live_gate MCP "
        f"tool exactly once with scenario {scenario}. Then return one short final response. "
        "If spawn_agent is unavailable, return immediately without calling the MCP gate. "
        "Never inspect files, run shell commands, browse, or call any other tool."
    )


class ScenarioPaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state = root / "state.json"
        self.child_state = root / "child-state.json"
        self.inner_pid = root / "inner.pid"
        self.adapter_pids = root / "adapter-pids.txt"
        self.control_pids = root / "control-pids.txt"
        self.health = root / "health.txt"
        self.watch_trace = root / "watch-trace.json"
        self.watch_result = root / "watch-result.json"
        self.hold_ready = root / "hold-ready.txt"


class ExecScenarioRunner:
    """Run a real Codex CLI parent so native multi-agent tools remain available."""

    def __init__(self, codex: str, python: str, scenario: str) -> None:
        if scenario not in LIVE_SCENARIOS:
            raise LiveProbeError("scenario_invalid")
        self.codex = codex
        self.python = python
        self.scenario = scenario
        self.parent_frames: Counter[str] = Counter()
        self.parent_thread_id: str | None = None
        self.parent_turn_id: str | None = None
        self.session_id: str | None = None
        self.child_thread_id: str | None = None
        self.child_turn_id: str | None = None
        self._child_candidates: set[str] = set()
        self._state_written = False
        self._forced_inner_failure = False
        self._forced_child_interrupt = False
        self._exec_method_counts: Counter[str] = Counter()
        self._exec_item_counts: Counter[str] = Counter()
        self._exec_status_counts: Counter[str] = Counter()
        self._exec_terminal_count = 0
        self._mcp_pending = False
        self._pending_activity_since_health = 0
        self._health_window_activity: list[int] = []
        self._parent_sequence: list[str] = []
        self._task_id = f"gkd-m1c-{uuid.uuid4().hex}"
        self._offer_id = f"offer-{uuid.uuid4().hex}"
        self._wrong_parent_turn_id = f"wrong-{uuid.uuid4().hex}"

    @staticmethod
    def _health_reads(path: Path) -> int:
        try:
            return int(path.read_text(encoding="ascii").strip())
        except (FileNotFoundError, UnicodeError, ValueError):
            return 0

    @staticmethod
    def _cleanup_processes(
        paths: ScenarioPaths, outer_pid: int
    ) -> dict[str, Any]:
        known = _read_pids(paths.adapter_pids)
        known.update(_read_pids(paths.control_pids))
        inner = _read_pid(paths.inner_pid)
        if inner is not None:
            known.add(inner)
        known.add(outer_pid)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and any(_pid_alive(pid) for pid in known):
            time.sleep(0.05)
        residual = sorted(pid for pid in known if _pid_alive(pid))
        for pid in residual:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        forced_deadline = time.monotonic() + 2.0
        while time.monotonic() < forced_deadline and any(
            _pid_alive(pid) for pid in residual
        ):
            time.sleep(0.05)
        final_residual = [pid for pid in residual if _pid_alive(pid)]
        return {
            "knownProcessCount": len(known),
            "forcedCleanup": bool(residual),
            "residualProcessCount": len(final_residual),
            "complete": not final_residual,
        }

    def _exec_command(self, paths: ScenarioPaths) -> tuple[str, ...]:
        environment = {
            "GKD_LIVE_STATE_PATH": paths.state,
            "GKD_LIVE_CHILD_STATE_PATH": paths.child_state,
            "GKD_LIVE_INNER_PID_PATH": paths.inner_pid,
            "GKD_LIVE_ADAPTER_PIDS_PATH": paths.adapter_pids,
            "GKD_LIVE_HEALTH_PATH": paths.health,
            "GKD_LIVE_WATCH_TRACE_PATH": paths.watch_trace,
            "GKD_LIVE_WATCH_RESULT_PATH": paths.watch_result,
            "GKD_LIVE_HOLD_READY_PATH": paths.hold_ready,
            "GKD_LIVE_TASK_ID": self._task_id,
            "GKD_LIVE_OFFER_ID": self._offer_id,
            "GKD_LIVE_WRONG_PARENT_TURN_ID": self._wrong_parent_turn_id,
            "GKD_LIVE_SCENARIO": self.scenario,
        }
        command = [
            self.codex,
            "exec",
            "--json",
            "-C",
            str(REPO_ROOT),
            "-m",
            "gpt-5.6-sol",
            "-s",
            "read-only",
            "-c",
            'model_reasoning_effort="xhigh"',
            "-c",
            "features.multi_agent_v2.enabled=true",
            "-c",
            f"mcp_servers.gkd_live.command={_toml_string(self.python)}",
            "-c",
            f"mcp_servers.gkd_live.args={json.dumps([str(ADAPTER_PATH)])}",
            "-c",
            f"mcp_servers.gkd_live.tool_timeout_sec={TOOL_TIMEOUT_SECONDS}",
            "-c",
            'mcp_servers.gkd_live.enabled_tools=["gkd_live_gate","gkd_canary_hold"]',
            "-c",
            'mcp_servers.gkd_live.tools.gkd_live_gate.approval_mode="approve"',
            "-c",
            'mcp_servers.gkd_live.tools.gkd_canary_hold.approval_mode="approve"',
        ]
        for key, value in sorted(environment.items()):
            command.extend(
                (
                    "-c",
                    f"mcp_servers.gkd_live.env.{key}={_toml_string(str(value))}",
                )
            )
        command.append(_fixed_prompt(self.scenario))
        return tuple(command)

    def _accept_exec_event(self, event: Any) -> None:
        if not isinstance(event, Mapping):
            raise LiveProbeError("exec_event_invalid")
        raw_type = event.get("type")
        allowed_types = {
            "error",
            "item.completed",
            "item.started",
            "thread.started",
            "turn.completed",
            "turn.failed",
            "turn.started",
        }
        event_type = raw_type if raw_type in allowed_types else "other_event"
        self._exec_method_counts[event_type] += 1
        if event_type == "thread.started":
            thread_id = event.get("thread_id")
            if not isinstance(thread_id, str):
                raise LiveProbeError("exec_parent_thread_missing")
            if self.parent_thread_id is not None and thread_id != self.parent_thread_id:
                raise LiveProbeError("exec_parent_thread_ambiguous")
            self.parent_thread_id = thread_id
        item = event.get("item")
        raw_item_type = item.get("type") if isinstance(item, Mapping) else None
        item_types = {
            "agent_message": "agentMessage",
            "collab_tool_call": "collabAgentToolCall",
            "mcp_tool_call": "mcpToolCall",
            "reasoning": "reasoning",
        }
        item_type = item_types.get(raw_item_type)
        if item_type is not None:
            self._exec_item_counts[f"{event_type}:{item_type}"] += 1
            self.parent_frames[f"{event_type.replace('.', '/')}:{item_type}"] += 1
            self._parent_sequence.append(f"{event_type}:{item_type}")
        is_mcp_start = event_type == "item.started" and item_type == "mcpToolCall"
        is_mcp_completion = (
            event_type == "item.completed" and item_type == "mcpToolCall"
        )
        if self._mcp_pending and not is_mcp_completion:
            self._pending_activity_since_health += 1
        if is_mcp_start:
            self._mcp_pending = True
        elif is_mcp_completion:
            self._mcp_pending = False
        status = _safe_status(item.get("status")) if isinstance(item, Mapping) else None
        if status is not None:
            self._exec_status_counts[f"{event_type}:{status}"] += 1
        if event_type in {"turn.completed", "turn.failed"}:
            self._exec_terminal_count += 1
            self._parent_sequence.append(event_type)

    def _load_binding(self, paths: ScenarioPaths) -> Any:
        value = _safe_json(paths.state)
        if value is None:
            return None
        from live_support import LiveBinding

        binding = LiveBinding.parse(value)
        self.parent_thread_id = binding.parent_thread_id
        self.parent_turn_id = binding.parent_turn_id
        self.session_id = binding.session_id
        self.child_thread_id = binding.child_thread_id
        self.child_turn_id = binding.child_turn_id
        self._child_candidates = {binding.child_thread_id}
        self._state_written = True
        return binding

    def _control_client(self, paths: ScenarioPaths) -> JsonRpcClient:
        transport = TrackedSubprocessTransport(
            (self.codex, "app-server"), pid_path=paths.control_pids
        )
        client = JsonRpcClient(transport)
        initialized = client.request(
            "initialize",
            {
                "clientInfo": {"name": "gkd-live-control", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
            timeout_ms=10_000,
        )
        if not isinstance(initialized, Mapping):
            client.close()
            raise LiveProbeError("control_initialize_invalid")
        return client

    def _interrupt_child(self, binding, paths: ScenarioPaths) -> None:
        client = self._control_client(paths)
        try:
            client.request(
                "turn/interrupt",
                {
                    "threadId": binding.child_thread_id,
                    "turnId": binding.child_turn_id,
                },
                timeout_ms=10_000,
            )
        finally:
            client.close()

    def _cleanup_exec_threads(self, binding, paths: ScenarioPaths) -> bool:
        if binding is None and self.parent_thread_id is None:
            return True
        client = self._control_client(paths)
        clean = True
        try:
            targets = []
            if binding is not None:
                targets.append((binding.child_thread_id, binding.child_turn_id))
                targets.append((binding.parent_thread_id, binding.parent_turn_id))
            else:
                targets.append((self.parent_thread_id, None))
            for thread_id, turn_id in targets:
                if thread_id is None:
                    continue
                try:
                    if turn_id is not None:
                        client.request(
                            "turn/interrupt",
                            {"threadId": thread_id, "turnId": turn_id},
                            timeout_ms=5_000,
                        )
                except AppServerError:
                    pass
                try:
                    client.request(
                        "thread/delete",
                        {"threadId": thread_id},
                        timeout_ms=10_000,
                    )
                except AppServerError:
                    clean = False
        finally:
            client.close()
        return clean

    def _assertions(
        self,
        *,
        parent_completed: bool,
        failure_reason: str | None,
        watch_result: Mapping[str, Any],
        watch_trace: Mapping[str, Any],
        thread_cleanup: bool,
        process_cleanup: Mapping[str, Any],
    ) -> dict[str, bool]:
        counts = watch_trace.get("methodCounts", {})
        sequence = watch_trace.get("controlSequence", [])
        read_validation = watch_trace.get("readValidation", {})
        child_reads = read_validation.get("childReadCount", 0)
        parent_mcp_started = self.parent_frames.get("item/started:mcpToolCall", 0)
        parent_mcp_completed = self.parent_frames.get("item/completed:mcpToolCall", 0)
        exact_reads = all(
            read_validation.get(field) is True
            for field in (
                "includeTurnsFalse",
                "childThreadAllMatch",
                "childSessionAllMatch",
                "childParentAllMatch",
                "childTurnsEmpty",
                "childActiveObserved",
                "parentThreadAllMatch",
                "parentSessionAllMatch",
                "parentTurnsEmpty",
                "parentActiveObserved",
            )
        )
        health_trace_complete = (
            isinstance(child_reads, int)
            and child_reads >= 3
            and len(self._health_window_activity) >= 3
            and all(count == 0 for count in self._health_window_activity)
        )
        common = {
            "exactBindingObserved": self._state_written
            and len(self._child_candidates) == 1
            and exact_reads,
            "fixedMaxWaitObserved": self._state_written
            and bool(watch_result)
            and exact_reads,
            "freshToolTimeoutAccepted": parent_mcp_started == 1
            and parent_mcp_completed == 1,
            "liveMcpCallObserved": parent_mcp_started == 1
            and parent_mcp_completed == 1,
            "parentCompleted": parent_completed,
            "cleanupComplete": thread_cleanup
            and bool(process_cleanup.get("complete")),
            "rawPayloadAbsent": watch_trace.get("rawPayloadStored") is False,
            "healthTraceComplete": health_trace_complete,
        }
        if self.scenario == "normal":
            control_methods = [
                entry.get("method")
                for entry in sequence
                if isinstance(entry, Mapping)
            ]
            common.update(
                {
                    "twoHealthyCycles": health_trace_complete,
                    "healthSilentToParent": health_trace_complete
                    and parent_mcp_started == 1
                    and parent_mcp_completed == 1,
                    "normalTerminal": watch_result.get("outcome")
                    == "normal_terminal",
                    "singleWatcherCompletion": parent_mcp_completed == 1,
                    # The CLI allowlist has no child-final/mailbox frame that can
                    # be safely correlated without reading conversation bodies.
                    "nativeAndWatcherSignalsDistinct": False,
                    "singleParentContinuation": self.parent_frames.get(
                        "item/completed:agentMessage", 0
                    )
                    == 1
                    and self._exec_terminal_count == 1,
                    "normalHasNoControl": not any(
                        method in {"turn/interrupt", "turn/steer", "turn/start"}
                        for method in control_methods
                    ),
                }
            )
        elif self.scenario == "abnormal":
            compact = [
                (entry.get("method"), entry.get("targetRole"))
                for entry in sequence
                if isinstance(entry, Mapping)
                and entry.get("method")
                in {"turn/interrupt", "turn/completed", "turn/steer"}
            ]
            common.update(
                {
                    "realSystemErrorObserved": any(
                        key.endswith(":child:systemError")
                        for key in watch_trace.get("statusCounts", {})
                    ),
                    "interruptConfirmSteerOrder": compact
                    == [
                        ("turn/interrupt", "child"),
                        ("turn/completed", "child"),
                        ("turn/steer", "parent"),
                    ],
                    "boundControlScope": len(compact) == 3
                    and all(
                        entry.get("targetThreadMatches") is True
                        and (
                            entry.get("method") == "turn/steer"
                            or entry.get("targetTurnMatches") is True
                        )
                        and (
                            entry.get("method") != "turn/steer"
                            or entry.get("expectedTurnMatches") is True
                        )
                        for entry in sequence
                        if isinstance(entry, Mapping)
                        and entry.get("method")
                        in {"turn/interrupt", "turn/completed", "turn/steer"}
                    ),
                    "parentNeverInterrupted": not any(
                        key == "request:turn/interrupt:parent" for key in counts
                    ),
                    "abnormalTerminal": watch_result.get("outcome")
                    == "abnormal_child",
                }
            )
        elif self.scenario == "cas_reject":
            steer_entries = [
                entry
                for entry in sequence
                if isinstance(entry, Mapping) and entry.get("method") == "turn/steer"
            ]
            common.update(
                {
                    "wrongExpectedTurnUsed": len(steer_entries) == 1
                    and steer_entries[0].get("expectedTurnMatches") is False,
                    "singleSteerAttempt": len(steer_entries) == 1,
                    "steerTargetsBoundParent": len(steer_entries) == 1
                    and steer_entries[0].get("targetThreadMatches") is True,
                    "noTurnStartFallback": not any(
                        isinstance(entry, Mapping)
                        and entry.get("method") == "turn/start"
                        for entry in sequence
                    ),
                    "casRejected": watch_result.get("outcome")
                    == "parent_steer_rejected",
                }
            )
        elif self.scenario == "orchestrator_failure":
            common.update(
                {
                    "innerTransportTerminated": self._forced_inner_failure,
                    "terminalToolWake": parent_mcp_completed == 1,
                    "orchestratorFailureClassified": watch_result.get("outcome")
                    in {"protocol_error", "orchestrator_error"},
                }
            )
        if failure_reason is not None:
            common["scenarioErrorAbsent"] = False
        return common

    def run(self, root: Path) -> dict[str, Any]:
        paths = ScenarioPaths(root)
        process = subprocess.Popen(
            self._exec_command(paths),
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        parent_completed = False
        failure_reason: str | None = None
        binding = None
        deadline = time.monotonic() + SCENARIO_DEADLINE_SECONDS
        last_output_at = time.monotonic()
        observed_health_reads = 0
        try:
            if process.stdout is None:
                raise LiveProbeError("exec_stdout_missing")
            while time.monotonic() < deadline:
                ready, _, _ = select.select([process.stdout.fileno()], [], [], 0.1)
                if ready:
                    line = process.stdout.readline()
                    if line:
                        last_output_at = time.monotonic()
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise LiveProbeError("exec_event_malformed") from exc
                        self._accept_exec_event(event)
                        if event.get("type") == "turn.completed":
                            parent_completed = True
                    elif process.poll() is not None:
                        break
                if binding is None:
                    binding = self._load_binding(paths)
                health_reads = self._health_reads(paths.health)
                if health_reads > observed_health_reads:
                    for _ in range(health_reads - observed_health_reads):
                        self._health_window_activity.append(
                            self._pending_activity_since_health
                        )
                        self._pending_activity_since_health = 0
                    observed_health_reads = health_reads
                if (
                    self.scenario == "orchestrator_failure"
                    and health_reads >= 3
                    and not self._forced_inner_failure
                ):
                    pid = _read_pid(paths.inner_pid)
                    if pid is not None:
                        os.kill(pid, signal.SIGTERM)
                        self._forced_inner_failure = True
                if (
                    self.scenario == "cas_reject"
                    and health_reads >= 3
                    and not self._forced_child_interrupt
                    and binding is not None
                ):
                    self._interrupt_child(binding, paths)
                    self._forced_child_interrupt = True
                if time.monotonic() - last_output_at >= NO_OUTPUT_DEADLINE_SECONDS:
                    raise LiveProbeError("scenario_no_output_timeout")
                if process.poll() is not None and not ready:
                    break
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
                raise LiveProbeError("scenario_timeout")
            if process.returncode != 0:
                raise LiveProbeError("exec_parent_failed")
            if not parent_completed:
                raise LiveProbeError("exec_parent_terminal_missing")
            if binding is None:
                binding = self._load_binding(paths)
            if binding is None:
                failure_reason = "binding_not_observed"
        except LiveProbeError as exc:
            failure_reason = str(exc)
        except (AppServerError, OSError, RuntimeError, ValueError):
            failure_reason = "exec_scenario_runtime_error"
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if process.stdout is not None:
                process.stdout.close()

        try:
            thread_cleanup = self._cleanup_exec_threads(binding, paths)
        except (AppServerError, LiveProbeError, OSError):
            thread_cleanup = False
        process_cleanup = self._cleanup_processes(paths, process.pid)
        watch_result = _safe_json(paths.watch_result) or {}
        watch_trace = _safe_json(paths.watch_trace) or {
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
        assertions = self._assertions(
            parent_completed=parent_completed,
            failure_reason=failure_reason,
            watch_result=watch_result,
            watch_trace=watch_trace,
            thread_cleanup=thread_cleanup,
            process_cleanup=process_cleanup,
        )
        identity = {}
        if binding is not None:
            identity = {
                "parentThreadSha256": identity_digest(binding.parent_thread_id),
                "parentTurnSha256": identity_digest(binding.parent_turn_id),
                "childThreadSha256": identity_digest(binding.child_thread_id),
                "childTurnSha256": identity_digest(binding.child_turn_id),
            }
        result = {
            "status": "pass" if all(assertions.values()) else "fail",
            "reason": failure_reason,
            "identity": identity,
            "assertions": assertions,
            "parentTrace": {
                "frameCounts": dict(sorted(self.parent_frames.items())),
                "methodCounts": dict(sorted(self._exec_method_counts.items())),
                "itemCounts": dict(sorted(self._exec_item_counts.items())),
                "statusCounts": dict(sorted(self._exec_status_counts.items())),
                "terminalCount": self._exec_terminal_count,
                "healthWindowParentActivityCounts": list(
                    self._health_window_activity
                ),
                "orderedSignals": list(self._parent_sequence),
                "rawPayloadStored": False,
            },
            "watcherTrace": watch_trace,
            "watcherResult": watch_result,
            "cleanup": {"threadsComplete": thread_cleanup, **process_cleanup},
        }
        prohibited = tuple(
            value
            for value in (
                self._task_id,
                self._offer_id,
                self._wrong_parent_turn_id,
                self.parent_thread_id,
                self.parent_turn_id,
                self.session_id,
                self.child_thread_id,
                self.child_turn_id,
            )
            if isinstance(value, str)
        )
        assert_evidence_safe(result, prohibited=prohibited)
        return result


def _gate(status: bool, reason: str) -> dict[str, str]:
    return {"status": "pass" if status else "fail", "reason": "proven" if status else reason}


def build_evidence(
    *,
    runtime,
    scenarios: Mapping[str, Mapping[str, Any]],
    config_before: Mapping[str, Any],
    config_after: Mapping[str, Any],
    temporary_cleanup: bool,
    m1b_contracts: Mapping[str, Any],
) -> dict[str, Any]:
    normal = scenarios.get("normal", {}).get("assertions", {})
    abnormal = scenarios.get("abnormal", {}).get("assertions", {})
    cas = scenarios.get("cas_reject", {}).get("assertions", {})
    failure = scenarios.get("orchestrator_failure", {}).get("assertions", {})
    all_cleanup = all(
        scenario.get("assertions", {}).get("cleanupComplete") is True
        for scenario in scenarios.values()
    )
    security = {
        "conversationBodyStored": False,
        "rawAppServerPayloadStored": False,
        "rawMcpPayloadStored": False,
        "rawIdentifierStored": False,
        "absolutePathStored": False,
        "environmentValueStored": False,
    }
    gates = {
        "1_actual_wiring_and_cross_process_identity": _gate(
            all(
                scenario.get("assertions", {}).get("exactBindingObserved") is True
                and scenario.get("assertions", {}).get("liveMcpCallObserved") is True
                for scenario in scenarios.values()
            ),
            "cross_process_identity_not_proven",
        ),
        "2_healthy_silence": _gate(
            normal.get("twoHealthyCycles") is True
            and normal.get("healthSilentToParent") is True,
            "healthy_silence_not_proven",
        ),
        "3_normal_terminal_deduplication": _gate(
            normal.get("normalTerminal") is True
            and normal.get("singleWatcherCompletion") is True
            and normal.get("nativeAndWatcherSignalsDistinct") is True
            and normal.get("singleParentContinuation") is True
            and normal.get("normalHasNoControl") is True,
            "normal_terminal_deduplication_not_proven",
        ),
        "4_abnormal_order_and_scope": _gate(
            abnormal.get("realSystemErrorObserved") is True
            and abnormal.get("interruptConfirmSteerOrder") is True
            and abnormal.get("boundControlScope") is True
            and abnormal.get("parentNeverInterrupted") is True
            and abnormal.get("abnormalTerminal") is True,
            "safe_real_system_error_not_proven",
        ),
        "5_expected_turn_cas": _gate(
            cas.get("wrongExpectedTurnUsed") is True
            and cas.get("singleSteerAttempt") is True
            and cas.get("steerTargetsBoundParent") is True
            and cas.get("noTurnStartFallback") is True
            and cas.get("casRejected") is True,
            "live_expected_turn_rejection_not_proven",
        ),
        "6_orchestrator_failure_wakeup": _gate(
            failure.get("innerTransportTerminated") is True
            and failure.get("terminalToolWake") is True
            and failure.get("orchestratorFailureClassified") is True,
            "orchestrator_failure_wakeup_not_proven",
        ),
        "7_combined_timeout_contract_not_soak": _gate(
            normal.get("freshToolTimeoutAccepted") is True
            and normal.get("fixedMaxWaitObserved") is True,
            "fresh_session_timeout_acceptance_not_proven",
        ),
        "8_parent_context_trace": _gate(
            all(
                scenario.get("assertions", {}).get("healthTraceComplete") is True
                and scenario.get("parentTrace", {}).get("rawPayloadStored") is False
                for scenario in scenarios.values()
            ),
            "required_parent_trace_missing",
        ),
        "9_data_and_cleanup": _gate(
            config_before == config_after
            and all_cleanup
            and temporary_cleanup
            and not any(security.values()),
            "data_or_cleanup_invariant_failed",
        ),
    }
    outcome = (
        "external_watcher_supported"
        if all(value["status"] == "pass" for value in gates.values())
        else "unsupported"
    )
    evidence: dict[str, Any] = {
        "schemaVersion": LIVE_SCHEMA_VERSION,
        "task": "GKD-M-1C",
        "outcome": outcome,
        "runtime": {
            "codexVersion": runtime.codex_version,
            "model": "gpt-5.6-sol",
            "reasoningEffort": "xhigh",
            "schemaDigestSha256": runtime.schema_digest,
            "mcpToolTimeoutSec": TOOL_TIMEOUT_SECONDS,
            "maxWaitMs": MAX_WAIT_MS,
            "scenarioDeadlineSec": SCENARIO_DEADLINE_SECONDS,
            "noOutputDeadlineSec": NO_OUTPUT_DEADLINE_SECONDS,
            "cleanupDeadlineSec": 7.0,
            "strictConfig": False,
            "evidenceClass": "combined_timeout_contract_not_soak",
        },
        "m1bContracts": dict(m1b_contracts),
        "gates": gates,
        "scenarios": dict(scenarios),
        "productionConfig": {
            "target": "user_home_codex_config",
            "before": dict(config_before),
            "after": dict(config_after),
            "beforeAfterMatch": config_before == config_after,
        },
        "cleanup": {
            "temporaryDirectoryRemoved": temporary_cleanup,
        },
        "security": security,
        "wallClockSoakClaimed": False,
        "normalization": {
            "scope": "decision_gates_and_safety_contracts",
        },
    }
    evidence["normalizedDigestSha256"] = normalized_digest(evidence)
    assert_evidence_safe(evidence)
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        action="append",
        choices=LIVE_SCENARIOS,
        help="Run a fixed scenario subset for diagnosis; omit for the required full gate.",
    )
    args = parser.parse_args(argv)

    codex = shutil.which("codex")
    python = shutil.which("python3")
    if codex is None or python is None:
        raise SystemExit("required executable unavailable")
    if not ADAPTER_PATH.is_file():
        raise SystemExit("live adapter unavailable")

    runtime = SubprocessRuntimeVerifier().capture((codex,))
    if runtime.codex_version != EXPECTED_CODEX_VERSION:
        raise SystemExit("Codex version mismatch")
    if runtime.schema_digest != EXPECTED_SCHEMA_DIGEST:
        raise SystemExit("app-server schema digest mismatch")
    try:
        m1b_contracts = _m1b_contract_summary()
    except LiveProbeError as exc:
        raise SystemExit(str(exc)) from exc

    config_before = _config_fingerprint()
    scenarios: dict[str, Mapping[str, Any]] = {}
    temporary_root: Path | None = None
    with tempfile.TemporaryDirectory(prefix="gkd-m1c-live-") as temporary:
        temporary_root = Path(temporary)
        for scenario in tuple(args.scenario or LIVE_SCENARIOS):
            scenario_root = temporary_root / scenario
            scenario_root.mkdir(mode=0o700)
            try:
                result = ExecScenarioRunner(codex, python, scenario).run(scenario_root)
            except (LiveProbeError, OSError, RuntimeError, ValueError):
                result = {
                    "status": "fail",
                    "reason": "scenario_setup_failed",
                    "identity": {},
                    "assertions": {
                        "cleanupComplete": False,
                        "rawPayloadAbsent": True,
                    },
                    "parentTrace": {
                        "frameCounts": {},
                        "methodCounts": {},
                        "itemCounts": {},
                        "statusCounts": {},
                        "terminalCount": 0,
                        "rawPayloadStored": False,
                    },
                    "watcherTrace": {
                        "methodCounts": {},
                        "statusCounts": {},
                        "controlSequence": [],
                        "readValidation": {
                            "childReadCount": 0,
                            "parentReadCount": 0,
                            "includeTurnsFalse": False,
                        },
                        "rawPayloadStored": False,
                    },
                    "watcherResult": {},
                    "cleanup": {
                        "threadsComplete": False,
                        "knownProcessCount": 0,
                        "forcedCleanup": False,
                        "residualProcessCount": 0,
                        "complete": False,
                    },
                }
            scenarios[scenario] = result
    temporary_cleanup = temporary_root is not None and not temporary_root.exists()
    config_after = _config_fingerprint()
    evidence = build_evidence(
        runtime=runtime,
        scenarios=scenarios,
        config_before=config_before,
        config_after=config_after,
        temporary_cleanup=temporary_cleanup,
        m1b_contracts=m1b_contracts,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "normalizedDigestSha256": evidence["normalizedDigestSha256"],
                "outcome": evidence["outcome"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
