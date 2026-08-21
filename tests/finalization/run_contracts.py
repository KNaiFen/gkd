"""Run M4 finalization contracts and emit deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import unittest

from gkd_task.canonical import atomic_write, canonical_bytes, digest_object


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(str(repository / "tests" / "finalization"), pattern="test_*.py", top_level_dir=str(repository))
    tests = list(_flatten(suite))
    test_ids = sorted(test.id() for test in tests)
    if len(test_ids) != len(set(test_ids)):
        return 2
    result = unittest.TextTestRunner(stream=None, verbosity=0, warnings="error").run(suite)
    if not result.wasSuccessful():
        return 1
    lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
    evidence = {
        "schemaVersion": 1,
        "task": "GKD-M4-A",
        "outcome": "finalization_release_mechanism_ready",
        "bundleVersion": lock["bundleVersion"],
        "candidateOutputBundleDigest": lock["contentDigest"],
        "contracts": {
            "count": len(test_ids),
            "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
            "groups": {
                "fixed-head-acceptance": [item for item in test_ids if ".test_acceptance." in item],
                "finalization": [item for item in test_ids if ".test_finalization." in item],
                "mutation": [item for item in test_ids if ".test_mutations." in item],
            },
        },
        "finalization": {
            "maximumPullRequests": 2,
            "closeoutOnlyBlocksProductLogicAndReleaseSideEffects": True,
            "releaseRequiresBoundAdapterAndAuthorization": True,
            "sourceCandidateMainTagAssetsAndProvenanceUseOneSha": True,
            "promotionRetryDoesNotCreateAnotherRelease": True,
        },
        "acceptance": {"candidateCodeExecuted": False, "synchronizedMainRevalidated": True},
        "dependenciesInstalled": False,
        "machinePathsRetained": False,
    }
    evidence["evidenceDigest"] = digest_object(evidence)
    atomic_write(args.output, canonical_bytes(evidence))
    print(canonical_bytes({"candidateOutputBundleDigest": lock["contentDigest"], "evidenceDigest": evidence["evidenceDigest"], "outcome": evidence["outcome"], "tests": len(test_ids)}).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
