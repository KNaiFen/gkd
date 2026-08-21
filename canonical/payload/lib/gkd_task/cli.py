"""Command-line entry point for the deterministic GKD task core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .acceptance import SubprocessGitHubAdapter, accept_candidate, rework_candidate, validate_review
from .canonical import SystemClock, SystemNonce, canonical_bytes, read_canonical_json
from .errors import TaskError
from .gitops import common_dir, git_root
from .locator import resolve_candidate
from .migration import migrate_v1
from .runtime import RuntimeStore
from .service import TaskService, bootstrap_task


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _runtime(candidate: Path, value: Path | None) -> RuntimeStore | None:
    if value is not None:
        candidate_resolved = candidate.resolve()
        runtime_resolved = value.resolve(strict=False)
        try:
            runtime_resolved.relative_to(candidate_resolved)
        except ValueError:
            pass
        else:
            raise TaskError("RUNTIME_ROOT_OVERLAP")
        try:
            candidate_resolved.relative_to(runtime_resolved)
        except ValueError:
            pass
        else:
            raise TaskError("RUNTIME_ROOT_OVERLAP")
        return RuntimeStore(value)
    return None


def _add_candidate(parser: argparse.ArgumentParser, runtime_required: bool = False) -> None:
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--task-path", required=True)
    parser.add_argument("--runtime-root", type=Path, required=runtime_required)


def _add_cas(parser: argparse.ArgumentParser) -> None:
    _add_candidate(parser)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-revision", type=int, required=True)


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)

    bootstrap = commands.add_parser("bootstrap")
    bootstrap.add_argument("--main-root", type=Path, required=True)
    bootstrap.add_argument("--candidate-root", type=Path, required=True)
    bootstrap.add_argument("--package-root", type=Path, required=True)
    bootstrap.add_argument("--task-id", required=True)
    bootstrap.add_argument("--task-path", required=True)
    bootstrap.add_argument("--repository", required=True)
    bootstrap.add_argument("--base-branch", required=True)
    bootstrap.add_argument("--base-sha", required=True)
    bootstrap.add_argument("--task-branch", required=True)
    bootstrap.add_argument("--runtime-root", type=Path)

    for name in ("status", "doctor"):
        command = commands.add_parser(name)
        command.add_argument("--repository", required=True)
        command.add_argument("--task-id", required=True)
        command.add_argument("--task-branch", required=True)
        command.add_argument("--task-path", required=True)
        command.add_argument("--candidate-root", type=Path)
        command.add_argument("--runtime-root", type=Path, required=True)
        if name == "doctor":
            command.add_argument("--mode", choices=("static", "live", "historical"), required=True)

    for name in ("attach", "handoff", "recover"):
        command = commands.add_parser(name)
        _add_candidate(command)

    requirements = commands.add_parser("requirements-ready")
    _add_cas(requirements)

    propose = commands.add_parser("plan-propose")
    _add_cas(propose)
    propose.add_argument("--plan-file", type=Path, required=True)
    propose.add_argument("--implementation-file", type=Path)

    approve = commands.add_parser("plan-approve")
    _add_cas(approve)
    approve.add_argument("--decision-ref", required=True)
    approve.add_argument("--authorize-implementation", action="store_true")
    approve.add_argument("--mode", choices=("implement_only", "implement_and_merge_on_acceptance"))
    approve.add_argument("--action", dest="actions", action="append")

    authorize = commands.add_parser("authorize")
    _add_cas(authorize)
    authorize.add_argument("--decision-ref", required=True)
    authorize.add_argument("--mode", choices=("implement_only", "implement_and_merge_on_acceptance"), required=True)
    authorize.add_argument("--action", dest="actions", action="append", required=True)

    offer = commands.add_parser("offer")
    _add_cas(offer)
    offer.add_argument("--route", required=True)
    offer.add_argument("--role-digest", required=True)
    offer.add_argument("--config-digest", required=True)
    offer.add_argument("--expires-at", required=True)
    offer.add_argument("--role-name")
    offer.add_argument("--bundle-digest")

    claim = commands.add_parser("claim")
    _add_cas(claim)
    claim.add_argument("--envelope-id", required=True)
    claim.add_argument("--activation-id")

    activation_recover = commands.add_parser("activation-recover")
    _add_candidate(activation_recover, runtime_required=True)
    activation_recover.add_argument("--activation-id", required=True)

    for name in ("revoke", "reclaim"):
        command = commands.add_parser(name)
        _add_cas(command)
        command.add_argument("--reason", required=True)

    block = commands.add_parser("block")
    _add_cas(block)
    block.add_argument("--reason", required=True)
    block.add_argument("--owner", required=True)

    resume = commands.add_parser("resume")
    _add_cas(resume)

    deliver = commands.add_parser("deliver")
    _add_cas(deliver)
    deliver.add_argument("--claim-id", required=True)
    deliver.add_argument("--candidate-output-bundle-digest")
    deliver.add_argument("--delivery-document-path", required=True)
    deliver.add_argument("--delivery-document-digest", required=True)

    migrate = commands.add_parser("migrate-v1")
    _add_cas(migrate)

    accept = commands.add_parser("accept")
    accept.add_argument("--trusted-root", type=Path, required=True)
    accept.add_argument("--candidate-root", type=Path, required=True)
    accept.add_argument("--task-path", required=True)
    accept.add_argument("--repository", required=True)
    accept.add_argument("--pr", type=int, required=True)
    accept.add_argument("--candidate-head", required=True)
    accept.add_argument("--required-check", action="append", default=[])
    accept.add_argument("--review-file", type=Path, required=True)
    accept.add_argument("--adapter-command", type=Path, required=True)
    accept.add_argument("--runtime-root", type=Path)
    accept.add_argument("--actor-role", choices=("executor", "acceptor", "main"), required=True)
    accept.add_argument("--merge", action="store_true")

    rework = commands.add_parser("rework")
    rework.add_argument("--trusted-root", type=Path, required=True)
    rework.add_argument("--candidate-root", type=Path, required=True)
    rework.add_argument("--task-path", required=True)
    rework.add_argument("--repository", required=True)
    rework.add_argument("--pr", type=int, required=True)
    rework.add_argument("--candidate-head", required=True)
    rework.add_argument("--review-file", type=Path, required=True)
    rework.add_argument("--adapter-command", type=Path, required=True)
    rework.add_argument("--runtime-root", type=Path, required=True)
    rework.add_argument("--actor-role", choices=("executor", "acceptor", "main"), required=True)
    return parser


def _service(args: Any) -> TaskService:
    runtime = _runtime(args.candidate_root, getattr(args, "runtime_root", None))
    activation_values = (
        getattr(args, "activation_id", None),
    )
    if any(value is not None for value in activation_values):
        raise TaskError("TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE")
    else:
        provider = None
    return TaskService(args.candidate_root, args.task_path, runtime=runtime, evidence_provider=provider)


def _dispatch(args: Any) -> dict[str, Any]:
    if args.command == "bootstrap":
        return bootstrap_task(
            args.main_root,
            args.candidate_root,
            args.package_root,
            args.task_id,
            args.task_path,
            args.repository,
            args.base_branch,
            args.base_sha,
            args.task_branch,
            args.runtime_root,
        )
    if args.command in {"status", "doctor"}:
        runtime = RuntimeStore(args.runtime_root)
        candidate = resolve_candidate(
            args.repository,
            args.task_id,
            args.task_branch,
            args.task_path,
            runtime,
            args.candidate_root,
            Path.cwd(),
        )
        service = TaskService(candidate, args.task_path, runtime=runtime)
        return service.status() if args.command == "status" else service.doctor(args.mode)
    if args.command in {"accept", "rework"}:
        candidate_root = args.candidate_root.resolve()
        for untrusted_path in (args.review_file.resolve(), args.adapter_command.resolve()):
            try:
                untrusted_path.relative_to(candidate_root)
            except ValueError:
                continue
            raise TaskError("UNTRUSTED_ACCEPTANCE_INPUT" if args.command == "accept" else "UNTRUSTED_REWORK_INPUT")
        review = read_canonical_json(args.review_file, "INVALID_REVIEW", validate_review)
        if args.command == "rework":
            return rework_candidate(
                args.trusted_root,
                args.candidate_root,
                args.task_path,
                args.repository,
                args.pr,
                args.candidate_head,
                review,
                SubprocessGitHubAdapter(args.adapter_command),
                args.actor_role,
                runtime=_runtime(args.candidate_root, args.runtime_root),
            )
        return accept_candidate(
            args.trusted_root,
            args.candidate_root,
            args.task_path,
            args.repository,
            args.pr,
            args.candidate_head,
            sorted(args.required_check),
            review,
            SubprocessGitHubAdapter(args.adapter_command),
            args.actor_role,
            args.merge,
            runtime=_runtime(args.candidate_root, args.runtime_root),
        )
    if args.command == "migrate-v1":
        candidate = git_root(args.candidate_root)
        runtime = _runtime(candidate, args.runtime_root) or RuntimeStore(common_dir(candidate) / "gkd-runtime")
        return migrate_v1(
            candidate,
            args.task_path,
            runtime,
            args.expected_head,
            args.expected_revision,
            SystemClock(),
            SystemNonce(),
        )

    service = _service(args)
    if args.command == "attach":
        return service.attach()
    if args.command == "handoff":
        return service.handoff()
    if args.command == "recover":
        return service.recover()
    if args.command == "requirements-ready":
        return service.requirements_ready(args.expected_head, args.expected_revision)
    if args.command == "plan-propose":
        return service.propose_plan(args.expected_head, args.expected_revision, args.plan_file, args.implementation_file)
    if args.command == "plan-approve":
        return service.approve_plan(
            args.expected_head,
            args.expected_revision,
            args.decision_ref,
            args.authorize_implementation,
            args.mode,
            sorted(args.actions) if args.actions else None,
        )
    if args.command == "authorize":
        return service.authorize(args.expected_head, args.expected_revision, args.decision_ref, args.mode, sorted(args.actions))
    if args.command == "offer":
        return service.offer(args.expected_head, args.expected_revision, args.route, args.role_digest, args.config_digest, args.expires_at, args.role_name, args.bundle_digest)
    if args.command == "claim":
        return service.claim(args.expected_head, args.expected_revision, args.envelope_id)
    if args.command == "activation-recover":
        return service.recover_activation()
    if args.command == "revoke":
        return service.revoke(args.expected_head, args.expected_revision, args.reason)
    if args.command == "reclaim":
        return service.reclaim(args.expected_head, args.expected_revision, args.reason)
    if args.command == "block":
        return service.block(args.expected_head, args.expected_revision, args.reason, args.owner)
    if args.command == "resume":
        return service.resume(args.expected_head, args.expected_revision)
    if args.command == "deliver":
        return service.deliver(
            args.expected_head,
            args.expected_revision,
            args.claim_id,
            args.candidate_output_bundle_digest,
            args.delivery_document_path,
            args.delivery_document_digest,
        )
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
