from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from tests.legacy_format_catalog import load_catalog, validate_catalog


CORE_SCOPE_PATHS = (
    "tests/release_candidate",
    "tests/finalization",
    "tests/ci_policy",
    "tests/task_core",
    "tests/role_routing",
    "tests/runtime_bridge",
    "tests/production_migration",
    "tests/foundation",
)


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _discover(repository: Path, relative_paths: tuple[str, ...]) -> set[str]:
    result: set[str] = set()
    for relative in relative_paths:
        suite = unittest.defaultTestLoader.discover(
            str(repository / relative),
            pattern="test_*.py",
            top_level_dir=str(repository),
        )
        result.update(test.id() for test in _flatten(suite))
    return result


class LegacyFormatCatalogContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[2]
        self.catalog = load_catalog()
        self.core_ids = _discover(self.repository, CORE_SCOPE_PATHS)
        self.matrix_ids = _discover(self.repository, ("tests/release_upgrade",))

    def test_catalog_covers_all_public_formats_with_disjoint_core_and_matrix_contracts(self) -> None:
        validate_catalog(self.catalog, self.core_ids, self.matrix_ids)

    def test_catalog_rejects_missing_duplicate_and_cross_scope_contracts(self) -> None:
        missing = deepcopy(self.catalog)
        missing["formats"].pop()
        with self.assertRaisesRegex(ValueError, "LEGACY_FORMAT_CATALOG_INVALID"):
            validate_catalog(missing, self.core_ids, self.matrix_ids)

        duplicate = deepcopy(self.catalog)
        duplicate["formats"][1]["core"]["readTestId"] = duplicate["formats"][0]["core"]["readTestId"]
        with self.assertRaisesRegex(ValueError, "LEGACY_FORMAT_CATALOG_INVALID"):
            validate_catalog(duplicate, self.core_ids, self.matrix_ids)

        cross_scope = deepcopy(self.catalog)
        cross_scope["formats"][0]["matrixTestIds"] = [cross_scope["formats"][0]["core"]["readTestId"]]
        with self.assertRaisesRegex(ValueError, "LEGACY_FORMAT_CATALOG_INVALID"):
            validate_catalog(cross_scope, self.core_ids, self.matrix_ids)


if __name__ == "__main__":
    unittest.main()
