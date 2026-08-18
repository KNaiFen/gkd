from __future__ import annotations

import json
import os
from pathlib import Path
import select
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_DIR = REPO_ROOT / "probes" / "app-server-watcher"
sys.path.insert(0, str(LIVE_DIR))

from gkd_watchdog.constants import EXPECTED_SCHEMA_DIGEST, MAX_WAIT_MS
from gkd_watchdog.jsonrpc import AppServerMalformedJSON, JsonRpcClient
from live_probe import build_evidence
from live_support import (
    LIVE_SCHEMA_VERSION,
    LiveBinding,
    LiveProbeError,
    NotificationTrace,
    assert_evidence_safe,
    normalized_digest,
    read_binding,
)


def valid_state(**overrides):
    value = {
        "schemaVersion": LIVE_SCHEMA_VERSION,
        "scenario": "normal",
        "taskId": "gkd-m1c-test",
        "offerId": "offer-test",
        "sessionId": "session-test",
        "parentThreadId": "parent-thread",
        "parentTurnId": "parent-turn",
        "childThreadId": "child-thread",
        "childTurnId": "child-turn",
        "wrongParentTurnId": "wrong-parent-turn",
        "maxWaitMs": MAX_WAIT_MS,
        "healthIntervalMs": 200,
    }
    value.update(overrides)
    return value


def terminal_notification():
    return {
        "method": "turn/completed",
        "params": {
            "threadId": "child-thread",
            "turn": {
                "id": "child-turn",
                "status": "completed",
                "items": [{"type": "agentMessage", "text": "private body"}],
            },
            "Authorization": "Bearer fixture-secret",
            "path": "/Users/private/session.jsonl",
        },
    }


def empty_scenarios(cleanup: bool = True):
    return {
        scenario: {
            "assertions": {
                "cleanupComplete": cleanup,
                "exactBindingObserved": False,
                "liveMcpCallObserved": False,
            },
            "parentTrace": {},
        }
        for scenario in ("normal", "abnormal", "cas_reject", "orchestrator_failure")
    }


def m1b_contracts():
    return {
        "tests": 47,
        "status": "pass",
        "testIdDigestSha256": "2e61a1c79e02515de194ac30c9999de0f75f60bca1a1fac207d909f75e19b965",
        "fakeClockTwelveHourSingleDeadline": "pass",
    }


class LiveSupportTests(unittest.TestCase):
    def test_real_app_server_envelope_without_jsonrpc_is_accepted(self) -> None:
        class ShapeTransport:
            def __init__(self) -> None:
                self.response = {"id": 1, "result": {}}

            def write_message(self, message) -> None:
                self.request = message

            def read_message(self, timeout_ms):
                response, self.response = self.response, None
                return response

            def close(self) -> None:
                pass

        client = JsonRpcClient(ShapeTransport())
        self.assertEqual(client.request("initialize", {}, timeout_ms=10), {})

    def test_missing_jsonrpc_is_accepted_but_explicit_null_is_rejected(self) -> None:
        class ShapeTransport:
            def __init__(self, response) -> None:
                self.response = response

            def write_message(self, message) -> None:
                pass

            def read_message(self, timeout_ms):
                response, self.response = self.response, None
                return response

            def close(self) -> None:
                pass

        null_response = JsonRpcClient(
            ShapeTransport({"jsonrpc": None, "id": 1, "result": {}})
        )
        with self.assertRaises(AppServerMalformedJSON):
            null_response.request("initialize", {}, timeout_ms=10)

        missing_notification = JsonRpcClient(
            ShapeTransport({"method": "turn/completed", "params": {}})
        )
        self.assertEqual(
            missing_notification.next_notification(10),
            {"method": "turn/completed", "params": {}},
        )

        null_notification = JsonRpcClient(
            ShapeTransport(
                {"jsonrpc": None, "method": "turn/completed", "params": {}}
            )
        )
        with self.assertRaises(AppServerMalformedJSON):
            null_notification.next_notification(10)

    def test_identity_ambiguity_fails_closed(self) -> None:
        with self.assertRaises(LiveProbeError):
            LiveBinding.parse(valid_state(childThreadId="parent-thread"))
        with self.assertRaises(LiveProbeError):
            LiveBinding.parse(valid_state(extra="unexpected"))

    def test_state_schema_and_version_drift_fail_closed(self) -> None:
        with self.assertRaisesRegex(LiveProbeError, "state_version_mismatch"):
            LiveBinding.parse(valid_state(schemaVersion=2))
        with self.assertRaisesRegex(LiveProbeError, "state_max_wait_mismatch"):
            LiveBinding.parse(valid_state(maxWaitMs=1_000))

    def test_cas_request_uses_only_wrong_expected_turn(self) -> None:
        binding = LiveBinding.parse(valid_state(scenario="cas_reject"))
        request = binding.watch_request()
        self.assertEqual(request.expected_parent_turn_id, "wrong-parent-turn")
        self.assertNotEqual(request.expected_parent_turn_id, binding.parent_turn_id)

    def test_raw_body_is_not_retained_and_leak_scanner_rejects_it(self) -> None:
        trace = NotificationTrace()
        reduced = trace.accept(terminal_notification())
        serialized = json.dumps({"reduced": reduced, "summary": trace.summary()})
        self.assertNotIn("private body", serialized)
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("/Users/private", serialized)
        with self.assertRaisesRegex(LiveProbeError, "evidence_sensitive_value"):
            assert_evidence_safe(terminal_notification())

    def test_duplicate_terminal_is_rejected(self) -> None:
        trace = NotificationTrace()
        trace.accept(terminal_notification())
        with self.assertRaisesRegex(LiveProbeError, "duplicate_terminal"):
            trace.accept(terminal_notification())

    def test_state_wait_timeout_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-live-test-") as root:
            with self.assertRaisesRegex(LiveProbeError, "state_unavailable"):
                read_binding(Path(root) / "missing.json", timeout_seconds=0.05)

    def test_cleanup_failure_forces_unsupported(self) -> None:
        runtime = SimpleNamespace(
            codex_version="0.147.0",
            schema_digest=EXPECTED_SCHEMA_DIGEST,
        )
        evidence = build_evidence(
            runtime=runtime,
            scenarios=empty_scenarios(cleanup=False),
            config_before={"exists": False, "sha256": None, "mtimeNs": None},
            config_after={"exists": False, "sha256": None, "mtimeNs": None},
            temporary_cleanup=True,
            m1b_contracts=m1b_contracts(),
        )
        self.assertEqual(evidence["outcome"], "unsupported")
        self.assertEqual(evidence["gates"]["9_data_and_cleanup"]["status"], "fail")

    def test_unbound_trace_cannot_prove_timeout_or_parent_context(self) -> None:
        runtime = SimpleNamespace(
            codex_version="0.147.0",
            schema_digest=EXPECTED_SCHEMA_DIGEST,
        )
        evidence = build_evidence(
            runtime=runtime,
            scenarios=empty_scenarios(),
            config_before={"exists": False, "sha256": None, "mtimeNs": None},
            config_after={"exists": False, "sha256": None, "mtimeNs": None},
            temporary_cleanup=True,
            m1b_contracts=m1b_contracts(),
        )
        self.assertEqual(
            evidence["gates"]["7_combined_timeout_contract_not_soak"]["status"],
            "fail",
        )
        self.assertEqual(
            evidence["gates"]["8_parent_context_trace"]["status"], "fail"
        )

    def test_normalized_digest_excludes_run_identity(self) -> None:
        first = {
            "schemaVersion": 1,
            "outcome": "unsupported",
            "runtime": {"codexVersion": "0.147.0"},
            "gates": {"gate": {"status": "fail", "reason": "fixed"}},
            "scenarios": {"normal": {"identity": {"x": "a"}, "assertions": {"ok": False}}},
        }
        second = json.loads(json.dumps(first))
        second["scenarios"]["normal"]["identity"]["x"] = "b"
        self.assertEqual(normalized_digest(first), normalized_digest(second))

    def test_normalized_digest_excludes_non_decisive_failed_assertions(self) -> None:
        first = {
            "schemaVersion": 1,
            "outcome": "unsupported",
            "runtime": {},
            "gates": {"gate": {"status": "fail", "reason": "fixed"}},
            "scenarios": {
                "normal": {
                    "status": "fail",
                    "reason": "binding_not_observed",
                    "assertions": {"liveMcpCallObserved": True},
                }
            },
        }
        second = json.loads(json.dumps(first))
        second["scenarios"]["normal"]["assertions"][
            "liveMcpCallObserved"
        ] = False
        second["scenarios"]["normal"]["reason"] = "scenario_no_output_timeout"
        self.assertEqual(normalized_digest(first), normalized_digest(second))

    def test_normalized_digest_binds_gate_security_and_cleanup_facts(self) -> None:
        evidence = {
            "schemaVersion": 1,
            "outcome": "unsupported",
            "runtime": {},
            "m1bContracts": {"tests": 47, "status": "pass"},
            "productionConfig": {"beforeAfterMatch": True},
            "cleanup": {"temporaryDirectoryRemoved": True},
            "security": {"rawAppServerPayloadStored": False},
            "wallClockSoakClaimed": False,
            "gates": {},
            "scenarios": {},
        }
        changed = json.loads(json.dumps(evidence))
        changed["security"]["rawAppServerPayloadStored"] = True
        self.assertNotEqual(normalized_digest(evidence), normalized_digest(changed))
        changed = json.loads(json.dumps(evidence))
        changed["productionConfig"]["beforeAfterMatch"] = False
        self.assertNotEqual(normalized_digest(evidence), normalized_digest(changed))

    def test_all_common_absolute_path_forms_are_rejected(self) -> None:
        for path in (
            "/etc/placeholder",
            "file:///Users/placeholder",
            r"C:\\Users\\placeholder",
            r"\\server\share\placeholder",
        ):
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    LiveProbeError, "evidence_sensitive_value"
                ):
                    assert_evidence_safe({"path": path})


class AdapterSubprocessTests(unittest.TestCase):
    def _line(self, process: subprocess.Popen[str]) -> dict:
        assert process.stdout is not None
        ready, _, _ = select.select([process.stdout.fileno()], [], [], 2.0)
        self.assertTrue(ready, "adapter response timed out")
        line = process.stdout.readline()
        self.assertTrue(line, "adapter closed without response")
        return json.loads(line)

    def test_adapter_rejects_unknown_gate_fields_before_live_side_effect(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-live-adapter-test-") as root:
            directory = Path(root)
            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}",
                    "GKD_LIVE_STATE_PATH": str(directory / "state.json"),
                    "GKD_LIVE_CHILD_STATE_PATH": str(directory / "child-state.json"),
                    "GKD_LIVE_INNER_PID_PATH": str(directory / "inner.pid"),
                    "GKD_LIVE_ADAPTER_PIDS_PATH": str(directory / "adapter-pids.txt"),
                    "GKD_LIVE_HEALTH_PATH": str(directory / "health.txt"),
                    "GKD_LIVE_WATCH_TRACE_PATH": str(directory / "trace.json"),
                    "GKD_LIVE_WATCH_RESULT_PATH": str(directory / "result.json"),
                    "GKD_LIVE_HOLD_READY_PATH": str(directory / "ready.txt"),
                    "GKD_LIVE_TASK_ID": "gkd-m1c-test",
                    "GKD_LIVE_OFFER_ID": "offer-test",
                    "GKD_LIVE_WRONG_PARENT_TURN_ID": "wrong-parent-turn",
                    "GKD_LIVE_SCENARIO": "normal",
                }
            )
            process = subprocess.Popen(
                (sys.executable, str(LIVE_DIR / "mcp_adapter.py")),
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            try:
                assert process.stdin is not None
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "gkd_live_gate",
                        "arguments": {"scenario": "normal", "command": "unsafe"},
                        "_meta": {},
                    },
                }
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                response = self._line(process)
            finally:
                if process.stdin is not None:
                    process.stdin.close()
                process.wait(timeout=2)
            stderr = process.stderr.read() if process.stderr is not None else ""
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            self.assertEqual(response["error"]["code"], -32602)
            self.assertEqual(response["error"]["message"], "invalid live scenario")
            self.assertFalse((directory / "inner.pid").exists())
            self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
