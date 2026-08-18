"""Machine CLI for canonical role and routing operations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from gkd_task.canonical import canonical_bytes, read_canonical_json, sha256_bytes
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore

from .activation import record_activation
from .migration import apply_migration, migration_plan, verify_migration
from .roles import context_manifest, resume_snapshot, role_action, role_catalog
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
    activation.add_argument("--bundle-root", type=Path, required=True)
    activation.add_argument("--bundle-digest", required=True)
    activation.add_argument("--runtime-root", type=Path, required=True)
    activation.add_argument("--candidate-root", type=Path, required=True)
    activation.add_argument("--expected", type=Path, required=True)
    activation.add_argument("--provider-command", type=Path, required=True)
    activation.add_argument("--provider-digest", required=True)
    activation.add_argument("--nonce", required=True)
    return parser


def _read(path: Path, code: str, validator=None) -> dict:
    if path.is_symlink():
        raise TaskError(code)
    return read_canonical_json(path, code, validator)


def _host_observation(args: argparse.Namespace, expected: dict) -> dict:
    command = args.provider_command
    if not command.is_absolute() or command.is_symlink() or not command.is_file():
        raise TaskError("INVALID_ACTIVATION_PROVIDER")
    resolved = command.resolve()
    candidate = args.candidate_root.resolve()
    try:
        resolved.relative_to(candidate)
    except ValueError:
        pass
    else:
        raise TaskError("UNTRUSTED_ACTIVATION_PROVIDER")
    if sha256_bytes(command.read_bytes()) != args.provider_digest:
        raise TaskError("ACTIVATION_PROVIDER_DRIFT")
    try:
        result = subprocess.run(
            [os.fspath(command)],
            input=canonical_bytes(expected),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.TimeoutExpired):
        raise TaskError("ACTIVATION_PROVIDER_FAILED") from None
    if result.returncode != 0:
        raise TaskError("ACTIVATION_PROVIDER_FAILED")
    try:
        observation = json.loads(result.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_ACTIVATION_OBSERVATION") from None
    if not isinstance(observation, dict) or canonical_bytes(observation) != result.stdout:
        raise TaskError("INVALID_ACTIVATION_OBSERVATION")
    if "providerDigest" in observation:
        raise TaskError("INVALID_ACTIVATION_OBSERVATION")
    observation["providerDigest"] = args.provider_digest
    return observation


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
        expected = _read(args.expected, "INVALID_ACTIVATION_REQUEST")
        observation = _host_observation(args, expected)
        catalog = role_catalog(args.bundle_root, args.bundle_digest)
        return record_activation(RuntimeStore(args.runtime_root), catalog, expected, observation, args.nonce)
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
