#!/usr/bin/env python3
"""Run deterministic task-core contracts and emit canonical evidence."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

import gkd_bundle
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, sha256_bytes
from gkd_task.errors import TaskError
from gkd_task.results import CanonicalResultError, load_canonical_results


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _contract_id(test: unittest.TestCase) -> str:
    value = test.id().removeprefix("tests.task_core.")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return f"M1-{normalized}"


def _group(test: unittest.TestCase) -> str:
    identifier = test.id()
    method = identifier.rsplit(".", 1)[-1]
    if "test_mutations" in identifier:
        return "mutation"
    if "test_acceptance" in identifier:
        return "l2-fixed-head-acceptance"
    if "test_bootstrap_and_packaging" in identifier:
        return "l2-bootstrap-packaging"
    if "test_runtime_and_migration" in identifier:
        return "l2-locator-migration" if "LocatorAndMigration" in identifier else "l1-transaction-recovery"
    if "concurrent_subprocess" in method:
        return "l2-concurrent-claim"
    if "test_lifecycle" in identifier:
        return "l1-offer-claim-lifecycle"
    return "l1-planning-schema"


def _resolve_directory(path: Path, code: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise TaskError(code)
    return path.resolve()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()
    try:
        repository_root = Path(__file__).resolve().parents[2]
        temporary_root = _resolve_directory(args.temporary_root, "INVALID_TEMPORARY_ROOT")
        protected_root = _resolve_directory(args.protected_root, "INVALID_PROTECTED_ROOT")
        system_temporary = Path(tempfile.gettempdir()).resolve()
        if temporary_root == system_temporary or not _is_within(temporary_root, system_temporary) or any(temporary_root.iterdir()):
            raise TaskError("INVALID_TEMPORARY_ROOT")
        output_parent = _resolve_directory(args.output.parent, "INVALID_EVIDENCE_OUTPUT")
        output = output_parent / args.output.name
        if output.is_symlink() or output.is_dir() or any(
            _is_within(output, root) or _is_within(root, output)
            for root in (repository_root, temporary_root, protected_root)
        ):
            raise TaskError("EVIDENCE_OUTPUT_OVERLAP")
        tempfile.tempdir = str(temporary_root)
        before = gkd_bundle._snapshot_protected(protected_root)
        suite = unittest.defaultTestLoader.discover(
            str(repository_root / "tests" / "task_core"),
            pattern="test_*.py",
            top_level_dir=str(repository_root),
        )
        tests = list(_flatten(suite))
        identifiers = [_contract_id(test) for test in tests]
        if len(identifiers) != len(set(identifiers)):
            raise TaskError("DUPLICATE_CONTRACT_ID")
        raw_test_ids = [test.id() for test in tests]
        groups: dict[str, list[str]] = {}
        if len(tests) != len(identifiers):
            raise TaskError("CONTRACT_TEST_COUNT_MISMATCH")
        for test, identifier in zip(tests, identifiers):
            groups.setdefault(_group(test), []).append(identifier)
        if args.canonical_results is None:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
            if not result.wasSuccessful():
                return 1
        else:
            load_canonical_results(args.canonical_results, "task-core", repository_root, raw_test_ids)
        if any(temporary_root.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")
        after = gkd_bundle._snapshot_protected(protected_root)
        if before != after:
            raise TaskError("PROTECTED_HOME_CHANGED")
        lock = json.loads((repository_root / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M1-A",
            "outcome": "deterministic_task_core_ready",
            "bundleVersion": lock["bundleVersion"],
            "contentDigest": lock["contentDigest"],
            "tests": len(tests),
            "contractIds": sorted(identifiers),
            "contractIdsDigest": sha256_bytes(b"".join(canonical_bytes(value) for value in sorted(identifiers))),
            "contractGroups": {name: sorted(values) for name, values in sorted(groups.items())},
            "protectedHome": {
                "beforeDigest": before["digest"],
                "afterDigest": after["digest"],
                "entries": before["entries"],
                "unchanged": True,
            },
            "temporaryRoot": {"cleanBefore": True, "cleanAfter": True},
            "liveProbeRun": False,
            "dependenciesInstalled": False,
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        encoded = canonical_bytes(evidence)
        for forbidden in (str(repository_root), str(temporary_root), str(protected_root)):
            if forbidden.encode("utf-8") in encoded:
                raise TaskError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
        atomic_write(output, encoded)
        sys.stdout.buffer.write(
            canonical_bytes(
                {
                    "outcome": evidence["outcome"],
                    "tests": evidence["tests"],
                    "contentDigest": evidence["contentDigest"],
                    "evidenceDigest": evidence["evidenceDigest"],
                }
            )
        )
        return 0
    except (TaskError, CanonicalResultError) as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
