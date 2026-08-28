#!/usr/bin/env python3
"""Run task-core contracts and emit deterministic M2-D evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import gkd_bundle
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.results import CanonicalResultError, load_canonical_results
from tests.role_routing.run_contracts import _snapshot_tree


EXECUTION_BUNDLE_DIGEST = "05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad"
REWORK_MUTATIONS = {
    "test_mutation_rework_actor_gate_is_killed",
    "test_mutation_rework_authorization_gate_is_killed",
    "test_mutation_rework_epoch_fence_is_killed",
}


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _directory(path: Path, code: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise TaskError(code)
    return path.resolve()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _group(identifier: str) -> str:
    method = identifier.rsplit(".", 1)[-1]
    if method in REWORK_MUTATIONS:
        return "rework-mutation"
    if ".test_rework." in identifier:
        return "rework-l1-l2"
    return "retained-task-core"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--aio-root", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    parser.add_argument("--implementation-head", required=True)
    args = parser.parse_args()
    try:
        repository = Path(__file__).resolve().parents[2]
        if len(args.implementation_head) != 40 or any(character not in "0123456789abcdef" for character in args.implementation_head):
            raise TaskError("INVALID_IMPLEMENTATION_HEAD")
        current_head = __import__("subprocess").run(
            ["git", "-C", os.fspath(repository), "rev-parse", "HEAD"],
            check=True,
            stdout=__import__("subprocess").PIPE,
            stderr=__import__("subprocess").DEVNULL,
            text=True,
        ).stdout.strip()
        if current_head != args.implementation_head:
            raise TaskError("IMPLEMENTATION_HEAD_MISMATCH")
        temporary = _directory(args.temporary_root, "INVALID_TEMPORARY_ROOT")
        system_temporary = Path(tempfile.gettempdir()).resolve()
        if temporary == system_temporary or not _within(temporary, system_temporary) or any(temporary.iterdir()):
            raise TaskError("INVALID_TEMPORARY_ROOT")
        protected = _directory(args.protected_root, "INVALID_PROTECTED_ROOT")
        aio = _directory(args.aio_root, "INVALID_AIO_ROOT")
        output_parent = _directory(args.output.parent, "INVALID_EVIDENCE_OUTPUT")
        output = output_parent / args.output.name
        if output.is_symlink() or output.is_dir() or any(
            _within(output, root) or _within(root, output)
            for root in (repository, temporary, protected, aio)
        ):
            raise TaskError("EVIDENCE_OUTPUT_OVERLAP")

        before_production = gkd_bundle._snapshot_protected(protected)
        before_aio = _snapshot_tree(aio)
        tempfile.tempdir = os.fspath(temporary)
        suite = unittest.defaultTestLoader.discover(
            str(repository / "tests" / "task_core"),
            pattern="test_*.py",
            top_level_dir=str(repository),
        )
        tests = list(_flatten(suite))
        identifiers = sorted(test.id() for test in tests)
        test_ids = identifiers
        if len(identifiers) != len(set(identifiers)):
            raise TaskError("DUPLICATE_CONTRACT_ID")
        if args.canonical_results is None:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
            if not result.wasSuccessful():
                return 1
        else:
            load_canonical_results(args.canonical_results, "task-core", repository, test_ids)
        if any(temporary.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")

        after_production = gkd_bundle._snapshot_protected(protected)
        after_aio = _snapshot_tree(aio)
        if before_production != after_production or before_aio != after_aio:
            raise TaskError("PROTECTED_SURFACE_CHANGED")
        lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
        groups: dict[str, list[str]] = {}
        for identifier in identifiers:
            groups.setdefault(_group(identifier), []).append(identifier)
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M2-D",
            "outcome": "delivered_rework_core_ready",
            "bundleVersion": lock["bundleVersion"],
            "executionBundleDigest": EXECUTION_BUNDLE_DIGEST,
            "candidateOutputBundleDigest": lock["contentDigest"],
            "implementationHead": args.implementation_head,
            "bundleDigestsSeparate": lock["contentDigest"] != EXECUTION_BUNDLE_DIGEST,
            "contracts": {
                "count": len(identifiers),
                "idDigestSha256": hashlib.sha256("\n".join(identifiers).encode("utf-8")).hexdigest(),
                "groups": {
                    name: {
                        "count": len(values),
                        "idDigestSha256": hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest(),
                    }
                    for name, values in sorted(groups.items())
                },
            },
            "boundaries": {
                "trustedMainOrAcceptorOnly": True,
                "executorReworkAvailable": False,
                "candidateCodeExecuted": False,
                "oldAttemptImmutable": True,
                "freshEpochRequired": True,
                "pullRequest8Changed": False,
            },
            "protected": {
                "production": {"before": before_production, "after": after_production, "unchanged": True},
                "aio": {"before": before_aio, "after": after_aio, "unchanged": True},
            },
            "temporaryRoot": {"cleanBefore": True, "cleanAfter": True},
            "historicalLiveProbeRun": False,
            "realOneHourWaitRun": False,
            "dependenciesInstalled": False,
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        encoded = canonical_bytes(evidence)
        for forbidden in (os.fspath(repository), os.fspath(temporary), os.fspath(protected), os.fspath(aio)):
            if forbidden.encode("utf-8") in encoded:
                raise TaskError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
        atomic_write(output, encoded)
        sys.stdout.buffer.write(
            canonical_bytes(
                {
                    "outcome": evidence["outcome"],
                    "tests": evidence["contracts"]["count"],
                    "candidateOutputBundleDigest": evidence["candidateOutputBundleDigest"],
                    "evidenceDigest": evidence["evidenceDigest"],
                }
            )
        )
        return 0
    except (TaskError, CanonicalResultError) as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
