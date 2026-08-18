"""Minimal concurrent MCP stdio adapter exposing one blocking watcher tool."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from typing import Any, Callable, Mapping, TextIO

from .constants import MAX_MESSAGE_BYTES
from .model import (
    RequestValidationError,
    WATCH_REQUEST_SCHEMA,
    WatchRequest,
    canonical_json,
)
from .runtime import default_app_server_factory
from .watcher import CancellationToken, WatchService


SERVER_NAME = "gkd-watchdog"
SERVER_VERSION = "1"
TOOL_NAME = "gkd_watch_agent"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2024-11-05")


class JsonLineWriter:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lock = threading.Lock()

    def write(self, message: Mapping[str, Any]) -> None:
        payload = canonical_json(message)
        with self._lock:
            self._stream.write(payload + "\n")
            self._stream.flush()


class McpServer:
    def __init__(
        self,
        service_factory: Callable[[], WatchService],
        *,
        writer: JsonLineWriter,
        max_active_watches: int = 15,
    ) -> None:
        if max_active_watches <= 0:
            raise ValueError("max_active_watches must be positive")
        self._service_factory = service_factory
        self._writer = writer
        self._max_active_watches = max_active_watches
        self._active: dict[Any, CancellationToken] = {}
        self._active_lock = threading.Lock()
        self._workers: set[threading.Thread] = set()
        self._workers_lock = threading.Lock()

    def serve(self, stream: TextIO) -> None:
        for line in stream:
            if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
                self._error(None, -32700, "invalid JSON-RPC message")
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._error(None, -32700, "invalid JSON-RPC message")
                continue
            self.handle(message)
        self._cancel_all()
        with self._workers_lock:
            workers = tuple(self._workers)
        for worker in workers:
            worker.join(timeout=2)

    def handle(self, message: Any) -> None:
        if not isinstance(message, Mapping) or message.get("jsonrpc") != "2.0":
            self._error(None, -32600, "invalid JSON-RPC request")
            return
        method = message.get("method")
        if not isinstance(method, str):
            self._error(message.get("id"), -32600, "invalid JSON-RPC request")
            return

        if "id" not in message:
            self._handle_notification(method, message.get("params", {}))
            return
        request_id = message.get("id")
        if (
            isinstance(request_id, bool)
            or not isinstance(request_id, (int, str))
            or (isinstance(request_id, str) and len(request_id) > 128)
        ):
            self._error(None, -32600, "invalid JSON-RPC request")
            return
        params = message.get("params", {})

        if method == "initialize":
            self._initialize(request_id, params)
        elif method == "tools/list":
            self._tools_list(request_id, params)
        elif method == "tools/call":
            self._tools_call(request_id, params)
        else:
            self._error(request_id, -32601, "method not found")

    def _initialize(self, request_id: Any, params: Any) -> None:
        if not isinstance(params, Mapping):
            self._error(request_id, -32602, "invalid initialize parameters")
            return
        requested = params.get("protocolVersion")
        protocol = (
            requested
            if requested in SUPPORTED_PROTOCOL_VERSIONS
            else SUPPORTED_PROTOCOL_VERSIONS[0]
        )
        self._result(
            request_id,
            {
                "protocolVersion": protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    def _tools_list(self, request_id: Any, params: Any) -> None:
        if not isinstance(params, Mapping) or params:
            self._error(request_id, -32602, "invalid tools/list parameters")
            return
        self._result(
            request_id,
            {
                "tools": [
                    {
                        "name": TOOL_NAME,
                        "description": "Wait for one bound child turn without progress output.",
                        "inputSchema": WATCH_REQUEST_SCHEMA,
                    }
                ]
            },
        )

    def _tools_call(self, request_id: Any, params: Any) -> None:
        if not isinstance(params, Mapping) or set(params) != {"name", "arguments"}:
            self._error(request_id, -32602, "invalid tools/call parameters")
            return
        if params.get("name") != TOOL_NAME:
            self._error(request_id, -32602, "unknown tool")
            return
        try:
            request = WatchRequest.parse(params.get("arguments"))
        except RequestValidationError:
            self._error(request_id, -32602, "invalid watch request")
            return

        cancellation = CancellationToken()
        with self._active_lock:
            if request_id in self._active:
                self._error(request_id, -32600, "duplicate request id")
                return
            if len(self._active) >= self._max_active_watches:
                self._error(request_id, -32000, "watch capacity reached")
                return
            self._active[request_id] = cancellation
        worker = threading.Thread(
            target=self._run_watch,
            args=(request_id, request, cancellation),
            name="gkd-watch-agent",
            daemon=True,
        )
        with self._workers_lock:
            self._workers.add(worker)
        worker.start()

    def _run_watch(
        self,
        request_id: Any,
        request: WatchRequest,
        cancellation: CancellationToken,
    ) -> None:
        try:
            result = self._service_factory().watch(request, cancellation).to_dict()
            is_error = result["outcome"] in {
                "protocol_error",
                "orchestrator_error",
                "parent_steer_rejected",
            }
            self._result(
                request_id,
                {
                    "content": [{"type": "text", "text": canonical_json(result)}],
                    "structuredContent": result,
                    "isError": is_error,
                },
            )
        except Exception:
            self._error(request_id, -32603, "watcher execution failed")
        finally:
            with self._active_lock:
                self._active.pop(request_id, None)
            with self._workers_lock:
                self._workers.discard(threading.current_thread())

    def _handle_notification(self, method: str, params: Any) -> None:
        if method not in {"notifications/cancelled", "$/cancelRequest"}:
            return
        if not isinstance(params, Mapping):
            return
        request_id = params.get("requestId", params.get("id"))
        with self._active_lock:
            cancellation = self._active.get(request_id)
        if cancellation is not None:
            cancellation.cancel()

    def _cancel_all(self) -> None:
        with self._active_lock:
            tokens = tuple(self._active.values())
        for token in tokens:
            token.cancel()

    def _result(self, request_id: Any, result: Any) -> None:
        self._writer.write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _error(self, request_id: Any, code: int, message: str) -> None:
        self._writer.write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    writer = JsonLineWriter(sys.stdout)
    server = McpServer(
        lambda: WatchService(default_app_server_factory()),
        writer=writer,
    )
    server.serve(sys.stdin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
