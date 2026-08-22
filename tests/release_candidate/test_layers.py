from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from unittest import mock

from gkd_release.core import (
    build_release_candidate,
    post_merge_promotion_request,
    validate_post_merge_release_record,
)
from gkd_release.verification import (
    CANARY_CHECK,
    CANARY_MARKER_PATH,
    TrustedMainFinalGate,
    build_l4_canary_request,
    run_l1_properties,
    validate_l3_eval_only_record,
    validate_l3_eval_only_trace,
    validate_l4_canary_request,
    validate_l4_canary_result,
    validate_canary_marker,
    validate_post_merge_l4_canary_request,
    validate_post_merge_l4_observed_check,
)
from gkd_task.canonical import canonical_bytes, digest_object
from gkd_task.errors import TaskError
from tests.ci_policy.helpers import (
    canary_marker_document,
    check_run,
    fake_github_environment,
    pull_request,
    write_scenario,
)


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY = ROOT / "canonical/payload/fixtures/release/traceability.json"
FORWARD_EVAL = ROOT / "canonical/payload/fixtures/release/forward-eval-trace.json"
SANDBOX_REPOSITORY = "github.com/KNaiFen/gkd-sandbox"


def release_input() -> dict:
    return {
        "version": "0.1.1",
        "sourceSha": "a" * 40,
        "bundleDigest": "b" * 64,
        "evidenceDigest": "c" * 64,
        "traceability": json.loads(TRACEABILITY.read_text(encoding="utf-8")),
        "layers": ["L0", "L1", "L2", "L3", "L4"],
        "sandboxRepository": SANDBOX_REPOSITORY,
    }


class LayeredVerificationContracts(unittest.TestCase):
    def test_l1_property_matrix_emits_distinct_positive_negative_and_mutation_evidence(self) -> None:
        evidence = run_l1_properties(release_input()["traceability"])
        self.assertEqual("L1", evidence["layer"])
        self.assertEqual(16, len(evidence["properties"]))
        self.assertEqual({"pass"}, {item["positive"] for item in evidence["properties"]})
        self.assertEqual({"pass"}, {item["negative"] for item in evidence["properties"]})
        self.assertEqual({"pass"}, {item["mutation"] for item in evidence["properties"]})

    def test_l2_subprocess_fake_github_probe_is_reproducible_and_read_only(self) -> None:
        request = {
            "baseBranch": "main",
            "expectedHead": "a" * 40,
            "pullRequest": 4,
            "repository": SANDBOX_REPOSITORY,
            "requiredCheck": CANARY_CHECK,
            "schemaVersion": 1,
        }
        scenario = {
            "pullRequest": pull_request(number=4, repository="KNaiFen/gkd-sandbox"),
            "checkPages": {"1": {"check_runs": [check_run(CANARY_CHECK)], "total_count": 1}},
            "statusPages": {"1": []},
        }
        with tempfile.TemporaryDirectory(prefix="gkd-release-l2-") as temporary:
            root = Path(temporary)
            scenario_path = root / "scenario.json"
            input_path = root / "request.json"
            write_scenario(scenario_path, scenario)
            input_path.write_bytes(canonical_bytes(request))
            environment = fake_github_environment(root, scenario_path)
            command = [sys.executable, "canonical/payload/bin/gkd-release", "l2-probe", "--input", os.fspath(input_path)]
            first = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, check=False)
            second = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, check=False)
            self.assertEqual(0, first.returncode, first.stderr.decode())
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(SANDBOX_REPOSITORY, json.loads(first.stdout)["repository"])

    def test_l3_eval_only_fixture_is_exact_sha_redacted_and_write_free(self) -> None:
        trace = json.loads(FORWARD_EVAL.read_text(encoding="utf-8"))
        self.assertEqual(trace, validate_l3_eval_only_trace(trace, "a" * 40))
        self.assertEqual(
            {
                "pullRequestWrite": False,
                "sourceMutation": False,
                "taskLifecycleWrite": False,
            },
            trace["effectBoundary"],
        )
        trace["releaseSourceSha"] = "b" * 40
        with self.assertRaisesRegex(TaskError, "L3_SOURCE_SHA_MISMATCH"):
            validate_l3_eval_only_trace(trace, "a" * 40)

    def test_l4_sandbox_canary_plan_and_result_are_bound_to_one_sha(self) -> None:
        record = build_release_candidate(release_input())
        request = build_l4_canary_request(record, "b" * 40)
        self.assertEqual(request, validate_l4_canary_request(request))
        result = {
            "branch": request["branch"],
            "eventDigest": "f" * 64,
            "outcome": "success",
            "pullRequest": 4,
            "repository": SANDBOX_REPOSITORY,
            "requestDigest": request["requestDigest"],
            "schemaVersion": 1,
            "releaseSourceSha": request["releaseSourceSha"],
        }
        self.assertEqual(result, validate_l4_canary_result(request, result))

    def test_critical_l3_and_l4_mutations_are_killed(self) -> None:
        trace = json.loads(FORWARD_EVAL.read_text(encoding="utf-8"))
        trace["roleName"] = "worker"
        with self.assertRaisesRegex(TaskError, "L3_EVAL_ONLY_INVALID"):
            validate_l3_eval_only_trace(trace)
        request = build_l4_canary_request(
            build_release_candidate(release_input()), "b" * 40
        )
        request["repository"] = "github.com/KNaiFen/gkd"
        with self.assertRaisesRegex(TaskError, "L4_CANARY_REQUEST_TAMPERED"):
            validate_l4_canary_request(request)

    def test_l4_result_rejects_cross_request_mutation(self) -> None:
        request = build_l4_canary_request(
            build_release_candidate(release_input()), "b" * 40
        )
        result = {
            "branch": request["branch"],
            "eventDigest": "f" * 64,
            "outcome": "success",
            "pullRequest": 4,
            "repository": SANDBOX_REPOSITORY,
            "requestDigest": "0" * 64,
            "schemaVersion": 1,
            "releaseSourceSha": request["releaseSourceSha"],
        }
        with self.assertRaisesRegex(TaskError, "L4_CANARY_RESULT_INVALID"):
            validate_l4_canary_result(request, result)

    def _trusted_main_final_gate(self) -> tuple[
        TrustedMainFinalGate, dict, dict, dict, dict, list[dict]
    ]:
        source_sha = "a" * 40
        sandbox_head_sha = "b" * 40
        gate = TrustedMainFinalGate(
            source_sha, SANDBOX_REPOSITORY, sandbox_head_sha
        )
        candidate = build_release_candidate(release_input())
        trace = json.loads(FORWARD_EVAL.read_text(encoding="utf-8"))
        l3_record = gate.l3_eval_only(trace)
        request = gate.l4_canary_request(candidate)
        marker = {
            "bundleDigest": candidate["bundleDigest"],
            "releaseSourceSha": source_sha,
            "schemaVersion": 1,
        }
        scenario = {
            "pullRequest": pull_request(
                number=4,
                repository="KNaiFen/gkd-sandbox",
                head=sandbox_head_sha,
                head_branch=request["branch"],
            ),
            "checkPages": {
                "1": {
                    "check_runs": [check_run(CANARY_CHECK, head=sandbox_head_sha)],
                    "total_count": 1,
                }
            },
            "canaryMarkers": {
                sandbox_head_sha: canary_marker_document(marker),
            },
            "statusPages": {"1": []},
        }
        with tempfile.TemporaryDirectory(prefix="gkd-release-l4-") as temporary:
            root = Path(temporary)
            scenario_path = root / "scenario.json"
            write_scenario(scenario_path, scenario)
            environment = fake_github_environment(root, scenario_path)
            with mock.patch.dict(os.environ, environment, clear=True):
                observed_check = gate.observe_l4_canary(request, 4)
        assets = [
            {
                "name": "gkd-0.1.1.tar.gz",
                "sourceSha": source_sha,
                "bundleDigest": candidate["bundleDigest"],
                "sha256": "f" * 64,
            }
        ]
        record = gate.release_record(candidate, l3_record, request, observed_check, assets)
        return gate, l3_record, request, observed_check, record, assets

    def test_trusted_main_final_gate_binds_distinct_source_and_sandbox_heads(self) -> None:
        _, l3_record, request, observed_check, record, assets = self._trusted_main_final_gate()
        self.assertEqual(l3_record, validate_l3_eval_only_record(l3_record, "a" * 40))
        self.assertEqual(
            request,
            validate_post_merge_l4_canary_request(
                request, "a" * 40, SANDBOX_REPOSITORY, "b" * 40
            ),
        )
        self.assertEqual(observed_check, validate_post_merge_l4_observed_check(request, observed_check))
        self.assertEqual("a" * 40, observed_check["releaseSourceSha"])
        self.assertEqual("b" * 40, observed_check["sandboxHeadSha"])
        self.assertEqual(CANARY_MARKER_PATH, observed_check["markerPath"])
        self.assertEqual(
            observed_check["canaryMarker"],
            validate_canary_marker(
                observed_check["canaryMarker"], "a" * 40, "b" * 64
            ),
        )
        self.assertEqual(record, validate_post_merge_release_record(record))
        promotion = post_merge_promotion_request(record)
        self.assertEqual("a" * 40, promotion["targetSha"])
        self.assertEqual(promotion["targetSha"], promotion["releaseSha"])
        self.assertEqual(assets, promotion["assets"])
        self.assertEqual("a" * 40, promotion["assets"][0]["sourceSha"])

    def test_post_merge_records_fail_closed_on_source_head_marker_l3_and_check_substitution(self) -> None:
        gate, l3_record, request, observed_check, _, assets = self._trusted_main_final_gate()
        l3_mutation = deepcopy(l3_record)
        l3_mutation["releaseSourceSha"] = "b" * 40
        l3_mutation["trace"]["releaseSourceSha"] = "b" * 40
        l3_mutation["traceDigest"] = digest_object(l3_mutation["trace"])
        unsigned_l3 = dict(l3_mutation)
        unsigned_l3.pop("recordDigest")
        l3_mutation["recordDigest"] = digest_object(unsigned_l3)
        with self.assertRaisesRegex(TaskError, "L3_SOURCE_SHA_MISMATCH"):
            validate_l3_eval_only_record(l3_mutation, "a" * 40)

        request_mutation = deepcopy(request)
        request_mutation["releaseSourceSha"] = "b" * 40
        request_mutation["branch"] = f"gkd-canary/{'b' * 12}"
        unsigned_request = dict(request_mutation)
        unsigned_request.pop("requestDigest")
        request_mutation["requestDigest"] = digest_object(unsigned_request)
        with self.assertRaisesRegex(TaskError, "L4_SOURCE_SHA_MISMATCH"):
            validate_post_merge_l4_canary_request(
                request_mutation, "a" * 40, SANDBOX_REPOSITORY, "b" * 40
            )

        sandbox_head_mutation = deepcopy(request)
        sandbox_head_mutation["sandboxHeadSha"] = "c" * 40
        unsigned_request = dict(sandbox_head_mutation)
        unsigned_request.pop("requestDigest")
        sandbox_head_mutation["requestDigest"] = digest_object(unsigned_request)
        with self.assertRaisesRegex(TaskError, "L4_SANDBOX_HEAD_SHA_MISMATCH"):
            validate_post_merge_l4_canary_request(
                sandbox_head_mutation, "a" * 40, SANDBOX_REPOSITORY, "b" * 40
            )

        marker_mutation = deepcopy(observed_check)
        marker_mutation["canaryMarker"]["bundleDigest"] = "d" * 64
        marker_mutation["markerDigest"] = digest_object(marker_mutation["canaryMarker"])
        unsigned_observed = dict(marker_mutation)
        unsigned_observed.pop("recordDigest")
        marker_mutation["recordDigest"] = digest_object(unsigned_observed)
        with self.assertRaisesRegex(TaskError, "L4_MARKER_BUNDLE_DIGEST_MISMATCH"):
            validate_post_merge_l4_observed_check(request, marker_mutation)

        observed_mutation = deepcopy(observed_check)
        observed_mutation["outcome"] = "failure"
        unsigned_observed = dict(observed_mutation)
        unsigned_observed.pop("recordDigest")
        observed_mutation["recordDigest"] = digest_object(unsigned_observed)
        with self.assertRaisesRegex(TaskError, "L4_CANARY_OBSERVATION_INVALID"):
            validate_post_merge_l4_observed_check(request, observed_mutation)

        split_assets = deepcopy(assets)
        split_assets[0]["sourceSha"] = "b" * 40
        with self.assertRaisesRegex(TaskError, "POST_MERGE_ASSET_PROVENANCE_MISMATCH"):
            gate.release_record(
                build_release_candidate(release_input()),
                l3_record,
                request,
                observed_check,
                split_assets,
            )
