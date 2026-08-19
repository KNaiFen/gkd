from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path("canonical/payload/lib/gkd_role")


class RuntimeBridgeMutationContracts(unittest.TestCase):
    def _killed(self, relative: str, old: str, new: str, test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-m2c-mutant-") as temporary:
            package = Path(temporary) / "gkd_role"
            shutil.copytree(SOURCE, package)
            path = package / relative
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text)
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = f"{temporary}:canonical/payload/lib:."
            result = subprocess.run(
                [sys.executable, "-m", "unittest", test_name, "-q"],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)

    def test_mutation_route_decision_binding_is_killed(self) -> None:
        self._killed(
            "bridge.py",
            '        or facts["routeDecisionDigest"] != expected["routeDecisionDigest"]\n',
            '        or False\n',
            "tests.runtime_bridge.test_bridge.AutomaticBridgeContracts.test_spawn_mismatch_matrix_is_write_free",
        )

    def test_mutation_fallback_rejection_is_killed(self) -> None:
        self._killed(
            "bridge.py",
            '        or facts["fallbackAttempted"] is not False\n',
            '        or False\n',
            "tests.runtime_bridge.test_bridge.AutomaticBridgeContracts.test_spawn_mismatch_matrix_is_write_free",
        )

    def test_mutation_project_digest_check_is_killed(self) -> None:
        self._killed(
            "project.py",
            '        if sha256_bytes(path.read_bytes()) != record["sha256"]:\n',
            '        if False:\n',
            "tests.runtime_bridge.test_project.ProjectStagingContracts.test_symlink_traversal_overlap_and_bundle_drift_fail_closed",
        )


if __name__ == "__main__":
    unittest.main()
