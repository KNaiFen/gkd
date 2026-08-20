#!/usr/bin/env python3
"""Run focused M2-J contracts and emit deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import gkd_bundle
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object
from gkd_task.errors import TaskError


EXECUTION_BUNDLE_DIGEST = "71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766"
CONTRACTS = (
    "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_requires_precommitted_canonical_document_binding",
    "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_document_commit_with_extra_tracked_path",
    "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_path_traversal_before_any_write",
    "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_duplicate_document_on_fresh_attempt",
    "tests.task_core.test_acceptance.AcceptanceContracts.test_exact_head_acceptance_performs_two_reads_and_one_merge",
    "tests.task_core.test_acceptance.AcceptanceContracts.test_legacy_delivery_without_document_binding_is_readable_but_not_acceptable",
    "tests.task_core.test_acceptance.AcceptanceContracts.test_post_delivery_document_commit_is_not_a_fixed_candidate",
    "tests.task_core.test_mutations.MutationContracts.test_mutation_delivery_document_digest_check_is_killed",
    "tests.task_core.test_mutations.MutationContracts.test_mutation_delivery_document_commit_paths_check_is_killed",
)


def _directory(path: Path, code: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise TaskError(code)
    return path.resolve()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--implementation-head", required=True)
    args = parser.parse_args()
    try:
        repository = Path(__file__).resolve().parents[2]
        if len(args.implementation_head) != 40 or any(character not in "0123456789abcdef" for character in args.implementation_head):
            raise TaskError("INVALID_IMPLEMENTATION_HEAD")
        actual_head = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        ).stdout.strip()
        if actual_head != args.implementation_head:
            raise TaskError("IMPLEMENTATION_HEAD_MISMATCH")
        temporary = _directory(args.temporary_root, "INVALID_TEMPORARY_ROOT")
        if temporary == Path(tempfile.gettempdir()).resolve() or any(temporary.iterdir()):
            raise TaskError("INVALID_TEMPORARY_ROOT")
        protected = _directory(args.protected_root, "INVALID_PROTECTED_ROOT")
        output_parent = _directory(args.output.parent, "INVALID_EVIDENCE_OUTPUT")
        output = output_parent / args.output.name
        if output.is_symlink() or output.is_dir() or any(
            _inside(output, root) or _inside(root, output)
            for root in (repository, temporary, protected)
        ):
            raise TaskError("EVIDENCE_OUTPUT_OVERLAP")

        before = gkd_bundle._snapshot_protected(protected)
        tempfile.tempdir = str(temporary)
        suite = unittest.TestSuite(
            unittest.defaultTestLoader.loadTestsFromName(identifier)
            for identifier in CONTRACTS
        )
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        if not result.wasSuccessful():
            return 1
        if any(temporary.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")
        after = gkd_bundle._snapshot_protected(protected)
        if before != after:
            raise TaskError("PROTECTED_SURFACE_CHANGED")
        lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M2-J",
            "outcome": "delivery_document_contract_ready",
            "bundleVersion": lock["bundleVersion"],
            "executionBundleDigest": EXECUTION_BUNDLE_DIGEST,
            "candidateOutputBundleDigest": lock["contentDigest"],
            "implementationHead": args.implementation_head,
            "bundleDigestsSeparate": EXECUTION_BUNDLE_DIGEST != lock["contentDigest"],
            "contracts": {
                "count": len(CONTRACTS),
                "idDigestSha256": hashlib.sha256("\n".join(CONTRACTS).encode("utf-8")).hexdigest(),
                "ids": list(CONTRACTS),
            },
            "sequence": {
                "documentBeforeDeliveryState": True,
                "finalStateCommitOnlyPostDocumentCommit": True,
                "legacyDeliveryReadableButNotAccepted": True,
                "candidateAcceptanceTrustedOnly": True,
            },
            "protected": {"before": before, "after": after, "unchanged": True},
            "temporaryRoot": {"cleanBefore": True, "cleanAfter": True},
            "dependenciesInstalled": False,
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        encoded = canonical_bytes(evidence)
        for forbidden in (str(repository), str(temporary), str(protected)):
            if forbidden.encode("utf-8") in encoded:
                raise TaskError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
        atomic_write(output, encoded)
        sys.stdout.buffer.write(canonical_bytes({"status": "pass", "task": evidence["task"], "contracts": len(CONTRACTS), "evidenceDigest": evidence["evidenceDigest"]}))
        return 0
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
