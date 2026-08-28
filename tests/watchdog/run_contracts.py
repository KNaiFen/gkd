#!/usr/bin/env python3
"""Run watcher contracts and generate a deterministic, redacted evidence file."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from gkd_watchdog.constants import (
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    SCHEMA_VERSION,
)
from gkd_watchdog.model import canonical_json
from probes.multiagentv2.native_probe import capture
from gkd_task.results import CanonicalResultError, load_canonical_results


CONTRACT_TEST_SUFFIXES = {
    "runtime_evidence_binding": (
        "WatchRequestTests.test_rejects_well_formed_but_unapproved_runtime_digest",
        "McpAdapterTests.test_unapproved_runtime_digest_never_constructs_watch_service",
        "WatchRequestTests.test_direct_request_construction_cannot_bypass_identity_invariants",
    ),
    "thread_ownership_binding": (
        "WatchServiceTests.test_thread_ownership_mismatch_fails_before_control",
        "WatchServiceTests.test_thread_ownership_drift_blocks_interrupt_and_steer",
        "WatchServiceTests.test_parent_read_remote_failure_is_protocol_not_child_abnormal",
    ),
    "interrupt_confirmation": (
        "WatchServiceTests.test_system_error_interrupts_child_then_steers_bound_parent",
        "WatchServiceTests.test_interrupt_without_bound_terminal_confirmation_never_steers",
    ),
    "steer_error_classification": (
        "WatchServiceTests.test_wrong_expected_turn_is_rejected_once_without_fallback",
        "WatchServiceTests.test_non_expected_steer_errors_remain_protocol_errors",
    ),
    "cancellation_and_eof_shutdown": (
        "WatchServiceTests.test_cancellation_interrupt_failure_is_terminal_protocol_error",
        "WatchServiceTests.test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed",
        "McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
    ),
    "credential_identity_rejection": (
        "WatchRequestTests.test_rejects_credential_shaped_values_in_every_echoed_id",
    ),
    "deadline_single_terminal": (
        "WatchServiceTests.test_twelve_hour_deadline_is_single_and_hourly_ticks_are_silent",
    ),
    "normal_terminal_no_steer": (
        "WatchServiceTests.test_normal_terminal_returns_immediately_without_steer",
    ),
    "active_stale_is_healthy": (
        "WatchServiceTests.test_stale_active_child_remains_healthy_across_ticks",
    ),
    "abnormal_classification_and_order": (
        "WatchServiceTests.test_system_error_interrupts_child_then_steers_bound_parent",
        "WatchServiceTests.test_failed_terminal_steers_without_interrupting_terminal_child",
        "WatchServiceTests.test_explicit_remote_errored_is_abnormal",
        "WatchServiceTests.test_not_found_is_abnormal_and_does_not_interrupt_parent",
    ),
    "expected_turn_cas": (
        "WatchServiceTests.test_wrong_expected_turn_is_rejected_once_without_fallback",
        "AppServerClientTests.test_actual_expected_turn_rejection_is_single_and_redacted",
    ),
    "bounded_protocol_failures": (
        "AppServerClientTests.test_eof_malformed_unknown_and_duplicate_responses_terminate",
        "AppServerClientTests.test_response_timeout_is_bounded",
        "AppServerClientTests.test_start_failure_maps_to_terminal_orchestrator_error",
        "McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
    ),
    "pre_side_effect_validation": (
        "WatchRequestTests.test_rejects_unknown_fields_before_side_effects",
        "WatchRequestTests.test_rejects_wrong_types_limits_and_digest",
        "McpAdapterTests.test_unapproved_runtime_digest_never_constructs_watch_service",
        "AppServerClientTests.test_schema_drift_stops_before_app_server_spawn",
    ),
    "cancellation_scope": (
        "WatchServiceTests.test_cancellation_interrupts_only_bound_child_and_never_parent",
        "WatchServiceTests.test_cancellation_interrupt_failure_is_terminal_protocol_error",
        "WatchServiceTests.test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed",
        "McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
    ),
    "concurrency_and_single_writer": (
        "WatchServiceTests.test_two_concurrent_instances_keep_identity_and_calls_separate",
        "AppServerClientTests.test_two_subprocess_clients_keep_rpc_ids_and_identity_isolated",
        "AppServerClientTests.test_single_client_serializes_concurrent_writers_and_ids",
        "McpAdapterTests.test_active_watch_capacity_is_bounded_before_service_construction",
    ),
    "mcp_framing_and_silence": (
        "McpAdapterTests.test_subprocess_initialize_list_call_and_success_framing",
        "McpAdapterTests.test_subprocess_invalid_request_uses_jsonrpc_error_without_side_effect",
        "McpAdapterTests.test_health_ticks_emit_no_progress_result_or_log_before_cancel",
        "McpAdapterTests.test_malformed_mcp_json_uses_parse_error_frame",
        "McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
    ),
    "sensitive_data_containment": (
        "AppServerClientTests.test_actual_subprocess_normal_terminal_drops_body_from_transcript",
        "AppServerClientTests.test_untrusted_notification_method_and_keys_are_redacted_in_transcript",
        "WatchRequestTests.test_rejects_credential_shaped_values_in_every_echoed_id",
    ),
}


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.success_ids: set[str] = set()

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self.success_ids.add(test.id())


def _matching(success_ids: set[str], suffix: str) -> str:
    matches = sorted(test_id for test_id in success_ids if test_id.endswith(suffix))
    if len(matches) != 1:
        raise RuntimeError(f"contract test mapping mismatch: {suffix}")
    return matches[0]


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
    if args.canonical_results is None:
        result = runner.run(suite)
        if not result.wasSuccessful():
            return 1
        success_ids = result.success_ids
    else:
        try:
            load_canonical_results(args.canonical_results, "watcher-core-and-live-negative", Path(__file__).resolve().parents[2], test_ids)
        except CanonicalResultError as error:
            print(canonical_json({"error": error.code, "status": "error"}), file=sys.stderr, end="")
            return 2
        success_ids = set(test_ids)
    contracts = {}
    for contract, suffixes in CONTRACT_TEST_SUFFIXES.items():
        contracts[contract] = {
            "status": "pass",
            "tests": [_matching(success_ids, suffix) for suffix in suffixes],
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
