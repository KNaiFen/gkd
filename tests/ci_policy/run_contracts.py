#!/usr/bin/env python3
"""Run M3-A contracts and emit path-minimized deterministic evidence."""

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
from tests.role_routing.run_contracts import _snapshot_tree


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


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _group(identifier: str) -> str:
    if ".test_mutations." in identifier:
        return "mutation"
    if ".test_cli_and_repository." in identifier:
        return "l2-subprocess-repository"
    if ".test_github." in identifier:
        return "l2-github-boundary"
    if ".test_monitor." in identifier:
        return "l1-fixed-head-monitor"
    return "l1-policy-origin"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--aio-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        repository = Path(__file__).resolve().parents[2]
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
            str(repository / "tests" / "ci_policy"),
            pattern="test_*.py",
            top_level_dir=str(repository),
        )
        tests = list(_flatten(suite))
        test_ids = sorted(test.id() for test in tests)
        if len(test_ids) != len(set(test_ids)):
            raise TaskError("DUPLICATE_CONTRACT_ID")
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, warnings="error").run(suite)
        if not result.wasSuccessful():
            return 1
        if any(temporary.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")
        after_production = gkd_bundle._snapshot_protected(protected)
        after_aio = _snapshot_tree(aio)
        if before_production != after_production or before_aio != after_aio:
            raise TaskError("PROTECTED_SURFACE_CHANGED")
        lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
        groups: dict[str, list[str]] = {}
        for identifier in test_ids:
            groups.setdefault(_group(identifier), []).append(identifier)
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M3-A",
            "outcome": "fixed_head_ci_policy_ready",
            "bundleVersion": lock["bundleVersion"],
            "candidateOutputBundleDigest": lock["contentDigest"],
            "contracts": {
                "count": len(test_ids),
                "groups": {name: values for name, values in sorted(groups.items())},
                "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
            },
            "policy": {
                "path": ".gkd/policy.json",
                "provider": "github",
                "strictCanonical": True,
                "originBound": True,
            },
            "monitor": {
                "fixedHeadBound": True,
                "ownsPolling": True,
                "readOnly": True,
                "singleTerminal": True,
            },
            "protected": {
                "aio": {"after": after_aio, "before": before_aio, "unchanged": True},
                "production": {"after": after_production, "before": before_production, "unchanged": True},
            },
            "temporaryRoot": {"cleanAfter": True, "cleanBefore": True},
            "dependenciesInstalled": False,
            "historicalLiveProbeRun": False,
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
                    "candidateOutputBundleDigest": evidence["candidateOutputBundleDigest"],
                    "evidenceDigest": evidence["evidenceDigest"],
                    "outcome": evidence["outcome"],
                    "tests": evidence["contracts"]["count"],
                }
            )
        )
        return 0
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"error": error.code, "status": "error"}))
        return 2
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError):
        sys.stderr.buffer.write(canonical_bytes({"error": "FILESYSTEM_ERROR", "status": "error"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
