from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from gkd_role.activation import ActivationEvidenceProvider
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService


parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--task-path", required=True)
parser.add_argument("--runtime", type=Path, required=True)
parser.add_argument("--activation", required=True)
parser.add_argument("--expected", type=Path, required=True)
parser.add_argument("--provider-digest", required=True)
parser.add_argument("--envelope", required=True)
args = parser.parse_args()

try:
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    runtime = RuntimeStore(args.runtime)
    provider = ActivationEvidenceProvider(runtime, args.activation, expected, args.provider_digest)
    service = TaskService(args.candidate, args.task_path, runtime=runtime, evidence_provider=provider)
    state = service._state()
    result = service.claim(service.status()["head"], state["revision"], args.envelope)
except TaskError as error:
    print(json.dumps({"status": "error", "error": error.code}, sort_keys=True), file=sys.stderr)
    raise SystemExit(2)
print(json.dumps(result, sort_keys=True))
