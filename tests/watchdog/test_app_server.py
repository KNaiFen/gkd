from __future__ import annotations

from collections import deque
from pathlib import Path
import sys
import threading
import unittest

from gkd_watchdog.jsonrpc import (
    AppServerDuplicateResponse,
    AppServerEOF,
    AppServerMalformedJSON,
    AppServerResponseTimeout,
    AppServerStartError,
    AppServerUnknownResponse,
    JsonRpcClient,
    SubprocessTransport,
)
from gkd_watchdog.runtime import (
    AppServerFactory,
    StaticRuntimeVerifier,
)
from gkd_watchdog.watcher import WatchService

from tests.watchdog.helpers import parsed_request


FAKE_SERVER = Path(__file__).with_name("fake_app_server.py")


def client_for(scenario: str) -> JsonRpcClient:
    return JsonRpcClient(
        SubprocessTransport((sys.executable, str(FAKE_SERVER), scenario))
    )


class FixedResolver:
    def __init__(self, command) -> None:
        self.command = tuple(command)

    def resolve(self):
        return self.command


class AutoResponseTransport:
    def __init__(self) -> None:
        self.responses = deque()
        self.writes = []
        self.in_write = False
        self.overlap = False
        self.lock = threading.Lock()

    def write_message(self, message) -> None:
        with self.lock:
            if self.in_write:
                self.overlap = True
            self.in_write = True
            self.writes.append(message)
            self.responses.append(
                {"jsonrpc": "2.0", "id": message["id"], "result": {}}
            )
            self.in_write = False

    def read_message(self, timeout_ms):
        return self.responses.popleft() if self.responses else None

    def close(self) -> None:
        pass


class AppServerClientTests(unittest.TestCase):
    def test_actual_subprocess_normal_terminal_drops_body_from_transcript(self) -> None:
        client = client_for("normal")
        try:
            client.request("initialize", {"clientInfo": {"name": "test"}})
            result = WatchService(lambda _request, _cancellation: client).watch(parsed_request())
            serialized = repr(client.transcript) + repr(result.to_dict())
        finally:
            client.close()

        self.assertEqual(result.outcome, "normal_terminal")
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("fixture-cookie-secret", serialized)
        self.assertNotIn("field-secret", serialized)
        self.assertNotIn("BEGIN PRIVATE KEY", serialized)
        self.assertNotIn("agentMessage", serialized)
        self.assertNotIn("/Users/", serialized)

    def test_actual_subprocess_system_error_orders_interrupt_before_steer(self) -> None:
        client = client_for("system_error")
        try:
            client.request("initialize", {"clientInfo": {"name": "test"}})
            result = WatchService(lambda _request, _cancellation: client).watch(parsed_request())
            methods = [
                entry.get("method")
                for entry in client.transcript
                if entry.get("direction") == "request"
            ]
        finally:
            client.close()

        self.assertEqual(result.outcome, "abnormal_child")
        self.assertEqual(
            methods,
            [
                "initialize",
                "thread/read",
                "thread/read",
                "thread/read",
                "thread/read",
                "turn/interrupt",
                "thread/read",
                "thread/read",
                "turn/steer",
            ],
        )
        self.assertNotIn("fixture-secret", repr(client.transcript) + repr(result.to_dict()))

    def test_actual_expected_turn_rejection_is_single_and_redacted(self) -> None:
        client = client_for("steer_rejected")
        try:
            client.request("initialize", {"clientInfo": {"name": "test"}})
            result = WatchService(lambda _request, _cancellation: client).watch(parsed_request())
            transcript = client.transcript
        finally:
            client.close()

        methods = [
            entry.get("method")
            for entry in transcript
            if entry.get("direction") == "request"
        ]
        self.assertEqual(result.outcome, "parent_steer_rejected")
        self.assertEqual(methods.count("turn/steer"), 1)
        self.assertNotIn("turn/start", methods)
        serialized = repr(transcript) + repr(result.to_dict())
        self.assertNotIn("fixture path", serialized)
        self.assertNotIn("/Users/private", serialized)
        self.assertNotIn("token=secret", serialized)

    def test_eof_malformed_unknown_and_duplicate_responses_terminate(self) -> None:
        cases = (
            ("eof", AppServerEOF),
            ("malformed", AppServerMalformedJSON),
            ("unknown_id", AppServerUnknownResponse),
        )
        for scenario, error in cases:
            with self.subTest(scenario=scenario):
                client = client_for(scenario)
                try:
                    with self.assertRaises(error):
                        client.request("initialize", {}, timeout_ms=500)
                finally:
                    client.close()

        client = client_for("duplicate")
        try:
            client.request("initialize", {}, timeout_ms=500)
            with self.assertRaises(AppServerDuplicateResponse):
                client.next_notification(500)
        finally:
            client.close()

    def test_response_timeout_is_bounded(self) -> None:
        client = client_for("silent")
        try:
            with self.assertRaises(AppServerResponseTimeout):
                client.request("initialize", {}, timeout_ms=50)
        finally:
            client.close()

    def test_start_failure_is_fixed_error_without_path(self) -> None:
        with self.assertRaises(AppServerStartError) as raised:
            SubprocessTransport(("/definitely/not/a/real/gkd-command",))
        self.assertNotIn("/definitely", str(raised.exception))

    def test_start_failure_maps_to_terminal_orchestrator_error(self) -> None:
        factory = AppServerFactory(
            FixedResolver(("/definitely/not/a/real/gkd-command",)),
            StaticRuntimeVerifier(),
        )
        result = WatchService(factory).watch(parsed_request(maxWaitMs=1))
        self.assertEqual(result.outcome, "orchestrator_error")
        self.assertEqual(result.reason, "app_server_start_failed")
        self.assertNotIn("/definitely", repr(result.to_dict()))

    def test_schema_drift_stops_before_app_server_spawn(self) -> None:
        calls = []

        def forbidden_transport(argv):
            calls.append(tuple(argv))
            raise AssertionError("transport must not start")

        factory = AppServerFactory(
            FixedResolver(("codex",)),
            StaticRuntimeVerifier("schema_digest_mismatch"),
            transport_factory=forbidden_transport,
        )
        result = WatchService(factory).watch(parsed_request(maxWaitMs=1))

        self.assertEqual(result.outcome, "protocol_error")
        self.assertEqual(result.reason, "schema_digest_mismatch")
        self.assertEqual(calls, [])

    def test_runtime_factory_appends_only_fixed_app_server_argv(self) -> None:
        captured = []

        class StopAfterCapture(Exception):
            pass

        def capture(argv):
            captured.append(tuple(argv))
            raise StopAfterCapture()

        factory = AppServerFactory(
            FixedResolver(("trusted-codex", "fixed-prefix")),
            StaticRuntimeVerifier(),
            transport_factory=capture,
        )
        with self.assertRaises(StopAfterCapture):
            factory(parsed_request())
        self.assertEqual(captured, [("trusted-codex", "fixed-prefix", "app-server")])

    def test_single_client_serializes_concurrent_writers_and_ids(self) -> None:
        transport = AutoResponseTransport()
        client = JsonRpcClient(transport)
        errors = []

        def call() -> None:
            try:
                client.request("thread/read", {"threadId": "bound", "includeTurns": False})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=call) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertFalse(transport.overlap)
        self.assertEqual([message["id"] for message in transport.writes], [1, 2])
        self.assertTrue(
            all(
                message["params"]["includeTurns"] is False
                for message in transport.writes
            )
        )

    def test_two_subprocess_clients_keep_rpc_ids_and_identity_isolated(self) -> None:
        results = {}
        transcripts = {}

        def run(name: str) -> None:
            client = client_for("normal")
            try:
                client.request("initialize", {"clientInfo": {"name": "test"}})
                request = parsed_request(
                    taskId=f"task-{name}",
                    offerId=f"offer-{name}",
                )
                results[name] = WatchService(lambda _request, _cancellation: client).watch(request)
                transcripts[name] = client.transcript
            finally:
                client.close()

        threads = [threading.Thread(target=run, args=(name,)) for name in ("a", "b")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(results["a"].request.task_id, "task-a")
        self.assertEqual(results["b"].request.task_id, "task-b")
        for name in ("a", "b"):
            request_ids = [
                entry["id"]
                for entry in transcripts[name]
                if entry.get("direction") == "request"
            ]
            self.assertEqual(request_ids, [1, 2, 3])

    def test_untrusted_notification_method_and_keys_are_redacted_in_transcript(self) -> None:
        class NotificationTransport:
            def write_message(self, message):
                raise AssertionError("no request expected")

            def read_message(self, timeout_ms):
                return {
                    "jsonrpc": "2.0",
                    "method": "token=method-secret",
                    "params": {
                        "token=field-secret": "private",
                        "threadId": "bound",
                    },
                }

            def close(self):
                pass

        client = JsonRpcClient(NotificationTransport())
        notification = client.next_notification(10)
        serialized = repr(client.transcript)

        self.assertEqual(notification["method"], "token=method-secret")
        self.assertEqual(client.transcript[0]["method"], "other_notification")
        self.assertEqual(client.transcript[0]["fieldNames"], ["threadId"])
        self.assertNotIn("method-secret", serialized)
        self.assertNotIn("field-secret", serialized)


if __name__ == "__main__":
    unittest.main()
