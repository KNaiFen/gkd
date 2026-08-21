from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path("canonical/payload/lib/gkd_finalization")


class FinalizationMutationContracts(unittest.TestCase):
    def _killed(self, replacements: list[tuple[str, str]], test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-finalization-mutant-") as temporary:
            package = Path(temporary) / "gkd_finalization"
            shutil.copytree(SOURCE, package)
            path = package / "core.py"
            text = path.read_text(encoding="utf-8")
            for old, new in replacements:
                self.assertIn(old, text)
                text = text.replace(old, new, 1)
            path.write_text(text, encoding="utf-8")
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = f"{temporary}:canonical/payload/lib:."
            result = subprocess.run([sys.executable, "-m", "unittest", test_name, "-q"], cwd=Path.cwd(), env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=90)
            self.assertNotEqual(0, result.returncode, f"mutant survived {test_name}\n{result.stdout}\n{result.stderr}")

    def test_mutation_closeout_boundary_is_killed(self) -> None:
        self._killed(
            [
                ("        if value[\"productLogic\"] or value[\"releaseSideEffects\"] or value[\"adapterDigest\"] is not None or value[\"authorizationDigest\"] is not None or assets:\n", "        if False:\n"),
                ("            finalization[\"phase\"] != \"closeout-ready\"\n            or finalization[\"productLogic\"]\n", "            False\n"),
            ],
            "tests.finalization.test_finalization.FinalizationContracts.test_closeout_rejects_product_logic_release_side_effects_and_release_bindings",
        )

    def test_mutation_same_sha_promotion_is_killed(self) -> None:
        self._killed(
            [("        or existing[\"releaseSha\"] != request[\"releaseSha\"]\n", "        or False\n")],
            "tests.finalization.test_finalization.FinalizationContracts.test_same_sha_promotion_plan_and_matching_retry_are_idempotent",
        )


if __name__ == "__main__":
    unittest.main()
