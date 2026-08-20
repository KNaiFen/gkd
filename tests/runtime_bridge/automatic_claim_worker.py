from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_task.canonical import FixedClock, canonical_bytes
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import FIXED_TIME


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--task-path", required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--bundle-digest", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-revision", type=int, required=True)
    parser.add_argument("--envelope-id", required=True)
    parser.add_argument("--spawn-result", type=Path, required=True)
    parser.add_argument("--activation-nonce", required=True)
    parser.add_argument("--start-marker", type=Path, required=True)
    args = parser.parse_args()
    while not args.start_marker.exists():
        time.sleep(0.01)
    spawn = json.loads(args.spawn_result.read_bytes())
    bridge = TrustedMainRuntimeBridge(
        args.candidate_root,
        args.task_path,
        RuntimeStore(args.runtime_root),
        args.bundle_root,
        args.bundle_digest,
        FixedClock(FIXED_TIME),
    )
    try:
        result = bridge.claim(
            args.expected_head,
            args.expected_revision,
            args.envelope_id,
            spawn,
            args.activation_nonce,
        )
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
