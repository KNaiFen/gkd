#!/usr/bin/env python3
"""Run M2-K host-acknowledgement bridge contracts and emit canonical evidence."""

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
from gkd_role.project import remove_project, stage_project
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.results import CanonicalResultError, load_canonical_results
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService
from tests.role_routing.run_contracts import _snapshot_tree
from tests.runtime_bridge.helpers import BUNDLE_ROOT, bundle_digest, init_repo, ready_bridge, spawn_result
from tests.task_core.helpers import TaskRepo


LEGACY_BRIDGE_CONTRACT = "host-runtime-event-v1"
HOST_ACKNOWLEDGEMENT_CONTRACT = "host-spawn-acknowledgement-v1"
SYNTHETIC_OUTPUT_BUNDLE_DIGEST = "d" * 64


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
    if ".test_mutations." in identifier:
        return "mutation"
    if ".test_project." in identifier:
        return "project-staging"
    if "interruption" in identifier:
        return "recovery"
    return "automatic-bridge"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--aio-root", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
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
            str(repository / "tests" / "runtime_bridge"),
            pattern="test_*.py",
            top_level_dir=str(repository),
        )
        tests = list(_flatten(suite))
        test_ids = sorted(test.id() for test in tests)
        if len(test_ids) != len(set(test_ids)):
            raise TaskError("DUPLICATE_CONTRACT_ID")
        if args.canonical_results is None:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
            if not result.wasSuccessful():
                return 1
        else:
            load_canonical_results(args.canonical_results, "runtime-bridge", repository, test_ids)

        first_project = temporary / "evidence-project-a"
        second_project = temporary / "evidence-project-b"
        init_repo(first_project)
        init_repo(second_project)
        first = stage_project(BUNDLE_ROOT, bundle_digest(), first_project, protected)
        second = stage_project(BUNDLE_ROOT, bundle_digest(), second_project, protected)
        if first != second or (first_project / ".gkd/runtime-project.json").read_bytes() != (second_project / ".gkd/runtime-project.json").read_bytes():
            raise TaskError("PROJECT_STAGE_NONDETERMINISTIC")
        remove_project(first_project, protected)
        remove_project(second_project, protected)
        shutil.rmtree(first_project)
        shutil.rmtree(second_project)

        repo = TaskRepo()
        try:
            bridge, prepared = ready_bridge(repo)
            claimed = bridge.claim(*repo.cas(), prepared["envelopeId"], spawn_result(prepared), "evidence-activation")
            service = TaskService(repo.candidate, repo.task_path, RuntimeStore(repo.runtime_root))
            document_path, document_digest = repo.prepare_delivery_document()
            service.deliver(
                *repo.cas(),
                claimed["claimId"],
                SYNTHETIC_OUTPUT_BUNDLE_DIGEST,
                document_path,
                document_digest,
            )
            delivery = repo.state()["lifecycle"]["delivery"]
            flow = {
                "routeDecisionDigest": prepared["routeDecisionDigest"],
                "hostContract": prepared["hostContract"],
                "offerBound": True,
                "handoffBound": True,
                "activationBound": True,
                "claimBound": True,
                "deliveryBound": True,
                "executorAttemptHandleBound": True,
                "automaticTerminalReclaimAvailable": False,
                "executionBundleDigest": delivery["executionBundleDigest"],
                "candidateOutputBundleDigest": delivery["candidateOutputBundleDigest"],
                "executionIdentityPreserved": delivery["executionBundleDigest"] == prepared["executionBundleDigest"],
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
        groups: dict[str, list[str]] = {}
        for identifier in test_ids:
            groups.setdefault(_group(identifier), []).append(identifier)
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M2-K",
            "outcome": "host_acknowledgement_bridge_ready",
            "bundleVersion": lock["bundleVersion"],
            "legacyBridgeContract": LEGACY_BRIDGE_CONTRACT,
            "hostAcknowledgementContract": HOST_ACKNOWLEDGEMENT_CONTRACT,
            "candidateOutputBundleDigest": lock["contentDigest"],
            "contracts": {
                "count": len(test_ids),
                "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
                "groups": {name: values for name, values in sorted(groups.items())},
            },
            "projectStaging": {
                **{key: first[key] for key in ("executionBundleDigest", "roleName", "roleDigest", "configDigest", "projectConfigDigest", "skillDigests", "inventoryDigest")},
                "byteIdenticalAcrossRoots": True,
                "candidateContamination": False,
                "productionTarget": False,
            },
            "automaticFlow": flow,
            "publicBoundaries": {
                "candidateTaskClaimFailClosed": True,
                "publicRoleAutomaticClaimFailClosed": True,
                "candidateActivationWriterAvailable": False,
                "genericWorkerFallback": False,
                "mainOutputPathMinimized": True,
                "runtimeIdentityCommittedAsEvidence": False,
                "hostEffectiveRuntimeClaimed": False,
                "unboundTerminalReclaim": False,
                "activationTransactionSingleWriter": True,
                "schemaV3FixedHeadAcceptanceBound": True,
                "defaultPythonBytecodeFree": True,
                "sourceDeclarationSymlinkRejected": True,
                "projectRemovalRetryable": True,
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
