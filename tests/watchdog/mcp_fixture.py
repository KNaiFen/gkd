#!/usr/bin/env python3
"""Subprocess MCP fixture with an injected deterministic watcher session."""

from __future__ import annotations

import sys

from gkd_watchdog.mcp_server import JsonLineWriter, McpServer
from gkd_watchdog.watcher import WatchService
from tests.watchdog.helpers import FakeClock, ScriptedSession


def service() -> WatchService:
    clock = FakeClock()
    session = ScriptedSession(
        clock,
        notifications=[
            (
                0,
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": "child-thread-1",
                        "turn": {
                            "id": "child-turn-1",
                            "status": "completed",
                            "items": [{"text": "private body"}],
                        },
                    },
                },
            )
        ],
    )
    return WatchService(lambda _request: session, clock=clock)


def main() -> int:
    McpServer(service, writer=JsonLineWriter(sys.stdout)).serve(sys.stdin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
