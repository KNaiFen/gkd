"""Read-only CLI for deterministic finalization records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError

from .core import promotion_plan, validate_finalization


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _record(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise TaskError("INVALID_FINALIZATION")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_FINALIZATION") from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError("INVALID_FINALIZATION")
    validate_finalization(value)
    return value


def _existing(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise TaskError("INVALID_PROMOTION_RECEIPT")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_PROMOTION_RECEIPT") from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError("INVALID_PROMOTION_RECEIPT")
    return value


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)
    validate = commands.add_parser("validate")
    validate.add_argument("--record", type=Path, required=True)
    promotion = commands.add_parser("promotion-plan")
    promotion.add_argument("--record", type=Path, required=True)
    promotion.add_argument("--existing", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        record = _record(args.record)
        if args.command == "validate":
            result = {
                "status": "valid",
                "mode": record["finalization"]["mode"],
                "sourceSha": record["metadata"]["sourceSha"],
                "recordDigest": record["recordDigest"],
            }
        else:
            result = promotion_plan(record, _existing(args.existing) if args.existing else None)
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2
    except (ValueError, TypeError, KeyError, OverflowError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "INTERNAL_ERROR"}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
