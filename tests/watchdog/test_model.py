from __future__ import annotations

from dataclasses import replace
import unittest

from gkd_watchdog.constants import MAX_WAIT_MS
from gkd_watchdog.model import RequestValidationError, WATCH_REQUEST_SCHEMA, WatchRequest

from tests.watchdog.helpers import valid_request


class WatchRequestTests(unittest.TestCase):
    def test_accepts_exact_versioned_request(self) -> None:
        request = WatchRequest.parse(valid_request())
        self.assertEqual(request.schema_version, 1)
        self.assertEqual(request.max_wait_ms, MAX_WAIT_MS)
        self.assertEqual(
            WATCH_REQUEST_SCHEMA["properties"]["taskId"]["pattern"],
            "^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
        )

    def test_rejects_unknown_fields_before_side_effects(self) -> None:
        for field, value in (
            ("command", "sh -c arbitrary"),
            ("path", "/Users/private/bin/codex"),
            ("steerText", "arbitrary natural language"),
            ("Authorization", "Bearer fixture-secret"),
        ):
            with self.subTest(field=field), self.assertRaises(RequestValidationError):
                WatchRequest.parse(valid_request(**{field: value}))

    def test_rejects_invalid_ids_and_parent_child_alias(self) -> None:
        invalid = (
            {"taskId": ""},
            {"offerId": "x" * 129},
            {"sessionId": "token=value"},
            {"parentThreadId": "child-thread-1"},
        )
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(
                RequestValidationError
            ):
                WatchRequest.parse(valid_request(**override))

    def test_rejects_wrong_types_limits_and_digest(self) -> None:
        invalid = (
            {"schemaVersion": 2},
            {"schemaVersion": True},
            {"maxWaitMs": MAX_WAIT_MS + 1},
            {"maxWaitMs": 0},
            {"healthIntervalMs": 0},
            {"healthIntervalMs": 3_600_001},
            {"runtimeEvidenceDigest": ""},
            {"runtimeEvidenceDigest": "A" * 64},
        )
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(
                RequestValidationError
            ):
                WatchRequest.parse(valid_request(**override))

    def test_rejects_well_formed_but_unapproved_runtime_digest(self) -> None:
        with self.assertRaises(RequestValidationError):
            WatchRequest.parse(valid_request(runtimeEvidenceDigest="0" * 64))

    def test_rejects_credential_shaped_values_in_every_echoed_id(self) -> None:
        credentials = (
            ("github_classic", "ghp_" + "A" * 36),
            ("github_fine_grained", "github_pat_" + "A" * 30),
            ("gitlab", "glpat-" + "A" * 24),
            ("openai", "sk-" + "A" * 24),
            ("slack", "xoxb-" + "A" * 24),
        )
        fields = (
            "taskId",
            "offerId",
            "sessionId",
            "childThreadId",
            "childTurnId",
            "parentThreadId",
            "expectedParentTurnId",
        )
        for credential_class, credential in credentials:
            for field in fields:
                with self.subTest(
                    credential_class=credential_class, field=field
                ), self.assertRaises(RequestValidationError):
                    WatchRequest.parse(valid_request(**{field: credential}))

    def test_direct_request_construction_cannot_bypass_identity_invariants(self) -> None:
        request = WatchRequest.parse(valid_request())
        with self.assertRaises(RequestValidationError):
            replace(request, runtime_evidence_digest="0" * 64)
        with self.assertRaises(RequestValidationError):
            replace(request, task_id="ghp_" + "A" * 36)

    def test_rejects_missing_field(self) -> None:
        raw = valid_request()
        raw.pop("offerId")
        with self.assertRaises(RequestValidationError):
            WatchRequest.parse(raw)


if __name__ == "__main__":
    unittest.main()
