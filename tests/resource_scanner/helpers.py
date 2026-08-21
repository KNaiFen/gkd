from __future__ import annotations

from typing import Any


def resource_facts(**overrides: Any) -> dict[str, Any]:
    value = {
        "availableDiskBytes": 8 * 1024**3,
        "memoryBytes": 8 * 1024**3,
        "cpuCount": 4,
        "source": "runner",
        "verified": True,
    }
    value.update(overrides)
    return value


def ci_facts(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schemaVersion": 1,
        "visibility": "public",
        "runner": {
            "provider": "github",
            "kind": "github-hosted",
            "capacity": "standard",
            "os": "linux",
            "verified": True,
        },
        "policy": {
            "baseBranch": "main",
            "requiredChecks": ["Fixture Verify"],
            "policyDigest": "a" * 64,
            "verified": True,
        },
        "billing": {
            "source": "github-public-pricing",
            "currency": "USD",
            "pricePerMinute": 0.01,
            "verified": True,
            "checkedAt": "2026-08-22T00:00:00Z",
        },
        "resource": resource_facts(),
    }
    value.update(overrides)
    return value
