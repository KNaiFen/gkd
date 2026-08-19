"""Machine CLI for canonical role and routing operations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from gkd_task.canonical import canonical_bytes, read_canonical_json
from gkd_task.errors import TaskError

from .migration import apply_migration, migration_plan, verify_migration
from .roles import context_manifest, locked_bundle_digest, resume_snapshot, role_action, role_catalog
from .routing import decide_route
from .waiting import new_wait_state, transition, validate_wait_state


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)
    for name in ("roles", "context"):
        command = commands.add_parser(name)
        command.add_argument("--bundle-root", type=Path, required=True)
        command.add_argument("--bundle-digest", required=True)
        if name == "context":
            command.add_argument("--role", required=True)
    route = commands.add_parser("route")
    route.add_argument("--input", type=Path, required=True)
    action = commands.add_parser("role-action")
    action.add_argument("--bundle-root", type=Path, required=True)
    action.add_argument("--role", required=True)
    action.add_argument("--action", required=True)
    resume = commands.add_parser("resume-snapshot")
    resume.add_argument("--context", type=Path, required=True)
    resume.add_argument("--task", type=Path, required=True)
    wait_init = commands.add_parser("wait-init")
    wait_init.add_argument("--facts", type=Path, required=True)
    wait_init.add_argument("--started-at", required=True)
    wait_transition = commands.add_parser("wait-transition")
    wait_transition.add_argument("--state", type=Path, required=True)
    wait_transition.add_argument("--observation", type=Path, required=True)
    for name in ("migration-plan", "migration-apply", "migration-verify"):
        command = commands.add_parser(name)
        command.add_argument("--bundle-root", type=Path, required=True)
        command.add_argument("--bundle-digest", required=True)
        command.add_argument("--home-root", type=Path, required=True)
    activation = commands.add_parser("activation-record")
    activation.add_argument("--runtime-root", type=Path, required=True)
    activation.add_argument("--expected", type=Path, required=True)
    activation.add_argument("--nonce", required=True)
    return parser


def _read(path: Path, code: str, validator=None) -> dict:
    if path.is_symlink():
        raise TaskError(code)
    return read_canonical_json(path, code, validator)


def _dispatch(args: argparse.Namespace) -> dict:
    if args.command == "roles":
        return role_catalog(args.bundle_root, args.bundle_digest)
    if args.command == "context":
        return context_manifest(args.bundle_root, args.bundle_digest, args.role)
    if args.command == "route":
        return decide_route(_read(args.input, "INVALID_ROUTE_REQUEST"))
    if args.command == "role-action":
        return role_action(args.bundle_root, args.role, args.action)
    if args.command == "resume-snapshot":
        return resume_snapshot(_read(args.context, "INVALID_RESUME_SNAPSHOT"), _read(args.task, "INVALID_RESUME_SNAPSHOT"))
    if args.command == "wait-init":
        return new_wait_state(_read(args.facts, "INVALID_WAIT_STATE"), args.started_at)
    if args.command == "wait-transition":
        return transition(_read(args.state, "INVALID_WAIT_STATE", validate_wait_state), _read(args.observation, "INVALID_WAIT_OBSERVATION"))
    if args.command == "migration-plan":
        return migration_plan(args.bundle_root, args.home_root, args.bundle_digest)
    if args.command == "migration-apply":
        return apply_migration(args.bundle_root, args.home_root, args.bundle_digest)
    if args.command == "migration-verify":
        return verify_migration(args.bundle_root, args.home_root, args.bundle_digest)
    if args.command == "activation-record":
        _read(args.expected, "INVALID_ACTIVATION_REQUEST")
        bundle_root = Path(__file__).resolve().parents[2]
        role_catalog(bundle_root, locked_bundle_digest(bundle_root))
        raise TaskError("ACTIVATION_PROVIDER_UNAVAILABLE")
    raise TaskError("INVALID_ARGUMENTS")


def main(argv: list[str] | None = None) -> int:
    try:
        result = _dispatch(_parser().parse_args(argv))
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, ValueError, TypeError, KeyError, OverflowError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
