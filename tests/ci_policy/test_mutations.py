from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path("canonical/payload/lib/gkd_ci")


class CiPolicyMutationContracts(unittest.TestCase):
    def killed(self, relative: str, old: str, new: str, test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-m3-mutant-") as temporary:
            package = Path(temporary) / "gkd_ci"
            shutil.copytree(SOURCE, package)
            path = package / relative
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text)
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = f"{temporary}:canonical/payload/lib:."
            result = subprocess.run(
                (sys.executable, "-B", "-m", "unittest", test_name, "-q"),
                cwd=Path(__file__).resolve().parents[2],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)

    def test_mutation_repository_binding_is_killed(self) -> None:
        self.killed(
            "policy.py",
            "    if origin.casefold() != policy.repository.casefold():\n",
            "    if False:\n",
            "tests.ci_policy.test_policy.PolicyContracts.test_origin_missing_nongithub_mismatch_ambiguity_and_base_drift_fail_closed",
        )

    def test_mutation_head_binding_is_killed(self) -> None:
        self.killed(
            "monitor.py",
            "        if observation.head_sha != request.expected_head:\n",
            "        if False:\n",
            "tests.ci_policy.test_monitor.MonitorContracts.test_head_drift_terminal_failure_and_closed_pr_are_terminal",
        )

    def test_mutation_success_gate_is_killed(self) -> None:
        self.killed(
            "monitor.py",
            '        if len(checks) == len(policy.required_checks) and all(state == "success" for _, state in checks):\n',
            "        if True:\n",
            "tests.ci_policy.test_monitor.MonitorContracts.test_pending_and_missing_checks_poll_then_timeout_once",
        )

    def test_mutation_ambiguity_gate_is_killed(self) -> None:
        self.killed(
            "github.py",
            "            if len(matches) > 1:\n",
            "            if False:\n",
            "tests.ci_policy.test_github.GitHubBoundaryContracts.test_duplicate_cross_source_and_unknown_conclusion_fail_closed",
        )

    def test_mutation_policy_drift_gate_is_killed(self) -> None:
        self.killed(
            "monitor.py",
            "            last = observation\n            observed_policy = load_validated_policy(request.checkout, request.repository, request.policy_path)\n            if observed_policy.digest != request.policy_digest:\n",
            "            last = observation\n            if False:\n",
            "tests.ci_policy.test_monitor.MonitorContracts.test_policy_drift_and_transport_error_return_stable_terminal_errors",
        )


if __name__ == "__main__":
    unittest.main()
