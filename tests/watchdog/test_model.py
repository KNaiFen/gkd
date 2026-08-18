from __future__ import annotations

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

    def test_rejects_missing_field(self) -> None:
        raw = valid_request()
        raw.pop("offerId")
        with self.assertRaises(RequestValidationError):
            WatchRequest.parse(raw)


if __name__ == "__main__":
    unittest.main()
