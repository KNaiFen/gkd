#!/usr/bin/env python3
"""Actual stdio subprocess fixture for app-server JSON-RPC contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def write(value) -> None:
    sys.stdout.write(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n")
    sys.stdout.flush()


def response(request_id, result) -> None:
    write({"jsonrpc": "2.0", "id": request_id, "result": result})


def main() -> int:
    scenario = sys.argv[1]
    pid_file = os.environ.get("GKD_FAKE_PID_FILE")
    if pid_file:
        Path(pid_file).write_text(str(os.getpid()), encoding="ascii")
    for line in sys.stdin:
        request = json.loads(line)
        request_id = request["id"]
        method = request["method"]
        if scenario == "silent":
            continue
        if scenario == "malformed":
            sys.stdout.write("{malformed\n")
            sys.stdout.flush()
            continue
        if scenario == "eof":
            return 0
        if scenario == "unknown_id":
            response(request_id + 100, {})
            continue
        if scenario == "duplicate":
            response(request_id, {})
            response(request_id, {})
            continue

        if method == "initialize":
            if scenario == "initialize_hang":
                continue
            response(
                request_id,
                {
                    "codexHome": "<redacted>",
                    "platformFamily": "unix",
                    "platformOs": "test",
                    "userAgent": "fake",
                },
            )
            continue
        if method == "thread/read":
            thread_id = request["params"]["threadId"]
            is_child = thread_id == "child-thread-1"
            response(
                request_id,
                {
                    "thread": {
                        "id": thread_id,
                        "sessionId": "session-1",
                        "parentThreadId": "parent-thread-1" if is_child else None,
                        "status": {"type": "active"},
                        "turns": [],
                        "updatedAt": 1,
                    }
                },
            )
            if scenario == "normal" and is_child:
                write(
                    {
                        "jsonrpc": "2.0",
                        "method": "turn/completed",
                        "params": {
                            "threadId": thread_id,
                            "cookie": "fixture-cookie-secret",
                            "token=field-secret": "present",
                            "privateKey": "-----BEGIN PRIVATE KEY-----fixture",
                            "localPath": "/Users/private/session.jsonl",
                            "turn": {
                                "id": "child-turn-1",
                                "status": "completed",
                                "items": [
                                    {
                                        "type": "agentMessage",
                                        "text": "token=fixture-secret",
                                    }
                                ],
                            },
                        },
                    }
                )
            elif scenario == "steer_rejected" and is_child:
                write(
                    {
                        "jsonrpc": "2.0",
                        "method": "turn/completed",
                        "params": {
                            "threadId": thread_id,
                            "turn": {
                                "id": "child-turn-1",
                                "status": "failed",
                                "items": [],
                            },
                        },
                    }
                )
            elif scenario == "system_error" and is_child:
                write(
                    {
                        "jsonrpc": "2.0",
                        "method": "thread/status/changed",
                        "params": {
                            "threadId": thread_id,
                            "status": {"type": "systemError"},
                            "Authorization": "Bearer fixture-secret",
                        },
                    }
                )
            continue
        if method == "turn/interrupt":
            if scenario == "cancel_hang":
                continue
            response(request_id, {})
            if scenario == "system_error":
                write(
                    {
                        "jsonrpc": "2.0",
                        "method": "turn/completed",
                        "params": {
                            "threadId": request["params"]["threadId"],
                            "turn": {
                                "id": request["params"]["turnId"],
                                "status": "interrupted",
                                "items": [],
                            },
                        },
                    }
                )
            continue
        if method == "turn/steer":
            if scenario == "steer_rejected":
                write(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "fixture path /Users/private and token=secret",
                            "data": {"type": "expectedTurnMismatch"},
                        },
                    }
                )
            else:
                response(
                    request_id,
                    {"turnId": request["params"]["expectedTurnId"]},
                )
            continue
        response(request_id, {})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
