#!/usr/bin/env python3
"""Run GKD-M2-A contracts and emit deterministic fixed-bundle evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest

import gkd_bundle
from gkd_role.migration import apply_migration, verify_migration
from gkd_role.roles import context_manifest, role_catalog
from gkd_role.routing import m2a_route_evidence
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, read_canonical_json, require_keys, require_sha256, sha256_bytes
from gkd_task.errors import TaskError
from tests.role_routing.helpers import build_migration_home


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _resolve_directory(path: Path, code: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise TaskError(code)
    return path.resolve()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _snapshot_tree(root_value: Path) -> dict[str, object]:
    root = _resolve_directory(root_value, "INVALID_PROTECTED_ROOT")
    records = []
    for path in [root, *sorted(root.rglob("*"))]:
        metadata = path.lstat()
        record = {"path": "." if path == root else path.relative_to(root).as_posix(), "mode": format(stat.S_IMODE(metadata.st_mode), "04o")}
        if stat.S_ISREG(metadata.st_mode):
            record.update(type="file", sha256=sha256_bytes(path.read_bytes()))
        elif stat.S_ISDIR(metadata.st_mode):
            record["type"] = "directory"
        elif stat.S_ISLNK(metadata.st_mode):
            record.update(type="symlink", targetSha256=sha256_bytes(os.readlink(path).encode("utf-8")))
        else:
            record["type"] = "other"
        records.append(record)
    return {"digest": sha256_bytes(b"".join(canonical_bytes(item) for item in records)), "entries": len(records)}


def _validate_handshake(value: dict[str, object]) -> None:
    if value.get("outcome") == "role_handshake_ready":
        require_keys(value, {"schemaVersion", "outcome", "evidenceClass", "roleName", "effectiveModel", "effectiveReasoningEffort", "effectiveSandbox", "runtimeSeconds", "bundleDigest", "roleDigest", "configDigest", "providerDigest", "pathFree", "handshakeDigest"}, "INVALID_ROLE_HANDSHAKE")
        if value["schemaVersion"] != 1 or value["evidenceClass"] != "host-runtime-event" or value["roleName"] not in {"gkd_executor", "gkd_acceptor", "gkd_ci_reviewer"} or value["pathFree"] is not True:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        for field in ("bundleDigest", "roleDigest", "configDigest", "providerDigest", "handshakeDigest"):
            require_sha256(value[field], "INVALID_ROLE_HANDSHAKE")
    elif value.get("outcome") == "blocked":
        require_keys(value, {"schemaVersion", "outcome", "error", "hostFailure", "evidenceClass", "attempts", "codexExitCode", "eventTypes", "events", "agentIdentities", "customRoleReferenceObserved", "customRoleActivationProven", "childTerminalObserved", "parentTerminalObserved", "productionProtectedUnchanged", "historicalLiveProbeRun", "realOneHourWaitRun", "pathFree", "setupFacts", "boundDigests", "handshakeDigest"}, "INVALID_ROLE_HANDSHAKE")
        if value["schemaVersion"] != 1 or value["error"] != "TRUSTED_ROLE_HANDSHAKE_NOT_ESTABLISHED" or value["hostFailure"] != "CUSTOM_ROLE_HANDSHAKE_INCOMPLETE" or value["evidenceClass"] != "host-runtime-evidence-insufficient" or value["attempts"] != 1 or value["codexExitCode"] != 1 or value["customRoleReferenceObserved"] is not False or value["customRoleActivationProven"] is not False or value["childTerminalObserved"] is not False or value["parentTerminalObserved"] is not False or value["pathFree"] is not True or value["setupFacts"] != {"roleFilesMounted": True, "skillFilesMounted": True, "bundleBindingPrepared": True, "temporaryRepoCleaned": True, "hostRoleBindingObserved": False, "hostConfigBindingObserved": False}:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        for field in ("bundleDigest", "roleDigest", "configDigest"):
            require_sha256(value["boundDigests"][field], "INVALID_ROLE_HANDSHAKE")
        require_sha256(value["handshakeDigest"], "INVALID_ROLE_HANDSHAKE")
    else:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    unsigned = dict(value); actual = unsigned.pop("handshakeDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_ROLE_HANDSHAKE")


def _exercise_install(source: Path, temporary: Path, name: str, bundle_digest: str) -> dict[str, object]:
    install_root = temporary / f"bundle-{name}"
    target = install_root / "target"
    install_root.mkdir(); target.mkdir()
    installed = gkd_bundle.install(source, install_root, target)
    home = temporary / f"home-{name}"
    build_migration_home(home)
    migrated = apply_migration(target / "gkd", home, bundle_digest)
    verified = verify_migration(target / "gkd", home, bundle_digest)
    result = {
        "bundleVersion": installed["bundleVersion"],
        "contentDigest": installed["contentDigest"],
        "files": installed["files"],
        "planDigest": migrated["planDigest"],
        "surfaceDigest": migrated["afterDigest"],
        "inventoryDigest": migrated["inventoryDigest"],
        "roleDigests": verified["roleDigests"],
        "skillDigests": verified["skillDigests"],
    }
    shutil.rmtree(install_root)
    shutil.rmtree(home)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    parser.add_argument("--aio-root", type=Path, required=True)
    parser.add_argument("--handshake", type=Path, required=True)
    args = parser.parse_args()
    try:
        repository = Path(__file__).resolve().parents[2]
        source = repository / "canonical"
        bundle_root = source / "payload"
        temporary = _resolve_directory(args.temporary_root, "INVALID_TEMPORARY_ROOT")
        if temporary != Path(tempfile.gettempdir()).resolve() and _within(temporary, Path(tempfile.gettempdir()).resolve()) and not any(temporary.iterdir()):
            pass
        else:
            raise TaskError("INVALID_TEMPORARY_ROOT")
        protected = _resolve_directory(args.protected_root, "INVALID_PROTECTED_ROOT")
        aio = _resolve_directory(args.aio_root, "INVALID_AIO_ROOT")
        output_parent = _resolve_directory(args.output.parent, "INVALID_EVIDENCE_OUTPUT")
        output = output_parent / args.output.name
        if output.is_symlink() or output.is_dir() or any(_within(output, root) or _within(root, output) for root in (repository, temporary, protected, aio)):
            raise TaskError("EVIDENCE_OUTPUT_OVERLAP")
        handshake = read_canonical_json(args.handshake, "INVALID_ROLE_HANDSHAKE", _validate_handshake)
        before_production = gkd_bundle._snapshot_protected(protected)
        before_aio = _snapshot_tree(aio)
        suite = unittest.defaultTestLoader.discover(str(repository / "tests" / "role_routing"), pattern="test_*.py", top_level_dir=str(repository))
        tests = list(_flatten(suite))
        test_ids = sorted(test.id() for test in tests)
        if len(test_ids) != len(set(test_ids)):
            raise TaskError("DUPLICATE_CONTRACT_ID")
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        if not result.wasSuccessful():
            return 1
        lock = json.loads((source / "manifest.lock.json").read_text(encoding="utf-8"))
        bundle_digest = lock["contentDigest"]
        catalog = role_catalog(bundle_root, bundle_digest)
        if handshake["outcome"] == "role_handshake_ready":
            if handshake["bundleDigest"] != bundle_digest:
                raise TaskError("ROLE_HANDSHAKE_BUNDLE_DRIFT")
            matching = next((role for role in catalog["roles"] if role["name"] == handshake["roleName"]), None)
            if matching is None or handshake["roleDigest"] != matching["roleDigest"] or handshake["configDigest"] != matching["configDigest"] or handshake["effectiveModel"] != matching["model"] or handshake["effectiveReasoningEffort"] != matching["modelReasoningEffort"] or handshake["effectiveSandbox"] != matching["sandboxMode"] or handshake["runtimeSeconds"] != matching["runtimeSeconds"]:
                raise TaskError("ROLE_HANDSHAKE_CONFIG_DRIFT")
        first = _exercise_install(source, temporary, "a", bundle_digest)
        second = _exercise_install(source, temporary, "b", bundle_digest)
        if first != second:
            raise TaskError("M2_INSTALL_NONDETERMINISTIC")
        if any(temporary.iterdir()):
            raise TaskError("TEMPORARY_ROOT_NOT_CLEAN")
        after_production = gkd_bundle._snapshot_protected(protected)
        after_aio = _snapshot_tree(aio)
        if before_production != after_production or before_aio != after_aio:
            raise TaskError("PROTECTED_SURFACE_CHANGED")
        contexts = {role["name"]: context_manifest(bundle_root, bundle_digest, role["name"])["contextDigest"] for role in catalog["roles"]}
        evidence = {
            "schemaVersion": 1,
            "task": "GKD-M2-A",
            "outcome": "role_routing_core_ready" if handshake["outcome"] == "role_handshake_ready" else "blocked",
            "error": None if handshake["outcome"] == "role_handshake_ready" else handshake["error"],
            "bundleVersion": lock["bundleVersion"],
            "contentDigest": bundle_digest,
            "activationProvider": {"name": catalog["activationProvider"]["name"], "digest": catalog["activationProviderDigest"], "trustedHostRequired": True, "cliFailClosed": True, "candidateWriterPresent": False, "testHostSeamInBundle": False, "trustedBoundaryAvailable": False, "candidateClaimFailClosed": True, "planDelta": "candidate-inaccessible-host-attestation-required"},
            "roleSourceDigest": catalog["roleSourceDigest"],
            "hardRulesDigest": catalog["hardRulesDigest"],
            "roles": {role["name"]: {"roleDigest": role["roleDigest"], "configDigest": role["configDigest"]} for role in catalog["roles"]},
            "skills": catalog["skillDigests"],
            "contexts": contexts,
            "route": m2a_route_evidence(bundle_digest),
            "waitContract": {"timeoutMs": 3600000, "maxIntervals": 12, "realOneHourRun": False, "externalWatcherUsed": False},
            "tests": {"count": len(test_ids), "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest()},
            "installation": first,
            "handshake": handshake,
            "protected": {"production": {"before": before_production, "after": after_production, "unchanged": True}, "aio": {"before": before_aio, "after": after_aio, "unchanged": True}},
            "temporaryRoot": {"cleanBefore": True, "cleanAfter": True},
            "historicalLiveProbeRun": False,
            "dependenciesInstalled": False,
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        encoded = canonical_bytes(evidence)
        for forbidden in (os.fspath(repository), os.fspath(temporary), os.fspath(protected), os.fspath(aio)):
            if forbidden.encode("utf-8") in encoded:
                raise TaskError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
        atomic_write(output, encoded)
        sys.stdout.buffer.write(canonical_bytes({"outcome": evidence["outcome"], "tests": evidence["tests"]["count"], "contentDigest": bundle_digest, "evidenceDigest": evidence["evidenceDigest"]}))
        return 0
    except TaskError as error:
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": error.code}))
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        sys.stderr.buffer.write(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
