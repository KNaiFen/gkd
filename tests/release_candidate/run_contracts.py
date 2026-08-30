"""Run deterministic M5 contracts and emit redacted release-candidate evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import unittest

from gkd_release.core import build_release_candidate
from gkd_release.verification import build_l3_trusted_main_record, run_l1_properties, validate_l3_trusted_main_record
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object
from gkd_task.results import CanonicalResultError, load_canonical_results


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _group(identifier: str) -> str:
    if ".test_trusted_main_final_gate_" in identifier or ".test_post_merge_records_" in identifier:
        return "post-merge-final-gate-fake-github"
    if ".test_l1_" in identifier:
        return "l1-property"
    if ".test_l2_" in identifier:
        return "l2-subprocess-fake-github"
    if ".test_l3_" in identifier:
        return "l3-trusted-main-evaluation"
    if ".test_l4_" in identifier:
        return "l4-sandbox-canary"
    if "mutation" in identifier:
        return "mutation"
    return "l0-traceability-release-record"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(
        str(repository / "tests" / "release_candidate"),
        pattern="test_*.py",
        top_level_dir=str(repository),
    )
    tests = list(_flatten(suite))
    test_ids = sorted(test.id() for test in tests)
    if len(test_ids) != len(set(test_ids)):
        return 2
    if args.canonical_results is None:
        result = unittest.TextTestRunner(stream=None, verbosity=0, warnings="error").run(suite)
        if not result.wasSuccessful():
            return 1
    else:
        try:
            load_canonical_results(args.canonical_results, "m5-release-candidate", repository, test_ids)
        except CanonicalResultError as error:
            print(canonical_bytes({"error": error.code, "status": "error"}).decode(), end="")
            return 2
    traceability = json.loads(
        (repository / "canonical/inputs/release/traceability.json").read_text(encoding="utf-8")
    )
    release_candidate = build_release_candidate(
        {
            "version": "0.1.5",
            "sourceSha": "a" * 40,
            "bundleDigest": "b" * 64,
            "evidenceDigest": "c" * 64,
            "traceability": traceability,
            "layers": ["L0", "L1", "L2", "L3", "L4"],
            "sandboxRepository": "github.com/KNaiFen/gkd-sandbox",
        }
    )
    l3_record = build_l3_trusted_main_record(release_candidate)
    lock = json.loads((repository / "canonical/manifest.lock.json").read_text(encoding="utf-8"))
    groups: dict[str, list[str]] = {}
    for identifier in test_ids:
        groups.setdefault(_group(identifier), []).append(identifier)
    evidence = {
        "bundleVersion": lock["bundleVersion"],
        "candidateOutputBundleDigest": lock["contentDigest"],
        "contracts": {
            "count": len(test_ids),
            "groups": {name: values for name, values in sorted(groups.items())},
            "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
        },
        "dependenciesInstalled": False,
        "layers": {
            "L0": "pass",
            "L1": run_l1_properties(traceability),
            "L2": {"fakeGitHubSubprocess": True, "status": "pass"},
            "L3": {
                "trustedMainObserved": True,
                "postMergeRecordContract": True,
                "status": "pass",
                "evaluationDigest": validate_l3_trusted_main_record(
                    l3_record, release_candidate
                )["evaluationDigest"],
            },
            "L4": {
                "canonicalMarkerContract": True,
                "liveCanaryRun": False,
                "observedCheckContract": True,
                "sandboxOnly": True,
                "status": "pass",
            },
        },
        "machinePathsRetained": False,
        "outcome": "release_candidate_verification_ready",
        "schemaVersion": 1,
        "task": "GKD-R10",
        "traceabilityDigest": digest_object(traceability),
    }
    evidence["evidenceDigest"] = digest_object(evidence)
    atomic_write(args.output, canonical_bytes(evidence))
    print(canonical_bytes({"candidateOutputBundleDigest": lock["contentDigest"], "evidenceDigest": evidence["evidenceDigest"], "outcome": evidence["outcome"], "tests": len(test_ids)}).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
