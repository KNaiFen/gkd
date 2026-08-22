"""Read-only release-candidate record CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from .core import (
    build_release_candidate,
    post_merge_promotion_request,
    promotion_request,
    validate_post_merge_release_record,
    validate_traceability,
)
from .verification import (
    build_l4_canary_request,
    run_l1_properties,
    run_l2_probe,
    validate_forward_eval_trace,
    validate_l3_forward_eval_record,
    validate_l4_canary_request,
    validate_l4_canary_result,
)


def _read(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise TaskError("INVALID_RELEASE_INPUT")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_RELEASE_INPUT") from None
    if not isinstance(value, dict) or canonical_bytes(value) != path.read_bytes():
        raise TaskError("INVALID_RELEASE_INPUT")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate-traceability", "l1-properties", "l2-probe", "validate-l3-trace", "validate-l3-record", "canary-plan", "validate-canary-request", "validate-canary-result", "validate-final-gate", "promotion-plan", "promotion-input"))
    parser.add_argument("--input", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        value = _read(args.input)
        if args.command == "validate-traceability":
            validate_traceability(value)
            result = {"status": "valid", "decisions": len(value["decisions"])}
        elif args.command == "l1-properties":
            result = run_l1_properties(value)
        elif args.command == "l2-probe":
            result = run_l2_probe(value)
        elif args.command == "validate-l3-trace":
            result = {"status": "valid", "sourceSha": validate_forward_eval_trace(value)["sourceSha"]}
        elif args.command == "validate-l3-record":
            result = {"status": "valid", "sourceSha": validate_l3_forward_eval_record(value)["sourceSha"]}
        elif args.command == "canary-plan":
            result = build_l4_canary_request(value)
        elif args.command == "validate-canary-request":
            result = {"status": "valid", "sourceSha": validate_l4_canary_request(value)["sourceSha"]}
        elif args.command == "validate-canary-result":
            request = value.get("request") if isinstance(value, dict) else None
            result_value = value.get("result") if isinstance(value, dict) else None
            result = {"status": "valid", "sourceSha": validate_l4_canary_result(request, result_value)["sourceSha"]}
        elif args.command == "validate-final-gate":
            result = {"status": "valid", "sourceSha": validate_post_merge_release_record(value)["finalGate"]["sourceSha"]}
        elif args.command == "promotion-input":
            result = post_merge_promotion_request(value)
        else:
            result = promotion_request(value)
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
