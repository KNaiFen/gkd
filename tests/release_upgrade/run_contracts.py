#!/usr/bin/env python3
"""Consume release-upgrade results and emit deterministic compatibility evidence."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "canonical" / "payload" / "lib"
sys.dont_write_bytecode = True
for _path in (LIBRARY, ROOT):
    sys.path.insert(0, str(_path))

from gkd_task.results import (
    CanonicalResultError,
    RELEASE_UPGRADE_LANE,
    RELEASE_UPGRADE_PROFILE,
    canonical_bytes,
    digest_object,
    load_canonical_results,
)
from tests.legacy_format_catalog import load_catalog, validate_catalog


CORE_SCOPE_PATHS = (
    "tests/release_candidate",
    "tests/finalization",
    "tests/ci_policy",
    "tests/task_core",
    "tests/role_routing",
    "tests/runtime_bridge",
    "tests/production_migration",
    "tests/foundation",
)


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _discover(relative_paths: tuple[str, ...]) -> set[str]:
    result: set[str] = set()
    for relative in relative_paths:
        suite = unittest.defaultTestLoader.discover(
            str(ROOT / relative),
            pattern="test_*.py",
            top_level_dir=str(ROOT),
        )
        result.update(test.id() for test in _flatten(suite))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()
    try:
        matrix_ids = sorted(_discover(("tests/release_upgrade",)))
        validate_catalog(load_catalog(), _discover(CORE_SCOPE_PATHS), set(matrix_ids))
        if args.canonical_results is None:
            suite = unittest.defaultTestLoader.discover(
                str(ROOT / "tests" / "release_upgrade"),
                pattern="test_*.py",
                top_level_dir=str(ROOT),
            )
            result = unittest.TextTestRunner(stream=None, verbosity=0, warnings="error").run(suite)
            if not result.wasSuccessful():
                return 1
            result_digest = None
            head_sha = None
            base_sha = None
            environment = None
        else:
            selected = load_canonical_results(
                args.canonical_results,
                "release-upgrade",
                ROOT,
                matrix_ids,
            )
            result_digest = selected["resultDigest"]
            head_sha = selected["headSha"]
            base_sha = selected["baseSha"]
            environment = selected["environment"]
        evidence = {
            "schemaVersion": 1,
            "lane": RELEASE_UPGRADE_LANE,
            "profile": RELEASE_UPGRADE_PROFILE,
            "outcome": "pass",
            "catalogDigest": digest_object(load_catalog()),
            "contracts": {
                "count": len(matrix_ids),
                "idDigestSha256": hashlib.sha256("\n".join(matrix_ids).encode("utf-8")).hexdigest(),
            },
            "canonicalResult": {
                "baseSha": base_sha,
                "headSha": head_sha,
                "environment": environment,
                "resultDigest": result_digest,
            },
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(canonical_bytes(evidence))
        print(
            canonical_bytes(
                {
                    "outcome": evidence["outcome"],
                    "evidenceDigest": evidence["evidenceDigest"],
                    "tests": len(matrix_ids),
                }
            ).decode(),
            end="",
        )
        return 0
    except (CanonicalResultError, ValueError) as error:
        print(canonical_bytes({"error": str(error), "status": "error"}).decode(), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
