#!/usr/bin/env python3
"""Run canonical foundation contracts and write deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

from gkd_task.results import CanonicalResultError, canonical_bytes, select_canonical_results
from tests.contract_catalog import FOUNDATION_CONTRACT_TEST_IDS, validate_contract_coverage


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.success_ids: set[str] = set()

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self.success_ids.add(test.id())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(
        "tests/foundation", pattern="test_*.py", top_level_dir="."
    )
    runner = unittest.TextTestRunner(
        verbosity=2, resultclass=RecordingResult, warnings="error"
    )
    tests = list(_flatten(suite))
    discovered_ids = [test.id() for test in tests]
    canonical_selection = None
    if args.canonical_results is None:
        result = runner.run(suite)
        if not result.wasSuccessful():
            return 1
        success_ids = result.success_ids
    else:
        try:
            canonical_selection = select_canonical_results(
                args.canonical_results,
                "foundation",
                repository,
                discovered_ids,
                discovered_ids,
            )
        except CanonicalResultError as error:
            sys.stderr.buffer.write(canonical_bytes({"error": error.code, "status": "error"}))
            return 2
        success_ids = {item["id"] for item in canonical_selection["tests"]}
    validate_contract_coverage(FOUNDATION_CONTRACT_TEST_IDS, success_ids)
    test_ids = sorted(success_ids)
    evidence = {
        "schemaVersion": 1,
        "task": "GKD-M0-A",
        "outcome": "pass",
        "tests": {
            "count": len(test_ids),
            "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
        },
        "contracts": {
            contract: {
                "status": "pass",
                "tests": list(contract_test_ids),
                "result": {
                    "headSha": canonical_selection["headSha"] if canonical_selection is not None else None,
                    "resultDigest": canonical_selection["resultDigest"] if canonical_selection is not None else None,
                    "scope": "foundation",
                },
            }
            for contract, contract_test_ids in FOUNDATION_CONTRACT_TEST_IDS.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": "pass", "tests": len(test_ids)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
