from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.ci_policy.helpers import (
    EXPECTED_HEAD,
    ROOT,
    SYNTHETIC_CHECK,
    SYNTHETIC_REPOSITORY,
    check_run,
    fake_github_environment,
    init_checkout,
    pull_request,
    tree_digest,
    write_scenario,
)


class CliAndRepositoryContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-m3-cli-")
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_installed_cli_uses_fake_github_and_writes_one_terminal_json(self) -> None:
        checkout = init_checkout(self.root)
        scenario = self.root / "scenario.json"
        write_scenario(
            scenario,
            {
                "checkPages": {"1": {"check_runs": [check_run()], "total_count": 1}},
                "pullRequest": pull_request(),
                "statusPages": {"1": []},
            },
        )
        environment = fake_github_environment(self.root, scenario)
        before = tree_digest(checkout)
        result = subprocess.run(
            (
                str(ROOT / "canonical" / "payload" / "bin" / "gkd-ci-monitor"),
                "--checkout",
                str(checkout),
                "--repository",
                SYNTHETIC_REPOSITORY,
                "--pull-request",
                "8",
                "--expected-head",
                EXPECTED_HEAD,
                "--policy",
                ".gkd/policy.json",
                "--timeout-seconds",
                "5",
                "--poll-interval-seconds",
                "1",
            ),
            cwd=checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        terminal = json.loads(result.stdout)
        self.assertEqual("success", terminal["outcome"])
        self.assertEqual(before, tree_digest(checkout))

    def test_transport_failure_is_redacted_and_never_prints_raw_body(self) -> None:
        checkout = init_checkout(self.root)
        scenario = self.root / "scenario.json"
        write_scenario(scenario, {"transportFailure": True})
        environment = fake_github_environment(self.root, scenario)
        result = subprocess.run(
            (
                str(ROOT / "canonical" / "payload" / "bin" / "gkd-ci-monitor"),
                "--checkout",
                str(checkout),
                "--repository",
                SYNTHETIC_REPOSITORY,
                "--pull-request",
                "8",
                "--expected-head",
                EXPECTED_HEAD,
                "--policy",
                ".gkd/policy.json",
                "--timeout-seconds",
                "5",
                "--poll-interval-seconds",
                "1",
            ),
            cwd=checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        self.assertEqual(2, result.returncode)
        combined = result.stdout + result.stderr
        self.assertNotIn("fixture-secret", combined)
        self.assertNotIn("/Users/private", combined)
        self.assertEqual("GITHUB_QUERY_FAILED", json.loads(result.stdout)["reason"])

    def test_repository_policy_workflow_verifier_and_schemas_agree(self) -> None:
        policy = json.loads((ROOT / ".gkd" / "policy.json").read_text(encoding="utf-8"))
        workflow = (ROOT / ".github" / "workflows" / "gkd-ci.yml").read_text(encoding="utf-8")
        self.assertEqual(["GKD Verify"], policy["requiredChecks"])
        self.assertIn("name: GKD Verify", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("scripts/gkd-verify --base-sha", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertTrue(os.access(ROOT / "scripts" / "gkd-verify", os.X_OK))
        for schema in ("policy.schema.json", "terminal-result.schema.json"):
            value = json.loads(
                (ROOT / "canonical" / "payload" / "schema" / "ci" / schema).read_text(encoding="utf-8")
            )
            self.assertEqual("object", value["type"])
            self.assertFalse(value["additionalProperties"])

    def test_reusable_mechanism_contains_no_repository_specific_constants(self) -> None:
        mechanism = ROOT / "canonical" / "payload" / "lib" / "gkd_ci"
        data = b"\n".join(path.read_bytes() for path in sorted(mechanism.glob("*.py")))
        for forbidden in (b"KNaiFen", b"GKD Verify", b"task/m3", os.fspath(ROOT).encode("utf-8")):
            self.assertNotIn(forbidden, data)


if __name__ == "__main__":
    unittest.main()
