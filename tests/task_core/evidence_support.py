"""Test-only runtime evidence fixtures."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_task.canonical import digest_object
from gkd_task.service import TASK_SCHEMA_VERSION, validate_runtime_evidence


class FixtureEvidenceProvider:
    def __init__(self, evidence: dict[str, Any]) -> None:
        validate_runtime_evidence(evidence)
        self.evidence = evidence

    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]:
        del purpose, expected
        return deepcopy(self.evidence)


def make_fixture_evidence(
    writer_id: str,
    session_digest: str,
    role_digest: str,
    config_digest: str,
    route: str,
    status: str,
    observed_at: str,
) -> dict[str, Any]:
    value = {
        "schemaVersion": TASK_SCHEMA_VERSION,
        "provider": "fixture",
        "writerId": writer_id,
        "sessionDigest": session_digest,
        "roleDigest": role_digest,
        "configDigest": config_digest,
        "route": route,
        "status": status,
        "observedAt": observed_at,
    }
    value["evidenceDigest"] = digest_object(value)
    validate_runtime_evidence(value)
    return value
