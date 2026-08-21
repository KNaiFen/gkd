from __future__ import annotations

import unittest

from gkd_ci.recommendations import parse_ci_facts, recommend_ci, verify_runtime_price
from gkd_ci.resources import classify_artifacts, select_preset
from gkd_task.errors import TaskError
from tests.resource_scanner.helpers import ci_facts, resource_facts


class ResourceContracts(unittest.TestCase):
    def test_zero_and_bounded_artifacts_are_deterministic(self) -> None:
        value = classify_artifacts(
            [
                {"name": "docs", "kind": "zero"},
                {"name": "reports", "kind": "bounded", "maxBytes": 1024},
            ]
        )
        self.assertEqual("bounded", value["artifactClass"])
        self.assertEqual("allow", value["outcome"])
        self.assertEqual(1024, value["peakBytes"])
        self.assertEqual(value, classify_artifacts([{"name": "docs", "kind": "zero"}, {"name": "reports", "kind": "bounded", "maxBytes": 1024}]))

    def test_unknown_build_is_terminal_and_cleanup_does_not_change_it(self) -> None:
        value = classify_artifacts([{"name": "package", "kind": "build", "buildCommand": "build"}])
        self.assertEqual("build-or-unknown", value["artifactClass"])
        self.assertEqual("blocked", value["outcome"])
        self.assertEqual("BUILD_BOUND_UNKNOWN", value["reason"])

    def test_peak_disk_violation_is_blocked(self) -> None:
        value = classify_artifacts(
            [{"name": "large", "kind": "bounded", "maxBytes": 2 * 1024**3}],
            "resource-constrained",
            resource_facts(availableDiskBytes=3 * 1024**3),
        )
        self.assertEqual("PEAK_DISK_VIOLATION", value["reason"])
        self.assertEqual("blocked", value["outcome"])

    def test_standard_and_high_capacity_require_verified_facts(self) -> None:
        with self.assertRaisesRegex(TaskError, "RESOURCE_FACTS_REQUIRED"):
            select_preset("standard")
        self.assertEqual("standard", select_preset("standard", resource_facts(memoryBytes=4 * 1024**3))["name"])
        with self.assertRaisesRegex(TaskError, "RESOURCE_PRESET_UNSUPPORTED"):
            select_preset("high-capacity", resource_facts(memoryBytes=4 * 1024**3))

    def test_facts_and_recommendations_preserve_source_and_goal(self) -> None:
        facts = parse_ci_facts(ci_facts(resource=resource_facts(availableDiskBytes=32 * 1024**3, memoryBytes=32 * 1024**3)))
        self.assertEqual("public", facts["visibility"])
        self.assertEqual("runner", facts["resource"]["source"])
        recommendation = recommend_ci(facts, "speed-first")
        self.assertEqual("high-capacity", recommendation["preset"])
        self.assertEqual("verified", recommendation["price"]["status"])
        self.assertEqual("verified", verify_runtime_price(ci_facts()["billing"])["status"])

    def test_unverified_price_is_not_claimed(self) -> None:
        billing = {"source": "provider-contract", "pricePerMinute": 0.01, "verified": False}
        price = verify_runtime_price(billing)
        self.assertEqual("unverified", price["status"])
        self.assertIsNone(price["pricePerMinute"])
        value = ci_facts(billing=billing)
        recommendation = recommend_ci(value, "cost-aware")
        self.assertEqual("PRICE_VERIFICATION_REQUIRED", recommendation["priceReason"])
        self.assertIsNone(recommendation["price"]["pricePerMinute"])

    def test_unknown_visibility_and_malformed_policy_fail_closed(self) -> None:
        value = ci_facts(visibility="unknown")
        self.assertEqual("unknown", parse_ci_facts(value)["visibility"])
        malformed = ci_facts(policy={"baseBranch": "main", "requiredChecks": ["B", "A"]})
        with self.assertRaisesRegex(TaskError, "POLICY_FACTS_INVALID"):
            parse_ci_facts(malformed)


if __name__ == "__main__":
    unittest.main()
