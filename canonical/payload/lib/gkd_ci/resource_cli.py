"""Machine-readable resource planning and scanner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError

from .recommendations import recommend_ci
from .resources import classify_artifacts
from .scanner import scan_surface


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)
    classify = commands.add_parser("classify")
    classify.add_argument("--input", type=Path, required=True)
    classify.add_argument("--preset", choices=("resource-constrained", "standard", "high-capacity"))
    classify.add_argument("--resource-facts", type=Path)
    recommend = commands.add_parser("recommend")
    recommend.add_argument("--input", type=Path, required=True)
    recommend.add_argument("--goal", choices=("speed-first", "balanced", "cost-aware"), required=True)
    recommend.add_argument("--artifacts", type=Path)
    scan = commands.add_parser("scan")
    scan.add_argument("--surface", choices=("diff", "pull-request", "artifact"), required=True)
    scan.add_argument("--input", type=Path, required=True)
    scan.add_argument("--path")
    return parser


def _read(path: Path) -> Any:
    try:
        raw = sys.stdin.buffer.read() if str(path) == "-" else path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INPUT_READ_FAILED") from None
    return value


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    value = _read(args.input)
    if args.command == "classify":
        facts = _read(args.resource_facts) if args.resource_facts else None
        return classify_artifacts(value, args.preset, facts)
    if args.command == "recommend":
        artifacts = _read(args.artifacts) if args.artifacts else None
        return recommend_ci(value, args.goal, artifacts)
    return scan_surface(args.surface, value, args.path)


def main(argv: list[str] | None = None) -> int:
    try:
        result = _dispatch(_parser().parse_args(argv))
    except TaskError as error:
        sys.stdout.buffer.write(canonical_bytes({"error": error.code, "status": "error"}))
        return 2
    except (OSError, UnicodeDecodeError, TypeError, ValueError, KeyError):
        sys.stdout.buffer.write(canonical_bytes({"error": "FILESYSTEM_ERROR", "status": "error"}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0 if result.get("outcome") not in {"terminal", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
