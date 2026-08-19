"""Subprocess claim fixture used by concurrency contracts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from gkd_task.canonical import FixedClock, SystemNonce, canonical_bytes
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.task_core.evidence_support import FixtureEvidenceProvider, make_fixture_evidence
from tests.task_core.helpers import CONFIG_DIGEST, FIXED_TIME, ROLE_DIGEST, SESSION_DIGEST


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--task-path", required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--revision", type=int, required=True)
    parser.add_argument("--envelope", required=True)
    parser.add_argument("--writer", required=True)
    args = parser.parse_args()
    evidence = make_fixture_evidence(
        args.writer,
        SESSION_DIGEST,
        ROLE_DIGEST,
        CONFIG_DIGEST,
        "manual",
        "active",
        FIXED_TIME,
    )
    try:
        result = TaskService(
            args.candidate,
            args.task_path,
            RuntimeStore(args.runtime),
            FixedClock(FIXED_TIME),
            SystemNonce(),
            FixtureEvidenceProvider(evidence),
        ).claim(args.head, args.revision, args.envelope)
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
