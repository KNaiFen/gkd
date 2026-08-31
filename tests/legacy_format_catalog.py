"""Versioned public legacy-format catalog validation."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[1] / "canonical" / "inputs" / "release" / "legacy-format-catalog.json"
FORMAT_NAMES = (
    "source-v1",
    "install-v1",
    "result-manifest-v1",
    "task-path-v1",
    "offer-v1",
    "launch-envelope-v1",
    "role-activation-v1",
    "wait-state-v1",
    "finalization-record-v1",
    "release-record-v2",
)
TEST_ID_RE = re.compile(r"^(?:tests\.)[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID") from error
    if not isinstance(value, dict):
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
    return value


def validate_catalog(
    catalog: dict[str, Any],
    core_test_ids: set[str],
    matrix_test_ids: set[str],
) -> None:
    if set(catalog) != {"schemaVersion", "formats"} or catalog["schemaVersion"] != 1:
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
    formats = catalog["formats"]
    if not isinstance(formats, list) or len(formats) != len(FORMAT_NAMES):
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")

    names: list[str] = []
    declared_core: list[str] = []
    declared_matrix: list[str] = []
    for item in formats:
        if not isinstance(item, dict) or set(item) != {"name", "publicSurface", "core", "matrixTestIds"}:
            raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
        core = item["core"]
        matrix = item["matrixTestIds"]
        if (
            not isinstance(item["name"], str)
            or not isinstance(item["publicSurface"], str)
            or not item["publicSurface"]
            or not isinstance(core, dict)
            or set(core) != {"readTestId", "rejectOrRestoreTestId"}
            or not isinstance(matrix, list)
            or not matrix
        ):
            raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
        read_id = core["readTestId"]
        reject_id = core["rejectOrRestoreTestId"]
        if (
            not isinstance(read_id, str)
            or not isinstance(reject_id, str)
            or read_id == reject_id
            or not TEST_ID_RE.fullmatch(read_id)
            or not TEST_ID_RE.fullmatch(reject_id)
            or any(not isinstance(identifier, str) or not TEST_ID_RE.fullmatch(identifier) for identifier in matrix)
            or matrix != sorted(set(matrix))
        ):
            raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
        names.append(item["name"])
        declared_core.extend((read_id, reject_id))
        declared_matrix.extend(matrix)

    if tuple(names) != FORMAT_NAMES or len(declared_core) != len(set(declared_core)) or len(declared_matrix) != len(set(declared_matrix)):
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
    if set(declared_core).intersection(declared_matrix):
        raise ValueError("LEGACY_FORMAT_CATALOG_INVALID")
    if not set(declared_core).issubset(core_test_ids):
        raise ValueError("LEGACY_FORMAT_CORE_SCOPE_MISMATCH")
    if not set(declared_matrix).issubset(matrix_test_ids):
        raise ValueError("LEGACY_FORMAT_MATRIX_SCOPE_MISMATCH")
