"""Deterministic artifact classification and resource preset selection."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, canonical_bytes, digest_object, require_keys
from gkd_task.errors import TaskError


ARTIFACT_CLASSES = ("zero", "bounded", "build-or-unknown")
PRESET_NAMES = ("resource-constrained", "standard", "high-capacity")

_BYTES_PER_GIB = 1024 * 1024 * 1024
_PRESETS: dict[str, dict[str, Any]] = {
    "resource-constrained": {
        "maxPeakDiskBytes": 512 * 1024 * 1024,
        "minMemoryBytes": 512 * 1024 * 1024,
        "minCpuCount": 1,
        "requiresExplicitFacts": False,
        "allowsUnknownBuild": False,
    },
    "standard": {
        "maxPeakDiskBytes": 4 * _BYTES_PER_GIB,
        "minMemoryBytes": 4 * _BYTES_PER_GIB,
        "minCpuCount": 2,
        "requiresExplicitFacts": True,
        "allowsUnknownBuild": False,
    },
    "high-capacity": {
        "maxPeakDiskBytes": 16 * _BYTES_PER_GIB,
        "minMemoryBytes": 16 * _BYTES_PER_GIB,
        "minCpuCount": 4,
        "requiresExplicitFacts": True,
        "allowsUnknownBuild": False,
    },
}


def _object(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError(code)
    return value


def _non_negative_integer(value: Any, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TaskError(code)
    return value


def _resource_facts(value: Any) -> dict[str, Any]:
    if value is None:
        return {
            "availableDiskBytes": None,
            "memoryBytes": None,
            "cpuCount": None,
            "source": "unknown",
            "verified": False,
            "complete": False,
        }
    facts = _object(value, "RESOURCE_FACTS_INVALID")
    expected = {"availableDiskBytes", "memoryBytes", "cpuCount", "source", "verified"}
    if not set(facts).issubset(expected):
        raise TaskError("RESOURCE_FACTS_INVALID")
    normalized = {
        "availableDiskBytes": facts.get("availableDiskBytes"),
        "memoryBytes": facts.get("memoryBytes"),
        "cpuCount": facts.get("cpuCount"),
        "source": facts.get("source", "unknown"),
        "verified": facts.get("verified", False),
    }
    for key in ("availableDiskBytes", "memoryBytes", "cpuCount"):
        if normalized[key] is not None:
            _non_negative_integer(normalized[key], "RESOURCE_FACTS_INVALID")
    if normalized["source"] not in {"host", "runner", "observed", "unknown"}:
        raise TaskError("RESOURCE_FACTS_INVALID")
    if not isinstance(normalized["verified"], bool):
        raise TaskError("RESOURCE_FACTS_INVALID")
    normalized["complete"] = all(
        normalized[key] is not None for key in ("availableDiskBytes", "memoryBytes", "cpuCount")
    ) and normalized["verified"]
    return normalized


def preset_details(name: str) -> dict[str, Any]:
    if name not in PRESET_NAMES:
        raise TaskError("RESOURCE_PRESET_INVALID")
    return {"name": name, **deepcopy(_PRESETS[name])}


def select_preset(name: str | None = None, resource_facts: dict[str, Any] | None = None) -> dict[str, Any]:
    facts = _resource_facts(resource_facts)
    selected = name or "resource-constrained"
    if selected not in PRESET_NAMES:
        raise TaskError("RESOURCE_PRESET_INVALID")
    details = preset_details(selected)
    if details["requiresExplicitFacts"] and not facts["complete"]:
        raise TaskError("RESOURCE_FACTS_REQUIRED")
    if facts["complete"]:
        if facts["memoryBytes"] < details["minMemoryBytes"] or facts["cpuCount"] < details["minCpuCount"]:
            raise TaskError("RESOURCE_PRESET_UNSUPPORTED")
    return {
        "schemaVersion": 1,
        "name": selected,
        "maxPeakDiskBytes": details["maxPeakDiskBytes"],
        "minMemoryBytes": details["minMemoryBytes"],
        "minCpuCount": details["minCpuCount"],
        "requiresExplicitFacts": details["requiresExplicitFacts"],
        "allowsUnknownBuild": details["allowsUnknownBuild"],
        "resourceFacts": facts,
        "presetDigest": digest_object({"name": selected, **details}),
    }


def _artifact_name(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 128 or CREDENTIAL_RE.search(value):
        raise TaskError("ARTIFACT_FACTS_INVALID")
    if any(character in value for character in "\x00\r\n"):
        raise TaskError("ARTIFACT_FACTS_INVALID")
    return value


def _artifact_record(value: Any, preset: dict[str, Any]) -> dict[str, Any]:
    item = _object(value, "ARTIFACT_FACTS_INVALID")
    allowed = {"name", "kind", "maxBytes", "peakBytes", "buildCommand"}
    if not set(item).issubset(allowed):
        raise TaskError("ARTIFACT_FACTS_INVALID")
    name = _artifact_name(item.get("name"))
    kind = item.get("kind")
    if kind is not None and kind not in {"zero", "bounded", "build", "unknown"}:
        raise TaskError("ARTIFACT_FACTS_INVALID")
    max_bytes = item.get("maxBytes")
    peak_bytes = item.get("peakBytes")
    if max_bytes is not None:
        max_bytes = _non_negative_integer(max_bytes, "ARTIFACT_FACTS_INVALID")
    if peak_bytes is not None:
        peak_bytes = _non_negative_integer(peak_bytes, "ARTIFACT_FACTS_INVALID")
    if max_bytes is not None and peak_bytes is not None and peak_bytes < max_bytes:
        raise TaskError("ARTIFACT_FACTS_INVALID")
    command = item.get("buildCommand")
    if command is not None and (
        not isinstance(command, str)
        or len(command.encode("utf-8")) > 4096
        or "\x00" in command
        or CREDENTIAL_RE.search(command)
    ):
        raise TaskError("ARTIFACT_FACTS_INVALID")

    if kind == "zero" or (kind is None and max_bytes == 0 and peak_bytes in {None, 0}):
        artifact_class = "zero"
        max_bytes = 0
        peak_bytes = 0
        reason = "NO_LARGE_ARTIFACT"
    elif max_bytes is not None and (kind in {None, "bounded", "build"}):
        artifact_class = "bounded"
        peak_bytes = max_bytes if peak_bytes is None else peak_bytes
        reason = "EXPLICIT_PEAK_BOUND"
    else:
        artifact_class = "build-or-unknown"
        reason = "BUILD_BOUND_UNKNOWN"

    budget = preset["maxPeakDiskBytes"]
    available = preset["resourceFacts"]["availableDiskBytes"]
    peak_violation = peak_bytes is not None and (peak_bytes > budget or (available is not None and peak_bytes > available))
    if peak_violation:
        decision = "blocked"
        decision_reason = "PEAK_DISK_VIOLATION"
    elif artifact_class == "build-or-unknown":
        decision = "blocked"
        decision_reason = "BUILD_BOUND_UNKNOWN"
    else:
        decision = "allow"
        decision_reason = reason
    return {
        "schemaVersion": 1,
        "name": name,
        "artifactClass": artifact_class,
        "maxBytes": max_bytes,
        "peakBytes": peak_bytes,
        "decision": decision,
        "reason": decision_reason,
    }


def classify_artifacts(
    artifacts: list[dict[str, Any]],
    preset: str | None = None,
    resource_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(artifacts, list) or not artifacts:
        raise TaskError("ARTIFACT_FACTS_INVALID")
    selected = select_preset(preset, resource_facts)
    records = [_artifact_record(value, selected) for value in artifacts]
    if all(record["artifactClass"] == "zero" for record in records):
        overall_class = "zero"
        peak_bytes: int | None = 0
    elif all(record["artifactClass"] in {"zero", "bounded"} for record in records):
        overall_class = "bounded"
        peak_bytes = sum(record["peakBytes"] or 0 for record in records)
    else:
        overall_class = "build-or-unknown"
        peak_bytes = None
    aggregate_violation = peak_bytes is not None and (
        peak_bytes > selected["maxPeakDiskBytes"]
        or (
            selected["resourceFacts"]["availableDiskBytes"] is not None
            and peak_bytes > selected["resourceFacts"]["availableDiskBytes"]
        )
    )
    if aggregate_violation:
        outcome = "blocked"
        reason = "PEAK_DISK_VIOLATION"
    elif any(record["decision"] == "blocked" for record in records):
        outcome = "blocked"
        reason = next(record["reason"] for record in records if record["decision"] == "blocked")
    else:
        outcome = "allow"
        reason = "WITHIN_RESOURCE_BOUND"
    return {
        "schemaVersion": 1,
        "artifactClass": overall_class,
        "artifacts": records,
        "peakBytes": peak_bytes,
        "preset": selected,
        "outcome": outcome,
        "reason": reason,
    }


def canonical_resource_plan(value: dict[str, Any]) -> bytes:
    """Encode a resource plan without retaining commands or external paths."""

    require_keys(value, {"schemaVersion", "artifactClass", "artifacts", "peakBytes", "preset", "outcome", "reason"}, "RESOURCE_PLAN_INVALID")
    return canonical_bytes(value)
