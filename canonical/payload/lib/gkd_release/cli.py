"""Read-only release-candidate record CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from .core import build_release_candidate, promotion_request, validate_traceability


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
    parser.add_argument("command", choices=("validate-traceability", "promotion-plan"))
    parser.add_argument("--input", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        value = _read(args.input)
        if args.command == "validate-traceability":
            validate_traceability(value)
            result = {"status": "valid", "decisions": len(value["decisions"])}
        else:
            result = promotion_request(value)
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
