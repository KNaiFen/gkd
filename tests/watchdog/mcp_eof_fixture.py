#!/usr/bin/env python3
"""MCP subprocess fixture that owns an actual hanging app-server child."""

from __future__ import annotations

from pathlib import Path
import os
import sys

from gkd_watchdog.mcp_server import JsonLineWriter, McpServer
from gkd_watchdog.runtime import AppServerFactory, StaticRuntimeVerifier
from gkd_watchdog.watcher import WatchService


FAKE_SERVER = Path(__file__).with_name("fake_app_server.py")


class FixedResolver:
    def resolve(self):
        scenario = os.environ.get("GKD_EOF_SCENARIO", "cancel_hang")
        return (sys.executable, str(FAKE_SERVER), scenario)


def service() -> WatchService:
    factory = AppServerFactory(
        FixedResolver(),
        StaticRuntimeVerifier(),
    )
    return WatchService(factory, cancel_poll_ms=10)


def main() -> int:
    McpServer(service, writer=JsonLineWriter(sys.stdout)).serve(sys.stdin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
