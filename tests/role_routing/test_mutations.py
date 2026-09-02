from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path("canonical/payload/lib/gkd_role")


class MutationContracts(unittest.TestCase):
    def _killed(self, relative: str, old: str, new: str, test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-role-mutant-") as temporary:
            package = Path(temporary) / "gkd_role"
            shutil.copytree(SOURCE, package)
            path = package / relative
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text, f"mutation anchor missing: {relative}")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONPATH"] = f"{temporary}:canonical/payload/lib:."
            result = subprocess.run([sys.executable, "-m", "unittest", test_name, "-q"], cwd=Path.cwd(), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=90)
            self.assertNotEqual(0, result.returncode, f"mutant survived {test_name}\n{result.stdout}\n{result.stderr}")

    def test_mutation_role_authority_is_killed(self) -> None:
        self._killed("roles.py", '    allowed = action in source["roleActions"][role_name]\n', '    allowed = True or action in source["roleActions"][role_name]\n', "tests.role_routing.test_roles.RoleContracts.test_role_authority_matrix_denies_every_forbidden_boundary")

    def test_mutation_route_fallback_is_killed(self) -> None:
        self._killed("routing.py", '        "fallbackAttempted": False,\n', '        "fallbackAttempted": True,\n', "tests.role_routing.test_routing_waiting.RoutingContracts.test_manual_is_default_and_does_not_claim_automatic_readiness")

    def test_mutation_short_wait_is_killed(self) -> None:
        self._killed("waiting.py", "WAIT_TIMEOUT_MS = 3_600_000\n", "WAIT_TIMEOUT_MS = 360_000\n", "tests.role_routing.test_routing_waiting.WaitingContracts.test_short_wait_and_early_timeout_are_rejected_not_rounded_up")

    def test_mutation_activation_task_binding_is_killed(self) -> None:
        self._killed("activation.py", '    names = ["taskId", "repository", "taskBranch", "route",', '    names = ["repository", "taskBranch", "route",', "tests.role_routing.test_activation.ActivationContracts.test_cross_task_offer_envelope_route_and_bundle_bindings_fail_before_claim_commit")

if __name__ == "__main__":
    unittest.main()
