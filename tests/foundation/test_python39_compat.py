from __future__ import annotations

import ast
from datetime import date, datetime, time, timezone
import io
import json
from pathlib import Path
import unittest
from unittest import mock

import gkd_toml
from gkd_toml import _parser as fallback_toml
from gkd_task import cli as task_cli


ROOT = Path(__file__).resolve().parents[2]
FACADE = ROOT / "canonical" / "payload" / "lib" / "gkd_toml" / "__init__.py"
SCANNED_ROOTS = (
    ROOT / "canonical" / "payload",
    ROOT / "probes",
    ROOT / "src",
    ROOT / "tests",
)
TOML_DOCUMENT = """
title = "GKD"
released = 2024-01-02
at = 2024-01-02T03:04:05Z
clock = 03:04:05
escaped = "line\\nquote: \\""
ports = [8000, 8001, 8002]

[owner]
name = "Tom \\"D.\\" Preston-Werner"

[database]
enabled = true
data = [["delta", "phi"], [3.14]]
"""


class _Stderr:
    def __init__(self) -> None:
        self.buffer = io.BytesIO()


class Python39CompatibilityContracts(unittest.TestCase):
    def test_toml_facade_and_fallback_preserve_complete_toml_values(self) -> None:
        expected = {
            "title": "GKD",
            "released": date(2024, 1, 2),
            "at": datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            "clock": time(3, 4, 5),
            "escaped": "line\nquote: \"",
            "ports": [8000, 8001, 8002],
            "owner": {"name": 'Tom "D." Preston-Werner'},
            "database": {"enabled": True, "data": [["delta", "phi"], [3.14]]},
        }
        for loader in (gkd_toml.loads, fallback_toml.loads):
            with self.subTest(loader=loader.__module__):
                self.assertEqual(expected, loader(TOML_DOCUMENT))
        for malformed in ("value = [1,", "value = \\q"):
            with self.subTest(malformed=malformed):
                with self.assertRaises(gkd_toml.TOMLDecodeError):
                    gkd_toml.loads(malformed)
                with self.assertRaises(fallback_toml.TOMLDecodeError):
                    fallback_toml.loads(malformed)

    def test_upstream_license_and_inventory_are_shipped(self) -> None:
        package_root = FACADE.parent
        self.assertIn("MIT License", (package_root / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("Taneli Hukkinen", FACADE.read_text(encoding="utf-8"))
        source = gkd_toml.loads((ROOT / "canonical" / "source.toml").read_text(encoding="utf-8"))
        declared = {
            record["source"]
            for component in source["components"]
            for record in component["files"]
        }
        expected = {
            f"payload/lib/gkd_toml/{name}"
            for name in ("LICENSE", "__init__.py", "_parser.py", "_re.py", "_types.py", "py.typed")
        }
        self.assertTrue(expected.issubset(declared))

    def test_reachable_sources_do_not_use_newer_python_apis(self) -> None:
        direct_tomllib_imports = []
        strict_zip = []
        dataclass_slots = []
        for root in SCANNED_ROOTS:
            for path in root.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        if any(name.name == "tomllib" for name in node.names):
                            direct_tomllib_imports.append(path)
                    elif isinstance(node, ast.ImportFrom) and node.module == "tomllib":
                        direct_tomllib_imports.append(path)
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id == "zip" and any(keyword.arg == "strict" for keyword in node.keywords):
                            strict_zip.append(path)
                        if node.func.id == "dataclass" and any(keyword.arg == "slots" for keyword in node.keywords):
                            dataclass_slots.append(path)
        self.assertEqual([FACADE], sorted(set(direct_tomllib_imports)))
        self.assertEqual([], strict_zip)
        self.assertEqual([], dataclass_slots)

    def test_task_cli_keeps_internal_errors_distinct_from_filesystem_errors(self) -> None:
        stderr = _Stderr()
        with mock.patch.object(task_cli, "_dispatch", side_effect=TypeError("compatibility defect")), mock.patch.object(task_cli.sys, "stderr", stderr):
            result = task_cli.main(
                [
                    "status",
                    "--repository", "example.test/gkd/repository",
                    "--task-id", "TASK-X",
                    "--task-branch", "task/x",
                    "--task-path", "tasks/x",
                    "--runtime-root", "runtime",
                ]
            )
        self.assertEqual(2, result)
        self.assertEqual(
            {"status": "error", "error": "INTERNAL_ERROR"},
            json.loads(stderr.buffer.getvalue()),
        )


if __name__ == "__main__":
    unittest.main()
