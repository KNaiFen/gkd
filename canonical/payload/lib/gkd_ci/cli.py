"""Machine-readable GitHub fixed-head monitor CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError

from .monitor import MonitorRequest, monitor_fixed_head
from .policy import POLICY_PATH, load_validated_policy


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise TaskError("INVALID_ARGUMENTS")


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    parser.add_argument("--poll-interval-seconds", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args: argparse.Namespace | None = None
    try:
        args = _parser().parse_args(argv)
        policy = load_validated_policy(args.checkout, args.repository, args.policy)
        request = MonitorRequest(
            checkout=args.checkout,
            repository=args.repository,
            pull_request=args.pull_request,
            expected_head=args.expected_head,
            policy_path=args.policy,
            policy_digest=policy.digest,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        result = monitor_fixed_head(request)
    except TaskError as error:
        result = {
            "baseBranch": None,
            "checks": [],
            "elapsedSeconds": 0,
            "expectedHead": None,
            "headBranch": None,
            "observations": 0,
            "observedHead": None,
            "outcome": "error",
            "policyDigest": None,
            "provider": "github",
            "pullRequest": None,
            "pullRequestState": None,
            "reason": error.code,
            "repository": None,
            "requiredChecks": [],
            "schemaVersion": 1,
        }
    except OSError:
        result = {
            "baseBranch": None,
            "checks": [],
            "elapsedSeconds": 0,
            "expectedHead": None,
            "headBranch": None,
            "observations": 0,
            "observedHead": None,
            "outcome": "error",
            "policyDigest": None,
            "provider": "github",
            "pullRequest": None,
            "pullRequestState": None,
            "reason": "FILESYSTEM_ERROR",
            "repository": None,
            "requiredChecks": [],
            "schemaVersion": 1,
        }
    except (TypeError, ValueError, KeyError, OverflowError):
        result = {
            "baseBranch": None,
            "checks": [],
            "elapsedSeconds": 0,
            "expectedHead": None,
            "headBranch": None,
            "observations": 0,
            "observedHead": None,
            "outcome": "error",
            "policyDigest": None,
            "provider": "github",
            "pullRequest": None,
            "pullRequestState": None,
            "reason": "INTERNAL_ERROR",
            "repository": None,
            "requiredChecks": [],
            "schemaVersion": 1,
        }
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0 if result["outcome"] == "success" else 2 if result["outcome"] == "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
