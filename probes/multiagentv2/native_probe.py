#!/usr/bin/env python3
"""Capture a redacted, version-bound snapshot of native D2 surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import tomllib
from typing import Any, Callable, Iterable, Mapping, Sequence


TWELVE_HOURS_MS = 43_200_000
ONE_HOUR_MS = 3_600_000
CONTRACT_IDS = (
    "single_long_wait",
    "normal_final_wakeup",
    "hourly_internal_watchdog",
    "healthy_zero_parent_context",
    "long_tool_is_healthy",
    "abnormal_wakeup",
    "wrong_turn_rejected",
    "child_interrupt_parent_safe",
    "orchestrator_failure_wakeup",
    "twelve_hour_deadline",
)
ALLOWED_STATUSES = frozenset({"pass", "fail", "unknown"})
RELEVANT_METHODS = frozenset(
    {
        "thread/list",
        "thread/read",
        "thread/status/changed",
        "turn/completed",
        "turn/interrupt",
        "turn/steer",
    }
)
RELEVANT_SCHEMA_FILES = (
    "codex_app_server_protocol.v2.schemas.json",
    "v2/ThreadListParams.json",
    "v2/ThreadReadParams.json",
    "v2/ThreadReadResponse.json",
    "v2/ThreadStatusChangedNotification.json",
    "v2/TurnCompletedNotification.json",
    "v2/TurnInterruptParams.json",
    "v2/TurnSteerParams.json",
)


class ProbeError(RuntimeError):
    pass


class DeadlineLatch:
    """Emit one timeout event when a deterministic deadline is crossed."""

    def __init__(self, duration_ms: int, clock: Callable[[], float] = time.monotonic):
        if duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        self._clock = clock
        self._deadline = clock() + duration_ms / 1000
        self._emitted = False

    def poll(self) -> str | None:
        if self._emitted or self._clock() < self._deadline:
            return None
        self._emitted = True
        return "timeout"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sanitize_text(value: str, *, home: str | None = None, cwd: str | None = None) -> str:
    replacements = ((cwd, "<WORKTREE>"), (home, "<HOME>"))
    cleaned = value
    for original, replacement in replacements:
        if original:
            cleaned = cleaned.replace(original, replacement)
    cleaned = re.sub(r"/Users/[^/\s]+", "<HOME>", cleaned)
    cleaned = re.sub(
        r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
        r"\1<REDACTED>",
        cleaned,
    )
    cleaned = re.sub(
        r"(?i)((?:api[_-]?key|token|cookie|password|secret)\s*[:=]\s*)[^\s,;]+",
        r"\1<REDACTED>",
        cleaned,
    )
    return cleaned


def classify_error(returncode: int, stderr: str) -> str | None:
    if returncode == 0:
        return None
    lowered = stderr.lower()
    if "max_wait_timeout_ms must be at most" in lowered:
        return "max_wait_timeout_exceeded"
    if returncode == 127 or "no such file or directory" in lowered:
        return "command_not_found"
    if "timed out" in lowered or "timeout expired" in lowered:
        return "timed_out"
    if "config" in lowered or "toml" in lowered:
        return "config_error"
    return "other_error"


def classify_native(matrix: Mapping[str, str]) -> str:
    if set(matrix) != set(CONTRACT_IDS):
        raise ValueError("matrix must contain exactly the ten D2 contracts")
    if any(status not in ALLOWED_STATUSES for status in matrix.values()):
        raise ValueError("matrix contains an unsupported status")
    hard_failures = {"single_long_wait", "twelve_hour_deadline"}
    if all(matrix[contract] == "fail" for contract in hard_failures):
        return "native_insufficient"
    return "environment_blocked"


def summarize_thread_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    thread = payload.get("thread", payload)
    if not isinstance(thread, Mapping):
        raise ValueError("thread snapshot must be an object")

    status = thread.get("status", {})
    status_type = status.get("type") if isinstance(status, Mapping) else None
    turns = thread.get("turns", [])
    item_types: list[str] = []
    if isinstance(turns, list):
        for turn in turns:
            if not isinstance(turn, Mapping):
                continue
            items = turn.get("items", [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, Mapping) and isinstance(item.get("type"), str):
                    item_types.append(item["type"])

    sorted_types = sorted(item_types)
    return {
        "threadIdDigest": sha256_text(str(thread.get("id", ""))),
        "status": status_type,
        "updatedAt": thread.get("updatedAt"),
        "parentThreadPresent": bool(thread.get("parentThreadId")),
        "agentRole": thread.get("agentRole"),
        "turnCount": len(turns) if isinstance(turns, list) else 0,
        "itemCount": len(item_types),
        "itemTypeDigest": sha256_text("\n".join(sorted_types)),
    }


def _run(args: Sequence[str], *, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"command timed out after {timeout}s: {Path(args[0]).name}") from exc


def _json_from_stdout(result: subprocess.CompletedProcess[str], label: str) -> Any:
    if result.returncode != 0:
        raise ProbeError(f"{label} failed with {classify_error(result.returncode, result.stderr)}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"{label} did not return JSON") from exc


def _models_from_catalog(catalog: Any) -> list[Mapping[str, Any]]:
    if isinstance(catalog, Mapping):
        models = catalog.get("models", [])
    elif isinstance(catalog, list):
        models = catalog
    else:
        raise ProbeError("bundled model catalog has an unsupported top-level type")
    if not isinstance(models, list):
        raise ProbeError("bundled model catalog models field is not an array")
    return [model for model in models if isinstance(model, Mapping)]


def _configuration_declaration() -> dict[str, Any]:
    config_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = config_home / "config.toml"
    try:
        with config_path.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {"available": False, "errorClass": type(exc).__name__}

    multiagent = config.get("features", {}).get("multi_agent_v2", {})
    return {
        "available": True,
        "source": "local_configuration_declaration",
        "model": config.get("model"),
        "reasoningEffort": config.get("model_reasoning_effort"),
        "multiAgentV2": {
            key: multiagent.get(key)
            for key in (
                "enabled",
                "max_concurrent_threads_per_session",
                "min_wait_timeout_ms",
                "default_wait_timeout_ms",
                "max_wait_timeout_ms",
            )
        },
    }


def _wait_trial(codex: str, timeout_ms: int) -> dict[str, Any]:
    result = _run(
        (
            codex,
            "-c",
            "features.multi_agent_v2.enabled=true",
            "-c",
            f"features.multi_agent_v2.max_wait_timeout_ms={timeout_ms}",
            "features",
            "list",
        )
    )
    feature_loaded = any(
        line.split()[-1:] == ["true"] and line.split()[:1] == ["multi_agent_v2"]
        for line in result.stdout.splitlines()
    )
    error_class = classify_error(result.returncode, result.stderr)
    return {
        "requestedMs": timeout_ms,
        "exitCode": result.returncode,
        "featureLoaded": feature_loaded,
        "errorClass": error_class,
    }


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_strings(nested)


def _variant_types(definition: Mapping[str, Any]) -> list[str]:
    variants: list[str] = []
    for variant in definition.get("oneOf", []):
        enum_values = variant.get("properties", {}).get("type", {}).get("enum", [])
        variants.extend(value for value in enum_values if isinstance(value, str))
    return sorted(set(variants))


def _enum_values(definition: Mapping[str, Any]) -> list[str]:
    return sorted(value for value in definition.get("enum", []) if isinstance(value, str))


def _protocol_surface(codex: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="gkd-m1-schema-") as temporary:
        root = Path(temporary)
        result = _run(
            (
                codex,
                "-c",
                "features.multi_agent_v2.enabled=true",
                "app-server",
                "generate-json-schema",
                "--experimental",
                "--out",
                str(root),
            )
        )
        if result.returncode != 0:
            raise ProbeError(
                "schema generation failed with "
                f"{classify_error(result.returncode, result.stderr)}"
            )

        documents: dict[str, Any] = {}
        digest = hashlib.sha256()
        for relative in RELEVANT_SCHEMA_FILES:
            raw = (root / relative).read_bytes()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(raw)
            documents[relative] = json.loads(raw)

        protocol = documents["codex_app_server_protocol.v2.schemas.json"]
        steer = documents["v2/TurnSteerParams.json"]
        interrupt = documents["v2/TurnInterruptParams.json"]
        read_params = documents["v2/ThreadReadParams.json"]
        read_response = documents["v2/ThreadReadResponse.json"]
        status_changed = documents["v2/ThreadStatusChangedNotification.json"]
        turn_completed = documents["v2/TurnCompletedNotification.json"]

        methods = sorted(RELEVANT_METHODS.intersection(_walk_strings(protocol)))
        item_types = _variant_types(turn_completed["definitions"]["ThreadItem"])
        thread_fields = read_response["definitions"]["Thread"]["properties"]
        thread_statuses = _variant_types(status_changed["definitions"]["ThreadStatus"])
        turn_statuses = _enum_values(turn_completed["definitions"]["TurnStatus"])
        collab_statuses = _enum_values(
            turn_completed["definitions"]["CollabAgentStatus"]
        )

        return {
            "source": "generated_app_server_json_schema",
            "schemaDigestSha256": digest.hexdigest(),
            "methods": methods,
            "threadFields": sorted(
                set(thread_fields).intersection(
                    {
                        "agentRole",
                        "id",
                        "parentThreadId",
                        "sessionId",
                        "status",
                        "turns",
                        "updatedAt",
                    }
                )
            ),
            "threadStatuses": thread_statuses,
            "turnStatuses": turn_statuses,
            "collabAgentStatuses": collab_statuses,
            "itemTypeCount": len(item_types),
            "itemTypeDigestSha256": sha256_text("\n".join(item_types)),
            "longToolItemTypes": sorted(
                set(item_types).intersection(
                    {"collabAgentToolCall", "commandExecution", "dynamicToolCall", "mcpToolCall"}
                )
            ),
            "threadReadIncludeTurnsIsOptional": "includeTurns"
            not in read_params.get("required", []),
            "turnSteerRequiredFields": sorted(steer.get("required", [])),
            "turnSteerExpectedTurnPreconditionDeclared": "currently active turn"
            in steer.get("properties", {})
            .get("expectedTurnId", {})
            .get("description", ""),
            "turnInterruptRequiredFields": sorted(interrupt.get("required", [])),
        }


def capture(codex: str) -> dict[str, Any]:
    version_result = _run((codex, "--version"))
    version_match = re.search(r"codex-cli\s+([0-9.]+)", version_result.stdout)
    if version_result.returncode != 0 or not version_match:
        raise ProbeError("unable to determine Codex CLI version")

    catalog = _json_from_stdout(
        _run((codex, "debug", "models", "--bundled")), "bundled model catalog"
    )
    models = _models_from_catalog(catalog)
    sol = next(
        (model for model in models if model.get("slug") == "gpt-5.6-sol"),
        None,
    )
    if sol is None:
        raise ProbeError("gpt-5.6-sol is absent from the bundled model catalog")
    supported_efforts = sorted(
        level["effort"]
        for level in sol.get("supported_reasoning_levels", [])
        if isinstance(level, Mapping) and isinstance(level.get("effort"), str)
    )

    valid_trial = _wait_trial(codex, ONE_HOUR_MS)
    invalid_trial = _wait_trial(codex, TWELVE_HOURS_MS)
    hard_status = (
        "fail"
        if valid_trial["featureLoaded"]
        and invalid_trial["errorClass"] == "max_wait_timeout_exceeded"
        else "unknown"
    )
    matrix = {contract: "unknown" for contract in CONTRACT_IDS}
    matrix["single_long_wait"] = hard_status
    matrix["twelve_hour_deadline"] = hard_status
    return {
        "schemaVersion": 1,
        "probe": "GKD-M-1A",
        "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "codexVersion": version_match.group(1),
        "nativeOutcome": classify_native(matrix),
        "configuration": _configuration_declaration(),
        "modelCatalog": {
            "source": "bundled_model_catalog",
            "slug": sol["slug"],
            "supportedReasoningEfforts": supported_efforts,
            "xhighSupported": "xhigh" in supported_efforts,
        },
        "waitLimit": {
            "source": "config_parser_behavior",
            "oneHourTrial": valid_trial,
            "twelveHourTrial": invalid_trial,
            "parserHardMaxMs": ONE_HOUR_MS if hard_status == "fail" else None,
            "twelveHourConfigurable": invalid_trial["exitCode"] == 0,
        },
        "protocol": _protocol_surface(codex),
        "security": {
            "conversationBodyStored": False,
            "rawConfigurationStored": False,
            "rawCommandOutputStored": False,
            "fullPathsStored": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=shutil.which("codex"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.codex:
        parser.error("codex executable not found")
    return args


def main() -> int:
    args = _parse_args()
    evidence = capture(args.codex)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
