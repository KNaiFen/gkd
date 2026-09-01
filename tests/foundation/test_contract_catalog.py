from __future__ import annotations

import unittest

from tests.contract_catalog import (
    APP_SERVER_INITIALIZE_CONTRACT_TEST_IDS,
    DELIVERY_CONTRACT_TEST_IDS,
    FOUNDATION_CONTRACT_TEST_IDS,
    WATCHDOG_CONTRACT_TEST_IDS,
    build_contract_catalog,
    test_to_contract_ids,
    validate_contract_coverage,
)


class ContractCatalogContracts(unittest.TestCase):
    def test_catalogs_use_full_test_ids_and_stable_contract_order(self) -> None:
        for catalog in (DELIVERY_CONTRACT_TEST_IDS, FOUNDATION_CONTRACT_TEST_IDS, WATCHDOG_CONTRACT_TEST_IDS, APP_SERVER_INITIALIZE_CONTRACT_TEST_IDS):
            self.assertEqual(sorted(catalog), list(catalog))
            for test_ids in catalog.values():
                self.assertEqual(sorted(test_ids), list(test_ids))
                self.assertTrue(all(test_id.startswith("tests.") for test_id in test_ids))

    def test_reverse_index_preserves_shared_test_ownership_once_per_contract(self) -> None:
        reverse = test_to_contract_ids(WATCHDOG_CONTRACT_TEST_IDS)
        shared = "tests.watchdog.test_mcp.McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker"
        self.assertEqual(
            (
                "bounded_protocol_failures",
                "cancellation_and_eof_shutdown",
                "cancellation_scope",
                "mcp_framing_and_silence",
            ),
            reverse[shared],
        )

    def test_invalid_duplicate_test_id_is_rejected(self) -> None:
        test_id = "tests.example.Contracts.test_once"
        with self.assertRaisesRegex(ValueError, "CONTRACT_CATALOG_INVALID"):
            build_contract_catalog({"example": (test_id, test_id)})

    def test_catalog_test_drift_is_rejected_before_evidence_generation(self) -> None:
        catalog = build_contract_catalog({"example": ("tests.example.Contracts.test_once",)})
        with self.assertRaisesRegex(ValueError, "CONTRACT_CATALOG_TEST_IDS_MISMATCH"):
            validate_contract_coverage(catalog, set())


if __name__ == "__main__":
    unittest.main()
