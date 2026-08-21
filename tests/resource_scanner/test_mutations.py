from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE = Path("canonical/payload/lib/gkd_ci")


class ResourceMutationContracts(unittest.TestCase):
    def killed(self, relative: str, old: str, new: str, test_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-resource-mutant-") as temporary:
            package = Path(temporary) / "gkd_ci"
            shutil.copytree(SOURCE, package)
            path = package / relative
            text = path.read_text(encoding="utf-8")
            self.assertIn(old, text)
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            result = subprocess.run(
                (sys.executable, "-B", "-m", "unittest", test_name, "-q"),
                cwd=Path(__file__).resolve().parents[2],
                env={"PYTHONPATH": f"{temporary}:canonical/payload/lib:."},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)

    def test_mutation_unknown_build_gate_is_killed(self) -> None:
        self.killed(
            "resources.py",
            '    elif artifact_class == "build-or-unknown":\n        decision = "blocked"\n',
            '    elif artifact_class == "build-or-unknown":\n        decision = "allow"\n',
            "tests.resource_scanner.test_resources.ResourceContracts.test_unknown_build_is_terminal_and_cleanup_does_not_change_it",
        )

    def test_mutation_scanner_terminal_gate_is_killed(self) -> None:
        self.killed(
            "scanner.py",
            '        "outcome": "terminal" if findings else "clean",\n',
            '        "outcome": "clean",\n',
            "tests.resource_scanner.test_scanner.ScannerContracts.test_credential_is_redacted_and_terminal",
        )


if __name__ == "__main__":
    unittest.main()
