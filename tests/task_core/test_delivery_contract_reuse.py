from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from gkd_task.results import write_manifest, write_scope_result
from tests.contract_catalog import DELIVERY_CONTRACT_TEST_IDS
from tests.delivery_contract import run_contracts


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class DeliveryContractResultReuseContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[2]
        self.head = subprocess.check_output(("git", "-C", str(self.repository), "rev-parse", "HEAD"), text=True).strip()
        suite = unittest.defaultTestLoader.discover(
            str(self.repository / "tests" / "task_core"),
            pattern="test_*.py",
            top_level_dir=str(self.repository),
        )
        self.task_core_ids = sorted(test.id() for test in _flatten(suite))
        self.contract_ids = list(DELIVERY_CONTRACT_TEST_IDS["delivery_document_binding"])

    def _write_results(self, root: Path, tests: list[dict[str, str]], head: str | None = None) -> dict[str, object]:
        result_head = head or self.head
        write_manifest(root / "manifest.json", base_sha=self.head, head_sha=result_head, verifier_digest="a" * 64)
        return write_scope_result(
            root / "task-core.json",
            base_sha=self.head,
            head_sha=result_head,
            scope="task-core",
            tests=tests,
            verifier_digest="a" * 64,
        )

    def _invoke(self, output: Path, temporary: Path, protected: Path, results: Path) -> int:
        arguments = [
            "run_contracts.py",
            "--output",
            str(output),
            "--temporary-root",
            str(temporary),
            "--protected-root",
            str(protected),
            "--implementation-head",
            self.head,
            "--canonical-results",
            str(results),
        ]
        previous_argv = sys.argv
        previous_tempdir = run_contracts.tempfile.tempdir
        previous_stdout = sys.stdout
        previous_stderr = sys.stderr
        captured_stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        captured_stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        try:
            sys.argv = arguments
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr
            return run_contracts.main()
        finally:
            sys.argv = previous_argv
            run_contracts.tempfile.tempdir = previous_tempdir
            sys.stdout = previous_stdout
            sys.stderr = previous_stderr

    def test_canonical_results_reuse_selected_delivery_contracts_without_running_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "results"
            results.mkdir()
            temporary_root = root / "temporary"
            protected = root / "protected"
            output_parent = root / "output"
            for path in (temporary_root, protected, output_parent):
                path.mkdir()
            canonical = self._write_results(results, [{"id": test_id, "status": "pass"} for test_id in self.task_core_ids])

            with mock.patch.object(run_contracts.unittest.TextTestRunner, "run", side_effect=AssertionError("focused suite ran")) as run:
                self.assertEqual(0, self._invoke(output_parent / "evidence.json", temporary_root, protected, results))
            run.assert_not_called()

            evidence = json.loads((output_parent / "evidence.json").read_text(encoding="utf-8"))
            binding = evidence["contractResults"]["delivery_document_binding"]
            self.assertEqual(self.contract_ids, binding["testIds"])
            self.assertEqual(canonical["resultDigest"], binding["resultDigest"])
            self.assertEqual(self.head, binding["headSha"])

    def test_canonical_results_reject_missing_or_failed_delivery_test(self) -> None:
        cases = (
            [
                {"id": test_id, "status": "pass"}
                for test_id in self.task_core_ids
                if test_id != self.contract_ids[0]
            ],
            [
                {"id": test_id, "status": "fail" if test_id == self.contract_ids[0] else "pass"}
                for test_id in self.task_core_ids
            ],
        )
        for tests in cases:
            with self.subTest(tests=tests[0]["id"]):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    results = root / "results"
                    results.mkdir()
                    temporary_root = root / "temporary"
                    protected = root / "protected"
                    output_parent = root / "output"
                    for path in (temporary_root, protected, output_parent):
                        path.mkdir()
                    self._write_results(results, tests)

                    with mock.patch.object(run_contracts.unittest.TextTestRunner, "run", side_effect=AssertionError("focused suite ran")):
                        self.assertEqual(2, self._invoke(output_parent / "evidence.json", temporary_root, protected, results))


if __name__ == "__main__":
    unittest.main()
