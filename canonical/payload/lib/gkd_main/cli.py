"""Path-redacted trusted-main task inspection and planning packages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from gkd_task.orchestrator import PlanningPackageStore, resolve_trusted_task_context


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _task_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task-id")


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)
    for name in ("inspect", "preflight"):
        command = commands.add_parser(name)
        _task_selector(command)
    planning = commands.add_parser("planning")
    planning_commands = planning.add_subparsers(dest="planning_command", required=True, parser_class=MachineParser)
    create = planning_commands.add_parser("create")
    _task_selector(create)
    create.add_argument("--requirements", required=True)
    create.add_argument("--plan", required=True)
    create.add_argument("--implementation", required=True)
    inspect = planning_commands.add_parser("inspect")
    _task_selector(inspect)
    inspect.add_argument("--package-selector", required=True)
    return parser


def _bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _context(args: argparse.Namespace):
    return resolve_trusted_task_context(Path.cwd(), _bundle_root(), args.task_id)


def _dispatch(args: argparse.Namespace) -> dict:
    context = _context(args)
    if args.command == "inspect":
        return context.inspect()
    if args.command == "preflight":
        return context.preflight()
    store = PlanningPackageStore(context.runtime)
    if args.planning_command == "create":
        return store.create(
            {
                "requirements.md": args.requirements,
                "plan.md": args.plan,
                "implementation.md": args.implementation,
            }
        )
    return store.inspect(args.package_selector)


def main(argv: list[str] | None = None) -> int:
    try:
        result = _dispatch(_parser().parse_args(argv))
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, ValueError, TypeError, KeyError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0
