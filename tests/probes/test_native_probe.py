from __future__ import annotations

import unittest

from probes.multiagentv2.native_probe import (
    CONTRACT_IDS,
    DeadlineLatch,
    ProbeError,
    _models_from_catalog,
    classify_error,
    classify_native,
    sanitize_text,
    summarize_thread_snapshot,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class DeadlineLatchTests(unittest.TestCase):
    def test_emits_timeout_once_at_twelve_hours(self) -> None:
        clock = FakeClock()
        latch = DeadlineLatch(43_200_000, clock)

        clock.advance(43_199.999)
        self.assertIsNone(latch.poll())
        clock.advance(0.001)
        self.assertEqual(latch.poll(), "timeout")
        self.assertIsNone(latch.poll())


class RedactionTests(unittest.TestCase):
    def test_redacts_paths_and_credentials(self) -> None:
        raw = (
            "/Users/example/work token=abc123 "
            "Authorization: Bearer bearer-secret cookie=session-secret"
        )
        cleaned = sanitize_text(raw)

        self.assertNotIn("example", cleaned)
        self.assertNotIn("abc123", cleaned)
        self.assertNotIn("bearer-secret", cleaned)
        self.assertNotIn("session-secret", cleaned)
        self.assertIn("<HOME>", cleaned)
        self.assertIn("<REDACTED>", cleaned)

    def test_thread_summary_drops_body_and_hashes_id(self) -> None:
        source = {
            "thread": {
                "id": "thread-sensitive-id",
                "status": {"type": "active"},
                "updatedAt": 123,
                "parentThreadId": "parent-id",
                "agentRole": "probe",
                "preview": "private user prompt",
                "turns": [
                    {
                        "items": [
                            {"type": "agentMessage", "text": "private response"},
                            {"type": "mcpToolCall", "arguments": "secret"},
                        ]
                    }
                ],
            }
        }

        summary = summarize_thread_snapshot(source)
        serialized = repr(summary)

        self.assertNotIn("thread-sensitive-id", serialized)
        self.assertNotIn("private user prompt", serialized)
        self.assertNotIn("private response", serialized)
        self.assertNotIn("secret", serialized)
        self.assertEqual(summary["itemCount"], 2)
        self.assertEqual(summary["turnCount"], 1)


class ClassificationTests(unittest.TestCase):
    def test_classifies_wait_limit_error(self) -> None:
        self.assertEqual(
            classify_error(
                1,
                "features.multi_agent_v2.max_wait_timeout_ms must be at most 3600000",
            ),
            "max_wait_timeout_exceeded",
        )

    def test_native_outcome_is_fail_closed(self) -> None:
        matrix = {contract: "unknown" for contract in CONTRACT_IDS}
        self.assertEqual(classify_native(matrix), "environment_blocked")

        matrix["single_long_wait"] = "fail"
        self.assertEqual(classify_native(matrix), "environment_blocked")

        matrix["twelve_hour_deadline"] = "fail"
        self.assertEqual(classify_native(matrix), "native_insufficient")

    def test_rejects_incomplete_or_invalid_matrix(self) -> None:
        with self.assertRaises(ValueError):
            classify_native({"single_long_wait": "fail"})

        matrix = {contract: "unknown" for contract in CONTRACT_IDS}
        matrix["normal_final_wakeup"] = "supported"
        with self.assertRaises(ValueError):
            classify_native(matrix)

    def test_accepts_object_or_array_model_catalog(self) -> None:
        model = {"slug": "gpt-5.6-sol"}
        self.assertEqual(_models_from_catalog({"models": [model]}), [model])
        self.assertEqual(_models_from_catalog([model]), [model])

        with self.assertRaises(ProbeError):
            _models_from_catalog({"models": "not-an-array"})


if __name__ == "__main__":
    unittest.main()
