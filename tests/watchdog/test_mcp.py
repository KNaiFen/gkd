from __future__ import annotations

import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
import unittest

from gkd_watchdog.mcp_server import JsonLineWriter, McpServer, TOOL_NAME
from gkd_watchdog.watcher import WatchService

from tests.watchdog.helpers import RealTimeActiveSession, valid_request


MCP_FIXTURE = Path(__file__).with_name("mcp_fixture.py")


class CapturingStream:
    def __init__(self) -> None:
        self.messages = []
        self.event = threading.Event()
        self.lock = threading.Lock()

    def write(self, value: str) -> int:
        with self.lock:
            self.messages.append(json.loads(value))
            self.event.set()
        return len(value)

    def flush(self) -> None:
        pass


def rpc(request_id, method, params):
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def read_json_line(process: subprocess.Popen[str], timeout: float = 2.0):
    assert process.stdout is not None
    ready, _, _ = select.select([process.stdout.fileno()], [], [], timeout)
    if not ready:
        raise AssertionError("timed out waiting for MCP response")
    line = process.stdout.readline()
    if not line:
        raise AssertionError("MCP process closed without a response")
    return json.loads(line)


class McpAdapterTests(unittest.TestCase):
    def test_subprocess_initialize_list_call_and_success_framing(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            (sys.executable, str(MCP_FIXTURE)),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            assert process.stdin is not None
            process.stdin.write(
                json.dumps(
                    rpc(
                        1,
                        "initialize",
                        {"protocolVersion": "2025-06-18", "capabilities": {}},
                    )
                )
                + "\n"
            )
            process.stdin.flush()
            initialized = read_json_line(process)

            process.stdin.write(json.dumps(rpc(2, "tools/list", {})) + "\n")
            process.stdin.flush()
            listed = read_json_line(process)

            process.stdin.write(
                json.dumps(
                    rpc(
                        3,
                        "tools/call",
                        {"name": TOOL_NAME, "arguments": valid_request(maxWaitMs=1_000)},
                    )
                )
                + "\n"
            )
            process.stdin.flush()
            called = read_json_line(process)
        finally:
            if process.stdin is not None:
                process.stdin.close()
            process.wait(timeout=2)
        stderr = process.stderr.read() if process.stderr is not None else ""
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(listed["result"]["tools"][0]["name"], TOOL_NAME)
        self.assertEqual(
            called["result"]["structuredContent"]["outcome"], "normal_terminal"
        )
        self.assertFalse(called["result"]["isError"])
        self.assertEqual(stderr, "")
        self.assertNotIn("private body", json.dumps(called))

    def test_subprocess_invalid_request_uses_jsonrpc_error_without_side_effect(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            (sys.executable, str(MCP_FIXTURE)),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            assert process.stdin is not None
            invalid = valid_request(command="sh -c injected")
            process.stdin.write(
                json.dumps(
                    rpc(7, "tools/call", {"name": TOOL_NAME, "arguments": invalid})
                )
                + "\n"
            )
            process.stdin.flush()
            response = read_json_line(process)
        finally:
            if process.stdin is not None:
                process.stdin.close()
            process.wait(timeout=2)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

        self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(response["error"]["message"], "invalid watch request")
        self.assertNotIn("injected", json.dumps(response))

    def test_invalid_request_never_constructs_watch_service(self) -> None:
        stream = CapturingStream()
        calls = []

        def forbidden_service():
            calls.append("started")
            raise AssertionError("must not start")

        server = McpServer(forbidden_service, writer=JsonLineWriter(stream))
        invalid = valid_request(runtimeEvidenceDigest="missing")
        server.handle(
            rpc(9, "tools/call", {"name": TOOL_NAME, "arguments": invalid})
        )

        self.assertEqual(calls, [])
        self.assertEqual(stream.messages[0]["error"]["code"], -32602)

    def test_health_ticks_emit_no_progress_result_or_log_before_cancel(self) -> None:
        stream = CapturingStream()
        session = RealTimeActiveSession()
        server = McpServer(
            lambda: WatchService(
                lambda _request: session, cancel_poll_ms=10
            ),
            writer=JsonLineWriter(stream),
        )
        request = valid_request(maxWaitMs=2_000, healthIntervalMs=10)
        server.handle(
            rpc(11, "tools/call", {"name": TOOL_NAME, "arguments": request})
        )

        self.assertTrue(session.health_event.wait(timeout=1))
        self.assertEqual(stream.messages, [])

        server.handle(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": 11, "reason": "stop"},
            }
        )
        self.assertTrue(stream.event.wait(timeout=1))
        deadline = time.monotonic() + 1
        while not stream.messages and time.monotonic() < deadline:
            time.sleep(0.01)

        self.assertEqual(len(stream.messages), 1)
        result = stream.messages[0]["result"]["structuredContent"]
        self.assertEqual(result["outcome"], "cancelled")
        methods = [method for method, _ in session.calls]
        self.assertIn("turn/interrupt", methods)
        self.assertNotIn("turn/steer", methods)

    def test_malformed_mcp_json_uses_parse_error_frame(self) -> None:
        stream = CapturingStream()
        server = McpServer(
            lambda: (_ for _ in ()).throw(AssertionError("must not start")),
            writer=JsonLineWriter(stream),
        )
        server.serve(iter(["{bad json\n"]))
        self.assertEqual(stream.messages[0]["error"]["code"], -32700)
        self.assertIsNone(stream.messages[0]["id"])

    def test_active_watch_capacity_is_bounded_before_service_construction(self) -> None:
        stream = CapturingStream()
        blocker = RealTimeActiveSession()
        calls = []

        def service():
            calls.append("started")
            return WatchService(lambda _request: blocker, cancel_poll_ms=10)

        server = McpServer(
            service,
            writer=JsonLineWriter(stream),
            max_active_watches=1,
        )
        arguments = valid_request(maxWaitMs=2_000, healthIntervalMs=10)
        server.handle(
            rpc(21, "tools/call", {"name": TOOL_NAME, "arguments": arguments})
        )
        self.assertTrue(blocker.health_event.wait(timeout=1))
        server.handle(
            rpc(22, "tools/call", {"name": TOOL_NAME, "arguments": arguments})
        )

        deadline = time.monotonic() + 1
        while not stream.messages and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(stream.messages[0]["error"]["code"], -32000)
        self.assertEqual(calls, ["started"])
        server.handle(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": 21},
            }
        )
        deadline = time.monotonic() + 1
        while len(stream.messages) < 2 and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(len(stream.messages), 2)


if __name__ == "__main__":
    unittest.main()
