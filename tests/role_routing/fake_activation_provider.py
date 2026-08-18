#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys


request = json.load(sys.stdin)
if request.get("roleName") != "gkd_executor":
    raise SystemExit(2)
value = {
    "activatedAt": "2026-01-02T03:04:05Z",
    "agentId": "fixture-agent",
    "evidenceClass": "host-runtime-event",
    "model": "gpt-5.6-sol",
    "reasoningEffort": "xhigh",
    "runtimeSeconds": 43200,
    "sandbox": "workspace-write",
    "threadDigest": hashlib.sha256(b"fixture-thread").hexdigest(),
}
print(json.dumps(value, sort_keys=True, separators=(",", ":")))
