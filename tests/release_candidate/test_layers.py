from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gkd_release.core import build_release_candidate
from gkd_release.verification import (
    CANARY_CHECK,
    build_l4_canary_request,
    run_l1_properties,
    validate_forward_eval_trace,
    validate_l4_canary_request,
    validate_l4_canary_result,
)
from gkd_task.canonical import canonical_bytes, digest_object
from gkd_task.errors import TaskError
from tests.ci_policy.helpers import check_run, fake_github_environment, pull_request, write_scenario


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY = ROOT / "canonical/payload/fixtures/release/traceability.json"
FORWARD_EVAL = ROOT / "canonical/payload/fixtures/release/forward-eval-trace.json"
SANDBOX_REPOSITORY = "github.com/KNaiFen/gkd-sandbox"


def release_input() -> dict:
    return {
        "version": "0.1.0",
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

    def test_l3_fresh_agent_forward_eval_fixture_is_exact_sha_and_redacted(self) -> None:
        trace = json.loads(FORWARD_EVAL.read_text(encoding="utf-8"))
        self.assertEqual(trace, validate_forward_eval_trace(trace, "a" * 40))
        trace["sourceSha"] = "b" * 40
        with self.assertRaisesRegex(TaskError, "L3_SOURCE_SHA_MISMATCH"):
            validate_forward_eval_trace(trace, "a" * 40)

    def test_l4_sandbox_canary_plan_and_result_are_bound_to_one_sha(self) -> None:
        record = build_release_candidate(release_input())
        request = build_l4_canary_request(record)
        self.assertEqual(request, validate_l4_canary_request(request))
        result = {
            "branch": request["branch"],
            "eventDigest": "f" * 64,
            "outcome": "success",
            "pullRequest": 4,
            "repository": SANDBOX_REPOSITORY,
            "requestDigest": request["requestDigest"],
            "schemaVersion": 1,
            "sourceSha": request["sourceSha"],
        }
        self.assertEqual(result, validate_l4_canary_result(request, result))

    def test_critical_l3_and_l4_mutations_are_killed(self) -> None:
        trace = json.loads(FORWARD_EVAL.read_text(encoding="utf-8"))
        trace["roleName"] = "worker"
        with self.assertRaisesRegex(TaskError, "L3_TRACE_INVALID"):
            validate_forward_eval_trace(trace)
        request = build_l4_canary_request(build_release_candidate(release_input()))
        request["repository"] = "github.com/KNaiFen/gkd"
        with self.assertRaisesRegex(TaskError, "L4_CANARY_REQUEST_TAMPERED"):
            validate_l4_canary_request(request)

    def test_l4_result_rejects_cross_request_mutation(self) -> None:
        request = build_l4_canary_request(build_release_candidate(release_input()))
        result = {
            "branch": request["branch"],
            "eventDigest": "f" * 64,
            "outcome": "success",
            "pullRequest": 4,
            "repository": SANDBOX_REPOSITORY,
            "requestDigest": "0" * 64,
            "schemaVersion": 1,
            "sourceSha": request["sourceSha"],
        }
        with self.assertRaisesRegex(TaskError, "L4_CANARY_RESULT_INVALID"):
            validate_l4_canary_result(request, result)
