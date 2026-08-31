#!/usr/bin/env python3
"""Run watcher contracts and generate a deterministic, redacted evidence file."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from gkd_watchdog.constants import (
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    SCHEMA_VERSION,
)
from gkd_watchdog.model import canonical_json
from probes.multiagentv2.native_probe import capture
from gkd_task.results import CanonicalResultError, select_canonical_results
from tests.contract_catalog import WATCHDOG_CONTRACT_TEST_IDS, validate_contract_coverage


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.success_ids: set[str] = set()

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self.success_ids.add(test.id())


def _tool_timeout_surface(codex: str) -> int:
    result = subprocess.run(
        (
            codex,
            "-c",
            'mcp_servers.gkd_watchdog.command="true"',
            "-c",
            "mcp_servers.gkd_watchdog.tool_timeout_sec=43200",
            "mcp",
            "list",
            "--json",
        ),
        shell=False,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    value = json.loads(result.stdout)
    servers = value if isinstance(value, list) else value.get("mcp_servers", [])
    entry = next(item for item in servers if item.get("name") == "gkd_watchdog")
    timeout = entry.get("tool_timeout_sec")
    if timeout != 43_200:
        raise RuntimeError("MCP tool timeout surface changed")
    return int(timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()

    suite = unittest.defaultTestLoader.discover(
        "tests/watchdog", pattern="test_*.py", top_level_dir="."
    )
    runner = unittest.TextTestRunner(
        verbosity=2,
        resultclass=RecordingResult,
        warnings="error",
    )
    test_ids = sorted(test.id() for test in _flatten(suite))
    canonical_selection = None
    if args.canonical_results is None:
        result = runner.run(suite)
        if not result.wasSuccessful():
            return 1
        success_ids = result.success_ids
    else:
        try:
            canonical_selection = select_canonical_results(
                args.canonical_results,
                "watcher-core-and-live-negative",
                Path(__file__).resolve().parents[2],
                test_ids,
                test_ids,
            )
        except CanonicalResultError as error:
            print(canonical_json({"error": error.code, "status": "error"}), file=sys.stderr, end="")
            return 2
        success_ids = {item["id"] for item in canonical_selection["tests"]}
    validate_contract_coverage(WATCHDOG_CONTRACT_TEST_IDS, success_ids)
    contracts = {
        contract: {
            "status": "pass",
            "tests": list(contract_test_ids),
            "result": {
                "headSha": canonical_selection["headSha"] if canonical_selection is not None else None,
                "resultDigest": canonical_selection["resultDigest"] if canonical_selection is not None else None,
                "scope": "watcher-core-and-live-negative",
            },
        }
        for contract, contract_test_ids in WATCHDOG_CONTRACT_TEST_IDS.items()
    }

    runtime = capture("codex")
    codex_version = runtime["codexVersion"]
    schema_digest = runtime["protocol"]["schemaDigestSha256"]
    if codex_version != EXPECTED_CODEX_VERSION:
        raise RuntimeError("Codex version changed")
    if schema_digest != EXPECTED_SCHEMA_DIGEST:
        raise RuntimeError("app-server schema digest changed")
    if runtime["configuration"]["model"] != "gpt-5.6-sol":
        raise RuntimeError("declared model changed")
    if runtime["configuration"]["reasoningEffort"] != "xhigh":
        raise RuntimeError("declared reasoning effort changed")

    test_ids = sorted(success_ids)
    evidence = {
        "schemaVersion": SCHEMA_VERSION,
        "task": "GKD-M-1B",
        "outcome": "core_ready_for_live_gate",
        "runtime": {
            "codexVersion": codex_version,
            "declaredModel": runtime["configuration"]["model"],
            "declaredReasoningEffort": runtime["configuration"][
                "reasoningEffort"
            ],
            "schemaDigestSha256": schema_digest,
            "mcpToolTimeoutSec": _tool_timeout_surface("codex"),
            "evidenceClass": "declaration_not_live_connection",
        },
        "tests": {
            "count": len(test_ids),
            "idDigestSha256": hashlib.sha256(
                "\n".join(test_ids).encode("utf-8")
            ).hexdigest(),
        },
        "contracts": contracts,
        "security": {
            "conversationBodyStored": False,
            "rawPayloadStored": False,
            "rawCommandStored": False,
            "fullPathStored": False,
            "transcriptStored": False,
        },
        "liveD2Claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(canonical_json({"outcome": evidence["outcome"], "tests": len(test_ids)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
