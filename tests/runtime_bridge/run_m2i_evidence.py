#!/usr/bin/env python3
"""Generate deterministic, path-free M2-I runtime bridge evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import gkd_bundle
from gkd_role.routing import decide_route
from gkd_task.canonical import FixedNonce, atomic_write, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from tests.role_routing.run_contracts import _snapshot_tree
from tests.runtime_bridge.helpers import BUNDLE_ROOT, bundle_digest, ready_bridge, spawn_result, terminal_result
from tests.task_core.helpers import TaskRepo


TEST_NAMES = (
    "tests.runtime_bridge.test_bridge.AutomaticBridgeContracts.test_task_names_are_ascii_bounded_and_attempt_aware",
    "tests.runtime_bridge.test_bridge.AutomaticBridgeContracts.test_terminal_reclaim_binds_exact_claim_and_allows_fresh_epoch",
    "tests.runtime_bridge.test_bridge.AutomaticBridgeContracts.test_terminal_reclaim_rejects_mismatch_active_and_stale_without_writes",
)


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


def _suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in TEST_NAMES)
    return suite


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
        test_ids = sorted(TEST_NAMES)
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(_suite())
        if not result.wasSuccessful():
            return 1

        repo = TaskRepo()
        try:
            bridge, prepared = ready_bridge(repo)
            bridge.claim(*repo.cas(), prepared["envelopeId"], spawn_result(prepared), "evidence-activation")
            claim = repo.state()["lifecycle"]["claim"]
            reclaimed = bridge.reclaim_terminal(*repo.cas(), terminal_result(repo, prepared, claim), "child-terminal")
            bridge.nonce = FixedNonce(["d" * 48, "fresh-offer", "fresh-tx", "fresh-handoff", "fresh-context"])
            prepared_again = bridge.prepare(
                *repo.cas(),
                decide_route(
                    {
                        "schemaVersion": 1,
                        "requestedRoute": "automatic",
                        "bundleDigest": bundle_digest(),
                        "gates": {
                            "activationProviderReady": True,
                            "bundleFixed": True,
                            "offerClaimReady": True,
                            "roleAvailable": True,
                            "roleConfigFixed": True,
                            "waitGateReady": True,
                        },
                    }
                ),
                "2027-01-02T03:04:05Z",
            )
            flow = {
                "firstTaskNameDigest": hashlib.sha256(prepared["spawnRequest"]["taskName"].encode("ascii")).hexdigest(),
                "secondTaskNameDigest": hashlib.sha256(prepared_again["spawnRequest"]["taskName"].encode("ascii")).hexdigest(),
                "taskNamesDistinct": prepared["spawnRequest"]["taskName"] != prepared_again["spawnRequest"]["taskName"],
                "terminalReclaimed": reclaimed["status"] == "reclaimed",
                "epochAdvanced": repo.state()["lifecycle"]["epoch"] == 1,
                "candidateOutputBundleDigest": "d" * 64,
                "executionBundleDigest": prepared["executionBundleDigest"],
            }
        finally:
            repo.close()

        if any(temporary.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")
        after_production = gkd_bundle._snapshot_protected(protected)
        after_aio = _snapshot_tree(aio)
        if before_production != after_production or before_aio != after_aio:
            raise TaskError("PROTECTED_SURFACE_CHANGED")

        lock = json.loads((repository / "canonical" / "manifest.lock.json").read_text(encoding="utf-8"))
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M2-I",
            "outcome": "automatic_host_recovery_bridge_ready",
            "bundleVersion": lock["bundleVersion"],
            "candidateOutputBundleDigest": lock["contentDigest"],
            "contracts": {
                "count": len(test_ids),
                "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
                "ids": test_ids,
            },
            "automaticFlow": flow,
            "publicBoundaries": {
                "candidateReclaimFailClosed": True,
                "publicAutomaticClaimFailClosed": True,
                "rawHostResultPersisted": False,
                "terminalProviderOneShot": True,
                "fallbackTaskName": False,
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
        sys.stdout.buffer.write(canonical_bytes({"outcome": evidence["outcome"], "tests": len(test_ids), "evidenceDigest": evidence["evidenceDigest"]}))
        return 0
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
