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


ACCEPTED_M2_BUNDLE_DIGEST = "5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880"
ACCEPTED_M2_HANDSHAKE_DIGEST = "e2f69c4b5c7a0e3945fbd06f432defbe65e703174ebb28833a9a510276fb6940"


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
    common = {"schemaVersion", "outcome", "evidenceClass", "attempts", "pathFree", "realOneHourWaitRun", "requestedRole", "parentConfigurationSource", "parentModelOverride", "parentReasoningEffortOverride", "parentStrictConfig", "boundDigests", "setupFacts", "preflightDigest", "handshakeDigest"}
    outcome = value.get("outcome")
    if outcome == "ready_for_live_diagnosis":
        require_keys(value, common | {"error", "modelInvocations", "liveAttemptsConsumed", "historicalNegativeEvidence", "historicalCompatibilityEvidence"}, "INVALID_ROLE_HANDSHAKE")
        if value["schemaVersion"] != 2 or value["error"] != "LIVE_DIAGNOSIS_PENDING" or value["evidenceClass"] != "deterministic-production-environment-preflight" or value["attempts"] != 0 or value["modelInvocations"] != 0 or value["liveAttemptsConsumed"] != 0:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        history = value["historicalNegativeEvidence"]
        require_keys(history, {"hostFailure", "evidenceClass", "codexExitCode", "hostError", "handshakeDigest"}, "INVALID_ROLE_HANDSHAKE")
        require_keys(history["hostError"], {"code", "httpStatus", "message"}, "INVALID_ROLE_HANDSHAKE")
        if history["hostFailure"] != "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT" or history["evidenceClass"] != "host-runtime-model-rejection" or history["codexExitCode"] != 1:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        require_sha256(history["handshakeDigest"], "INVALID_ROLE_HANDSHAKE")
    elif outcome == "blocked" and value.get("evidenceClass") == "deterministic-production-environment-preflight-failure":
        require_keys(value, common | {"error", "modelInvocations", "liveAttemptsConsumed", "preflightFailure", "historicalNegativeEvidence", "historicalCompatibilityEvidence"}, "INVALID_ROLE_HANDSHAKE")
        if value["schemaVersion"] != 2 or value["error"] != "STATIC_PREFLIGHT_FAILED" or value["attempts"] != 0 or value["modelInvocations"] != 0 or value["liveAttemptsConsumed"] != 0:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        require_keys(value["preflightFailure"], {"code", "message"}, "INVALID_ROLE_HANDSHAKE")
        if value["preflightFailure"]["code"] not in {"GENERATED_PROJECT_CONFIG_PARSE_FAILED", "GENERATED_ROLE_CONFIG_PARSE_FAILED", "GENERATED_PROJECT_CONFIG_INVALID", "GENERATED_ROLE_CONFIG_INVALID", "PROJECT_CONFIG_PARSE_FAILED", "PROJECT_TRUST_NOT_EFFECTIVE", "CUSTOM_ROLE_PARSE_FAILED", "STATIC_PARSER_UNEXPECTED_RESULT", "LIVE_COMMAND_PARSE_FAILED", "PRODUCTION_CONFIG_CHANGED", "PROBE_REPO_CHANGED"}:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        history = value["historicalNegativeEvidence"]
        require_keys(history, {"hostFailure", "evidenceClass", "codexExitCode", "hostError", "handshakeDigest"}, "INVALID_ROLE_HANDSHAKE")
        require_keys(history["hostError"], {"code", "httpStatus", "message"}, "INVALID_ROLE_HANDSHAKE")
        if history["hostFailure"] != "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT" or history["evidenceClass"] != "host-runtime-model-rejection" or history["codexExitCode"] != 1:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        require_sha256(history["handshakeDigest"], "INVALID_ROLE_HANDSHAKE")
    elif outcome in {"role_handshake_ready", "blocked"}:
        require_keys(value, common | {"error", "modelInvocations", "liveAttemptsConsumed", "hostFacts", "historicalNegativeEvidence", "historicalCompatibilityEvidence"}, "INVALID_ROLE_HANDSHAKE")
        facts = value["hostFacts"]
        require_keys(facts, {"parentTurnEntered", "spawnCount", "spawnFacts", "activatedRoles", "unexpectedRoles", "downgradeObserved", "fallbackObserved", "childBindingValid", "childThreadIdentityHash", "childTerminalObserved", "parentTerminalObserved", "codexExitCode", "eventTypes", "threadIdentityHashes", "hostError"}, "INVALID_ROLE_HANDSHAKE")
        if value["schemaVersion"] != 2 or value["evidenceClass"] != "host-runtime-events-plus-deterministic-preflight" or value["attempts"] != 1 or value["modelInvocations"] != 1 or value["liveAttemptsConsumed"] != 1:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        if not isinstance(facts["eventTypes"], list) or not facts["eventTypes"] or any(not isinstance(item, str) or not item for item in facts["eventTypes"]):
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        if not isinstance(facts["threadIdentityHashes"], list) or any(not isinstance(item, str) for item in facts["threadIdentityHashes"]):
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        for identity in facts["threadIdentityHashes"]:
            require_sha256(identity, "INVALID_ROLE_HANDSHAKE")
        if facts["childThreadIdentityHash"] is not None:
            require_sha256(facts["childThreadIdentityHash"], "INVALID_ROLE_HANDSHAKE")
        if not isinstance(facts["spawnFacts"], list):
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        ready_facts = facts["parentTurnEntered"] is True and facts["spawnCount"] == 1 and facts["spawnFacts"] == [{"agentType": "gkd_executor", "taskName": "gkd_executor_handshake", "forkTurns": "none"}] and facts["activatedRoles"] == ["gkd_executor"] and facts["unexpectedRoles"] == [] and facts["downgradeObserved"] is False and facts["fallbackObserved"] is False and facts["childBindingValid"] is True and facts["childThreadIdentityHash"] in facts["threadIdentityHashes"] and facts["childTerminalObserved"] is True and facts["parentTerminalObserved"] is True and facts["codexExitCode"] == 0 and facts["hostError"] is None
        if outcome == "role_handshake_ready":
            if value["error"] is not None or not ready_facts:
                raise TaskError("INVALID_ROLE_HANDSHAKE")
        else:
            if not isinstance(value["error"], str) or not value["error"] or facts["hostError"] is not None and not isinstance(facts["hostError"], dict):
                raise TaskError("INVALID_ROLE_HANDSHAKE")
            if value["error"] not in {"CUSTOM_ROLE_ACTIVATION_MISSING", "PROBE_ORCHESTRATION_MISS_WAIT_BEFORE_SPAWN", "CUSTOM_ROLE_HANDSHAKE_INCOMPLETE"} or ready_facts:
                raise TaskError("INVALID_ROLE_HANDSHAKE")
            if value["error"] != "CUSTOM_ROLE_HANDSHAKE_INCOMPLETE" and (facts["parentTurnEntered"] is not True or facts["spawnCount"] != 0 or facts["spawnFacts"] != [] or facts["activatedRoles"] != [] or facts["unexpectedRoles"] != [] or facts["downgradeObserved"] is not False or facts["fallbackObserved"] is not False or facts["childBindingValid"] is not False or facts["childThreadIdentityHash"] is not None or facts["childTerminalObserved"] is not False or facts["parentTerminalObserved"] is not True or facts["codexExitCode"] != 0 or facts["hostError"] is not None):
                raise TaskError("INVALID_ROLE_HANDSHAKE")
    else:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    compatibility = value.get("historicalCompatibilityEvidence")
    if compatibility is not None:
        require_keys(compatibility, {"failure", "evidenceClass", "strictConfigUsed", "message", "modelInvocations", "liveAttemptsConsumed", "preflightDigest"}, "INVALID_ROLE_HANDSHAKE")
        if compatibility["failure"] != "USER_CONFIG_PARSE_FAILED" or compatibility["evidenceClass"] != "strict-user-config-compatibility-rejection" or compatibility["strictConfigUsed"] is not True or compatibility["modelInvocations"] != 0 or compatibility["liveAttemptsConsumed"] != 0 or not isinstance(compatibility["message"], str) or not compatibility["message"]:
            raise TaskError("INVALID_ROLE_HANDSHAKE")
        require_sha256(compatibility["preflightDigest"], "INVALID_ROLE_HANDSHAKE")
    if value["pathFree"] is not True or value["realOneHourWaitRun"] is not False or value["parentConfigurationSource"] != "normal-user-config" or value["parentModelOverride"] is not False or value["parentReasoningEffortOverride"] is not False or value["parentStrictConfig"] is not False:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    require_keys(value["requestedRole"], {"name", "model", "reasoningEffort", "sandbox"}, "INVALID_ROLE_HANDSHAKE")
    if value["requestedRole"] != {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"}:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    require_keys(value["boundDigests"], {"bundleDigest", "roleDigest", "configDigest", "projectConfigDigest", "probeInstructionsDigest", "skillDigests"}, "INVALID_ROLE_HANDSHAKE")
    for field in ("bundleDigest", "roleDigest", "configDigest", "projectConfigDigest", "probeInstructionsDigest"):
        require_sha256(value["boundDigests"][field], "INVALID_ROLE_HANDSHAKE")
    if not isinstance(value["boundDigests"]["skillDigests"], dict) or not value["boundDigests"]["skillDigests"]:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    for digest in value["boundDigests"]["skillDigests"].values():
        require_sha256(digest, "INVALID_ROLE_HANDSHAKE")
    require_keys(value["setupFacts"], {"codexExecutableResolution", "codexExecutableDigest", "generatedProjectConfigParsed", "generatedRoleConfigParsed", "normalEnvironmentReachedNoTransport", "trustedProjectLayerLoaded", "agentsEnabled", "projectRoleDefinitionAccepted", "customRoleActivationProven", "liveCommandParsed", "probeRepoClean", "probeRepoUnchanged", "productionConfigUnchanged"}, "INVALID_ROLE_HANDSHAKE")
    if value["setupFacts"]["codexExecutableResolution"] != "command-v" or value["setupFacts"]["probeRepoClean"] is not True or value["setupFacts"]["probeRepoUnchanged"] is not True or value["setupFacts"]["productionConfigUnchanged"] is not True:
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    require_sha256(value["setupFacts"]["codexExecutableDigest"], "INVALID_ROLE_HANDSHAKE")
    if value["setupFacts"]["customRoleActivationProven"] is not (outcome == "role_handshake_ready"):
        raise TaskError("INVALID_ROLE_HANDSHAKE")
    require_sha256(value["preflightDigest"], "INVALID_ROLE_HANDSHAKE")
    require_sha256(value["handshakeDigest"], "INVALID_ROLE_HANDSHAKE")
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
        if handshake["boundDigests"]["bundleDigest"] != ACCEPTED_M2_BUNDLE_DIGEST:
            raise TaskError("ROLE_HANDSHAKE_BUNDLE_DRIFT")
        if handshake["handshakeDigest"] != ACCEPTED_M2_HANDSHAKE_DIGEST:
            raise TaskError("ROLE_HANDSHAKE_HISTORY_DRIFT")
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
            "activationProvider": {
                "name": catalog["activationProvider"]["name"],
                "digest": catalog["activationProviderDigest"],
                "boundary": "trusted-main-workflow-authority",
                "trustedMainBoundaryAvailable": True,
                "candidatePublicReceiptWriterAvailable": False,
                "candidatePublicClaimFailClosed": True,
                "cliFailClosed": True,
                "testHostSeamInBundle": False,
                "sameUserTamperingIsNonGoal": True,
            },
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
            "historicalHandshake": {
                "accepted": True,
                "bundleDigest": ACCEPTED_M2_BUNDLE_DIGEST,
                "handshakeDigest": ACCEPTED_M2_HANDSHAKE_DIGEST,
            },
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
