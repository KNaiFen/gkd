"""Stable JSON command surface for repository-neutral review workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError

from .core import approve_partial, begin_review, recover_review, recommend_review, resume_review
from .remediation import approve_remediation, begin_remediation, recover_remediation, resume_remediation


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _read(path: Path) -> Any:
    try:
        raw = sys.stdin.buffer.read() if str(path) == "-" else path.read_bytes()
        return json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INPUT_READ_FAILED") from None


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)
    recommend = commands.add_parser("recommend")
    recommend.add_argument("--intent")
    recommend.add_argument("--target")
    start = commands.add_parser("start")
    start.add_argument("--input", type=Path, required=True)
    partial = commands.add_parser("partial-approve")
    partial.add_argument("--input", type=Path, required=True)
    partial.add_argument("--approval", action="append", required=True)
    resume = commands.add_parser("resume")
    resume.add_argument("--input", type=Path, required=True)
    recover = commands.add_parser("recover")
    recover.add_argument("--input", type=Path, required=True)
    remediate = commands.add_parser("remediate")
    remediate.add_argument("--review", type=Path, required=True)
    remediate.add_argument("--findings", type=Path, required=True)
    remediation_partial = commands.add_parser("remediate-partial-approve")
    remediation_partial.add_argument("--input", type=Path, required=True)
    remediation_partial.add_argument("--finding", action="append", required=True)
    remediation_resume = commands.add_parser("remediate-resume")
    remediation_resume.add_argument("--input", type=Path, required=True)
    remediation_recover = commands.add_parser("remediate-recover")
    remediation_recover.add_argument("--input", type=Path, required=True)
    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "recommend":
        return recommend_review(args.intent, args.target)
    if args.command == "start":
        value = _read(args.input)
        if not isinstance(value, dict) or set(value) != {"entryPoint", "adapter", "target", "intent", "machineFacts"}:
            raise TaskError("REVIEW_REQUEST_INVALID")
        return begin_review(
            value["entryPoint"],
            value["adapter"],
            target=value["target"],
            intent=value["intent"],
            machine_facts=value["machineFacts"],
        )
    if args.command == "partial-approve":
        return approve_partial(_read(args.input), args.approval)
    if args.command == "resume":
        return resume_review(_read(args.input), {"continue": True})
    if args.command == "recover":
        return recover_review(_read(args.input))
    if args.command == "remediate":
        return begin_remediation(_read(args.review), _read(args.findings))
    if args.command == "remediate-partial-approve":
        return approve_remediation(_read(args.input), args.finding)
    if args.command == "remediate-resume":
        return resume_remediation(_read(args.input), {"continue": True})
    return recover_remediation(_read(args.input))


def main(argv: list[str] | None = None) -> int:
    try:
        value = _dispatch(_parser().parse_args(argv))
    except TaskError as error:
        value = {"error": error.code, "status": "error"}
        sys.stdout.buffer.write(canonical_bytes(value))
        return 2
    except (OSError, TypeError, ValueError, KeyError):
        sys.stdout.buffer.write(canonical_bytes({"error": "FILESYSTEM_ERROR", "status": "error"}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
