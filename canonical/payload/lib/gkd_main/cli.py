"""Path-redacted trusted-main task inspection and planning packages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gkd_task.canonical import canonical_bytes
from gkd_task.canonical import read_canonical_json
from gkd_task.errors import TaskError
from gkd_task.orchestrator import PlanningPackageStore, resolve_trusted_task_context
from .orchestrator import TrustedMainCIFacade, TrustedMainOrchestrator
from .facts import render_facts_block


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

    delivery = commands.add_parser("delivery")
    _task_selector(delivery)

    facts = commands.add_parser("facts")
    facts_commands = facts.add_subparsers(dest="facts_command", required=True, parser_class=MachineParser)
    render = facts_commands.add_parser("render")
    _task_selector(render)
    render.add_argument("--document", choices=("requirements", "plan", "implementation", "delivery", "acceptance"), required=True)
    render.add_argument("--review-file", type=Path)
    render.add_argument("--ci-file", type=Path)
    render.add_argument("--output", type=Path)
    render.add_argument("--format", choices=("json", "markdown"), default="json")
    verify = facts_commands.add_parser("verify")
    verify.add_argument("--input", type=Path, required=True)

    ci = commands.add_parser("ci")
    ci_commands = ci.add_subparsers(dest="ci_command", required=True, parser_class=MachineParser)
    monitor = ci_commands.add_parser("monitor")
    monitor.add_argument("--pull-request", type=int, required=True)
    monitor.add_argument("--expected-head", required=True)
    monitor.add_argument("--timeout-seconds", type=int, default=3600)
    monitor.add_argument("--poll-interval-seconds", type=int, default=60)

    for name in ("accept", "rework"):
        command = commands.add_parser(name)
        _task_selector(command)
        command.add_argument("--review-file", type=Path, required=True)
        if name == "accept":
            command.add_argument("--merge", action="store_true")
    stage = commands.add_parser("stage")
    stage.add_argument("--project-root", type=Path)
    stage.add_argument("--production-root", type=Path, required=True)
    stage.add_argument("--refresh", action="store_true")
    stage.add_argument("--pack", action="append", default=[])
    return parser


def _bundle_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _context(args: argparse.Namespace):
    return resolve_trusted_task_context(Path.cwd(), _bundle_root(), args.task_id)


def _dispatch(args: argparse.Namespace) -> dict:
    if args.command == "facts" and args.facts_command == "verify":
        facts = read_canonical_json(args.input, "INVALID_DOCUMENT_FACTS")
        from .facts import validate_machine_facts

        validate_machine_facts(facts)
        return {"status": "valid", "document": facts["document"], "factsDigest": facts["factsDigest"]}
    if args.command == "ci":
        return TrustedMainCIFacade(Path.cwd()).monitor(
            args.pull_request,
            args.expected_head,
            args.timeout_seconds,
            args.poll_interval_seconds,
        )
    if args.command == "stage":
        from .orchestrator import TrustedMainStageFacade

        return TrustedMainStageFacade(_bundle_root()).transition(
            args.project_root or Path.cwd(),
            args.production_root,
            refresh=args.refresh,
            packs=tuple(args.pack),
        )
    context = _context(args)
    if args.command == "inspect":
        return context.inspect()
    if args.command == "preflight":
        return context.preflight()
    orchestrator = TrustedMainOrchestrator.from_current(
        _bundle_root(),
        args.task_id,
        current_path=Path.cwd(),
        runtime=context.runtime,
    )
    if args.command == "facts" and args.facts_command == "render":
        review = read_canonical_json(args.review_file, "INVALID_REVIEW") if args.review_file else None
        ci = read_canonical_json(args.ci_file, "TERMINAL_RESULT_INVALID") if args.ci_file else None
        facts = orchestrator.render_facts(args.document, review=review, ci=ci)
        if args.output is not None:
            from gkd_task.canonical import atomic_write

            encoded = canonical_bytes(facts) if args.format == "json" else render_facts_block(facts).encode("utf-8")
            atomic_write(args.output, encoded)
        return facts
    if args.command == "delivery":
        return orchestrator.deliver()
    if args.command in {"accept", "rework"}:
        try:
            args.review_file.resolve().relative_to(context.candidate_root.resolve())
        except ValueError:
            pass
        else:
            raise TaskError("UNTRUSTED_ACCEPTANCE_INPUT" if args.command == "accept" else "UNTRUSTED_REWORK_INPUT")
        review = read_canonical_json(args.review_file, "INVALID_REVIEW")
        return orchestrator.rework(review) if args.command == "rework" else orchestrator.accept(review, args.merge)

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
