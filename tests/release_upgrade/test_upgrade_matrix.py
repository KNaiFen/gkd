from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import platform
import sys
import tempfile
import unittest

from gkd_finalization.core import build_finalization
from gkd_release.core import build_release_candidate, promotion_request
from gkd_role.activation import TrustedMainActivationAuthority
from gkd_role.roles import role_catalog, role_record
from gkd_role.waiting import new_wait_state, transition
from gkd_task.canonical import FixedClock, SystemNonce, canonical_bytes, digest_object
from gkd_task.errors import TaskError
from gkd_task.migration import migrate_v1
from gkd_task.model import record_acceptance_state, record_completion_state
from gkd_task.results import (
    CanonicalResultError,
    LEGACY_SCOPE_NAMES,
    canonical_bytes as result_canonical_bytes,
    digest_object as result_digest_object,
    load_canonical_results,
)
from gkd_task.runtime import RuntimeStore, validate_envelope
from tests.finalization.helpers import finalization_input
from tests.foundation.helpers import copy_source, gkd_bundle
from tests.role_routing.helpers import BUNDLE_ROOT, bundle_digest
from tests.task_core.helpers import CONFIG_DIGEST, FIXED_TIME, FUTURE_TIME, ROLE_DIGEST, TaskRepo, make_legacy_v1, run


class ReleaseUpgradeMatrixContracts(unittest.TestCase):
    def test_source_v1_schema_matrix(self) -> None:
        cases = (
            ("v1-packs", "schema_version = 2", "schema_version = 1", "INVALID_SOURCE_DECLARATION"),
            ("v2-missing-packs", '[[packs]]\nname = "ci-advice"\n\n[[packs]]\nname = "review-remediation"\n\n', "", "INVALID_SOURCE_DECLARATION"),
            ("unknown-schema", "schema_version = 2", "schema_version = 3", "INVALID_SOURCE_DECLARATION"),
            ("pack-owner-drift", 'pack = "ci-advice"', 'pack = "unknown"', "INVALID_COMPONENT"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, before, after, error in cases:
                with self.subTest(name=name):
                    destination = root / name
                    destination.mkdir()
                    source = copy_source(destination)
                    gkd_bundle.generate(source)
                    declaration_path = source / "source.toml"
                    declaration_path.write_text(
                        declaration_path.read_text(encoding="utf-8").replace(before, after, 1),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(gkd_bundle.BundleError, error):
                        gkd_bundle.generate(source)

    def test_install_v1_metadata_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = copy_source(Path(temporary))
            manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
            manifest["schemaVersion"] = 1
            manifest.pop("packs")
            for component in manifest["components"]:
                component.pop("pack", None)
            for mutation in ("component-pack", "unexpected-top-level"):
                with self.subTest(mutation=mutation):
                    candidate = json.loads(json.dumps(manifest))
                    if mutation == "component-pack":
                        candidate["components"][0]["pack"] = "ci-advice"
                    else:
                        candidate["packs"] = []
                    with self.assertRaisesRegex(gkd_bundle.BundleError, "INSTALLED_MANIFEST_INVALID"):
                        gkd_bundle._validate_installed_manifest(candidate)

    def test_result_manifest_v1_scope_matrix(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        head = run("git", "rev-parse", "HEAD", cwd=repository)
        digest = "a" * 64
        for scopes in (LEGACY_SCOPE_NAMES[:-1], tuple(reversed(LEGACY_SCOPE_NAMES))):
            with self.subTest(scopes=scopes), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = {
                    "baseSha": head,
                    "environment": {
                        "dependenciesInstalled": False,
                        "platform": platform.system().lower(),
                        "pythonVersion": sys.version.split()[0],
                    },
                    "headSha": head,
                    "schemaVersion": 1,
                    "scopes": list(scopes),
                    "verifierDigest": digest,
                }
                manifest["manifestDigest"] = result_digest_object(manifest)
                (root / "manifest.json").write_bytes(result_canonical_bytes(manifest))
                with self.assertRaisesRegex(CanonicalResultError, "CANONICAL_RESULT_SCOPE_MISMATCH"):
                    load_canonical_results(root, "foundation", repository)

    def test_task_path_v1_archived_restore(self) -> None:
        repo = TaskRepo()
        try:
            service, candidate_head = repo.delivered()
            state = repo.state()
            accepted = record_acceptance_state(state, candidate_head, "a" * 64, True, FIXED_TIME)
            completed = record_completion_state(accepted, repo.base_sha, digest_object({"archive": "fixture"}), FIXED_TIME)
            legacy = make_legacy_v1(completed, str(repo.root / "deleted-worktree"), True)
            (repo.task_root / "task.json").write_bytes(canonical_bytes(legacy))
            run("git", "add", f"{repo.task_path}/task.json", cwd=repo.candidate)
            run("git", "commit", "-m", "archived legacy", cwd=repo.candidate)
            result = migrate_v1(repo.candidate, repo.task_path, RuntimeStore(repo.runtime_root), repo.head(), completed["revision"], FixedClock(FIXED_TIME), SystemNonce())
            self.assertEqual("migrated_v1", result["status"])
            self.assertEqual("completed", repo.state()["lifecycle"]["phase"])
            with self.assertRaisesRegex(TaskError, "worktree_missing"):
                RuntimeStore(repo.runtime_root).read_attachment(repo.identity, repo.task_id, repo.task_branch)
        finally:
            repo.close()

    def test_offer_v1_claim_to_delivery_matrix(self) -> None:
        repo = TaskRepo()
        try:
            service, claim_id = repo.offer_and_claim()
            offer = json.loads((repo.task_root / "offer.json").read_text(encoding="utf-8"))
            self.assertEqual(1, offer["schemaVersion"])
            delivered = repo.deliver(service, claim_id)
            self.assertEqual("delivered", delivered["status"])
        finally:
            repo.close()

    def test_launch_envelope_v1_mismatch_matrix(self) -> None:
        repo = TaskRepo()
        try:
            service = repo.ready_and_authorized()
            service.offer(*repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
            handoff = service.handoff()
            envelope = RuntimeStore(repo.runtime_root).read_envelope(handoff["envelopeId"])
            for field, value in (("capability", "short"), ("candidateRoot", "relative")):
                with self.subTest(field=field):
                    candidate = dict(envelope)
                    candidate[field] = value
                    candidate["envelopeDigest"] = digest_object(
                        {key: item for key, item in candidate.items() if key != "envelopeDigest"}
                    )
                    with self.assertRaisesRegex(TaskError, "INVALID_LAUNCH_ENVELOPE"):
                        validate_envelope(candidate)
        finally:
            repo.close()

    def test_role_activation_v1_binding_matrix(self) -> None:
        repo = TaskRepo()
        try:
            digest = bundle_digest()
            catalog = role_catalog(BUNDLE_ROOT, digest)
            role = role_record(catalog, "gkd_executor")
            service = repo.ready_and_authorized()
            service.offer(*repo.cas(), "manual", role["roleDigest"], role["configDigest"], FUTURE_TIME, "gkd_executor", digest)
            handoff = service.handoff()
            offer = json.loads((repo.task_root / "offer.json").read_text(encoding="utf-8"))
            expected = {
                "taskId": repo.task_id,
                "repository": repo.identity,
                "taskBranch": repo.task_branch,
                "offerId": offer["offerId"],
                "envelopeId": handoff["envelopeId"],
                "route": "manual",
                "roleName": "gkd_executor",
                "roleDigest": role["roleDigest"],
                "configDigest": role["configDigest"],
                "bundleDigest": digest,
                "offerCreatedAt": offer["createdAt"],
                "offerExpiresAt": offer["expiresAt"],
            }
            observation = {
                "evidenceClass": "host-runtime-event",
                "agentId": "agent-one",
                "threadDigest": "e" * 64,
                "model": role["model"],
                "reasoningEffort": role["modelReasoningEffort"],
                "sandbox": role["sandboxMode"],
                "runtimeSeconds": role["runtimeSeconds"],
                "activatedAt": FIXED_TIME,
            }
            authority = TrustedMainActivationAuthority(RuntimeStore(repo.runtime_root), catalog)
            activation = authority.build(expected, observation, "activation-nonce")
            self.assertEqual(1, activation["schemaVersion"])
            mutated = dict(expected)
            mutated["roleName"] = "gkd_acceptor"
            with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
                authority.build(mutated, observation, "activation-nonce")
            mutated_observation = dict(observation)
            mutated_observation["runtimeSeconds"] = 3600
            with self.assertRaisesRegex(TaskError, "ACTIVATION_OBSERVATION_MISMATCH"):
                authority.build(expected, mutated_observation, "activation-nonce")
        finally:
            repo.close()

    def test_wait_state_v1_deadline_matrix(self) -> None:
        started = datetime(2026, 1, 1, tzinfo=timezone.utc)
        identity = {
            "taskId": "TASK-1",
            "repository": "example.test/team/repo",
            "head": "a" * 40,
            "claimId": "b" * 64,
            "agentId": "agent-one",
            "sessionDigest": "c" * 64,
            "bundleDigest": bundle_digest(),
        }
        for hour in (12, 13):
            with self.subTest(hour=hour):
                state = new_wait_state(identity, "2026-01-01T00:00:00Z")
                observation = {
                    "schemaVersion": 1,
                    "kind": "healthy_timeout",
                    "observedAt": (started + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeoutMs": 3_600_000,
                    "identity": identity,
                }
                result = transition(state, observation)
                self.assertEqual("deadline_timeout", result["outcome"])
                self.assertEqual({"agentId": "agent-one", "once": True}, result["interrupt"])

    def test_finalization_release_input_matrix(self) -> None:
        source = finalization_input("release")
        for field, value in (("adapterDigest", None), ("authorizationDigest", None), ("assets", [])):
            with self.subTest(field=field):
                candidate = dict(source)
                candidate[field] = value
                with self.assertRaisesRegex(TaskError, "RELEASE_AUTHORIZATION_REQUIRED"):
                    build_finalization(candidate)

    def test_finalization_source_binding_matrix(self) -> None:
        mutations = (
            ("metadata", "mainSha", "d" * 40),
            ("metadata", "sourceSha", "d" * 40),
            ("evidence", "sourceSha", "d" * 40),
            ("assets", 0, "sourceSha", "d" * 40),
            ("taskPr", "headSha", "d" * 40),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = finalization_input("release")
                if mutation[0] == "assets":
                    candidate[mutation[0]][mutation[1]][mutation[2]] = mutation[3]
                else:
                    candidate[mutation[0]][mutation[1]] = mutation[2]
                with self.assertRaisesRegex(TaskError, "FINALIZATION_(SHA|EVIDENCE|ASSET)_SPLIT"):
                    build_finalization(candidate)

    def test_release_record_stable_version_matrix(self) -> None:
        traceability = json.loads(
            (Path(__file__).resolve().parents[2] / "canonical/inputs/release/traceability.json").read_text(encoding="utf-8")
        )
        candidate = {
            "version": "0.1.5",
            "sourceSha": "a" * 40,
            "bundleDigest": "b" * 64,
            "evidenceDigest": "c" * 64,
            "traceability": traceability,
            "layers": ["L0", "L1", "L2", "L3", "L4"],
            "sandboxRepository": "github.com/KNaiFen/gkd-sandbox",
        }
        for version in ("0.1.0", "0.1.5", "1.2.3"):
            with self.subTest(version=version):
                value = dict(candidate, version=version)
                self.assertEqual(f"v{version}", promotion_request(build_release_candidate(value))["tagName"])
        for version in ("0.1", "0.01.5", "0.1.5-rc.1", "v0.1.5", ""):
            with self.subTest(version=version):
                invalid = dict(candidate, version=version)
                with self.assertRaisesRegex(TaskError, "INVALID_RELEASE_CANDIDATE"):
                    build_release_candidate(invalid)


if __name__ == "__main__":
    unittest.main()
