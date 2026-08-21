#!/usr/bin/env python3
"""Run M3-B contracts and emit deterministic, path-free evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

import gkd_bundle
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.success_ids: set[str] = set()

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self.success_ids.add(test.id())


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(
        str(repository / "tests" / "resource_scanner"),
        pattern="test_*.py",
        top_level_dir=str(repository),
    )
    tests = list(_flatten(suite))
    test_ids = sorted(test.id() for test in tests)
    if len(test_ids) != len(set(test_ids)):
        print(canonical_bytes({"error": "DUPLICATE_CONTRACT_ID", "status": "error"}).decode(), file=sys.stderr, end="")
        return 2
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=RecordingResult, warnings="error").run(suite)
    if not result.wasSuccessful():
        return 1
    lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
    groups: dict[str, list[str]] = {}
    for identifier in test_ids:
        group = "mutation" if ".test_mutations." in identifier else "resource-and-recommendation" if ".test_resources." in identifier else "scanner-boundary"
        groups.setdefault(group, []).append(identifier)
    evidence = {
        "schemaVersion": 1,
        "task": "GKD-M3-B",
        "outcome": "resource_scanner_ready",
        "bundleVersion": lock["bundleVersion"],
        "candidateOutputBundleDigest": lock["contentDigest"],
        "contracts": {
            "count": len(test_ids),
            "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
            "groups": {name: values for name, values in sorted(groups.items())},
        },
        "resource": {
            "artifactClasses": ["zero", "bounded", "build-or-unknown"],
            "presets": ["resource-constrained", "standard", "high-capacity"],
            "unknownAndPeakViolationsFailClosed": True,
        },
        "recommendations": {
            "goals": ["speed-first", "balanced", "cost-aware"],
            "priceClaimsRequireVerification": True,
            "factsSourceBound": True,
        },
        "scanner": {
            "surfaces": ["diff", "pull-request", "artifact"],
            "boundedInputs": True,
            "redactedOutput": True,
            "credentialExposureTerminal": True,
        },
        "dependenciesInstalled": False,
        "machinePathsRetained": False,
    }
    evidence["evidenceDigest"] = digest_object(evidence)
    atomic_write(args.output, canonical_bytes(evidence))
    print(canonical_bytes({"candidateOutputBundleDigest": lock["contentDigest"], "evidenceDigest": evidence["evidenceDigest"], "outcome": evidence["outcome"], "tests": len(test_ids)}).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
