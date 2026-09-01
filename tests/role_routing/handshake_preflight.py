#!/usr/bin/env python3
"""Prepare and statically validate the project-scoped F-004 role probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import gkd_toml as tomllib

import gkd_bundle
from gkd_role.roles import load_role_source, locked_bundle_digest, role_catalog, role_files, role_record
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, read_canonical_json, sha256_bytes


ROLE_NAME = "gkd_executor"
ROLE_MODEL = "gpt-5.6-sol"
ROLE_REASONING_EFFORT = "xhigh"
ROLE_SANDBOX = "workspace-write"
SPAWN_TASK_NAME = "gkd_executor_handshake"
SPAWN_FORK_TURNS = "none"
CHILD_TERMINAL_MARKER = "GKD_EXECUTOR_CHILD_TERMINAL"
PARENT_TERMINAL_MARKER = "GKD_PARENT_TERMINAL"
FALLBACK_ROLES = {"default", "worker", "explorer"}
LEGACY_ROLLOUT_VERSION = "0.147.0"
CURRENT_ROLLOUT_VERSION = "0.152.0"
ROLLOUT_ADAPTER_SCHEMA_VERSION = 1
CURRENT_EVENT_TYPES = {
    "error",
    "item.completed",
    "item.started",
    "thread.started",
    "turn.completed",
    "turn.failed",
    "turn.started",
}
CURRENT_ITEM_TYPES = {"agent_message", "collab_tool_call", "mcp_tool_call", "reasoning"}
PARSER_SENTINEL = "no transport configured; use --listen or enable remote control"
LIVE_PROMPT = (
    "Delegation itself is the only task and cannot be completed by the parent. Do not solve the "
    "child task or emit a success marker yourself. Immediately call the tool named `spawn_agent` "
    "exactly once with "
    'agent_type="gkd_executor", task_name="gkd_executor_handshake", fork_turns="none", and '
    'message="Return exactly GKD_EXECUTOR_CHILD_TERMINAL. Do not call tools or read or modify files." '
    "If and only if that spawn succeeds, call the exposed multi-agent wait tool for the returned "
    "child until it is terminal, then return exactly GKD_PARENT_TERMINAL. Never call a wait tool "
    "before spawn. If spawn_agent is unavailable, return exactly GKD_SPAWN_TOOL_UNAVAILABLE and "
    "do not call wait. Do not spawn another agent, change role or model, fall back to a built-in "
    "role, or perform any other work."
)
PROBE_INSTRUCTIONS = (
    "# GKD role handshake\n\n"
    "When the user says that delegation itself is the only task, the parent MUST call "
    "`spawn_agent` before any other tool or response, with exactly the agent type and task "
    "given by the user. The parent MUST NOT replace delegation with its own marker, call a "
    "wait tool before spawn succeeds, choose another role, or fall back. A spawned child whose "
    "task only requests a fixed terminal marker MUST return that marker without tools or file access.\n"
).encode("ascii")


class PreflightError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _unsupported(code: str, message: str) -> None:
    raise PreflightError(code, message)


def _path_hash(path: Path) -> str:
    return hashlib.sha256(path.as_posix().encode("utf-8")).hexdigest()


def _skill_tree_digest(root: Path) -> str:
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_bytes(path.read_bytes()),
                }
            )
    return digest_object(records)


def discover_codex() -> Path:
    discovered = shutil.which("codex")
    if discovered is None:
        raise PreflightError("CODEX_NOT_FOUND", "command -v codex did not resolve an executable")
    resolved = Path(discovered).resolve()
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise PreflightError("CODEX_NOT_EXECUTABLE", "command -v codex did not resolve an executable file")
    return resolved


def _production_root() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).resolve() if configured else (Path.home() / ".codex").resolve()


def _production_snapshot() -> dict[str, object]:
    return gkd_bundle._snapshot_protected(_production_root())


def _repo_snapshot(repo: Path) -> dict[str, object]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or commit.returncode != 0 or tree.returncode != 0:
        raise PreflightError("PROBE_REPO_INSPECTION_FAILED", (result.stderr or commit.stderr or tree.stderr).strip())
    return {
        "clean": result.stdout == "",
        "commitIdentitySha256": sha256_bytes(commit.stdout.strip().encode("ascii")),
        "treeIdentitySha256": sha256_bytes(tree.stdout.strip().encode("ascii")),
    }


def _project_config(description: str) -> bytes:
    return (
        "[agents]\n"
        "enabled = true\n"
        "\n"
        f"[agents.{ROLE_NAME}]\n"
        f"description = {json.dumps(description, ensure_ascii=True)}\n"
        f'config_file = "agents/{ROLE_NAME}.toml"\n'
    ).encode("utf-8")


def validate_generated_toml(
    project_config: bytes,
    role_config: bytes,
    definition: dict[str, object],
    all_skills: list[str],
) -> dict[str, bool]:
    try:
        project = tomllib.loads(project_config.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise PreflightError("GENERATED_PROJECT_CONFIG_PARSE_FAILED", "generated project config is not valid TOML") from error
    try:
        role = tomllib.loads(role_config.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise PreflightError("GENERATED_ROLE_CONFIG_PARSE_FAILED", "generated role config is not valid TOML") from error

    expected_registration = {
        "description": definition["description"],
        "config_file": f"agents/{ROLE_NAME}.toml",
    }
    if project != {"agents": {"enabled": True, ROLE_NAME: expected_registration}}:
        raise PreflightError("GENERATED_PROJECT_CONFIG_INVALID", "generated project config does not match the fixed registration")

    expected_role = {
        "name": definition["name"],
        "description": definition["description"],
        "model": definition["model"],
        "model_reasoning_effort": definition["modelReasoningEffort"],
        "sandbox_mode": definition["sandboxMode"],
        "developer_instructions": definition["developerInstructions"],
        "agents": {"enabled": False},
        "skills": {
            "config": [
                {"path": f"../skills/{name}/SKILL.md", "enabled": name in definition["skills"]}
                for name in all_skills
            ]
        },
    }
    if role != expected_role:
        raise PreflightError("GENERATED_ROLE_CONFIG_INVALID", "generated role config does not match the fixed role definition")
    return {"generatedProjectConfigParsed": True, "generatedRoleConfigParsed": True}


def prepare_probe_repo(bundle_root: Path, repo: Path) -> dict[str, object]:
    bundle_root = bundle_root.resolve()
    repo = repo.resolve()
    if repo.exists():
        if repo.is_symlink() or not repo.is_dir() or any(repo.iterdir()):
            raise PreflightError("PROBE_REPO_NOT_EMPTY", "probe repository must be a new empty directory")
    else:
        repo.mkdir(parents=True)

    git_result = subprocess.run(
        ["git", "init", "--quiet"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if git_result.returncode != 0:
        raise PreflightError("PROBE_GIT_INIT_FAILED", git_result.stderr.strip())

    bundle_digest = locked_bundle_digest(bundle_root)
    catalog = role_catalog(bundle_root, bundle_digest)
    role = role_record(catalog, ROLE_NAME)
    source, _ = load_role_source(bundle_root)
    definition = next(item for item in source["roles"] if item["name"] == ROLE_NAME)

    agents = repo / ".codex" / "agents"
    skills = repo / ".codex" / "skills"
    agents.mkdir(parents=True)
    skills.mkdir()
    role_bytes = role_files(bundle_root, bundle_digest)[f"{ROLE_NAME}.toml"]
    (agents / f"{ROLE_NAME}.toml").write_bytes(role_bytes)
    for name in role["skills"]:
        shutil.copytree(bundle_root / "skills" / name, skills / name)
    project_config = _project_config(definition["description"])
    (repo / ".codex" / "config.toml").write_bytes(project_config)
    (repo / "AGENTS.md").write_bytes(PROBE_INSTRUCTIONS)
    generated_toml = validate_generated_toml(project_config, role_bytes, definition, source["skills"])

    actual_skills = {name: _skill_tree_digest(skills / name) for name in role["skills"]}
    expected_skills = {name: catalog["skillDigests"][name] for name in role["skills"]}
    if sha256_bytes(role_bytes) != role["configDigest"] or actual_skills != expected_skills:
        raise PreflightError("PROBE_DIGEST_MISMATCH", "generated role or Skill bytes do not match the fixed bundle")

    add_result = subprocess.run(
        ["git", "add", "--", ".codex", "AGENTS.md"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commit_result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=GKD Handshake",
            "-c",
            "user.email=gkd-handshake@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "prepare role handshake",
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if add_result.returncode != 0 or commit_result.returncode != 0 or status_result.returncode != 0 or status_result.stdout:
        message = add_result.stderr or commit_result.stderr or status_result.stderr or "probe repository is dirty"
        raise PreflightError("PROBE_REPO_NOT_CLEAN", message.strip())

    return {
        "bundleDigest": bundle_digest,
        "roleDigest": role["roleDigest"],
        "configDigest": role["configDigest"],
        "projectConfigDigest": sha256_bytes(project_config),
        "probeInstructionsDigest": sha256_bytes(PROBE_INSTRUCTIONS),
        "skillDigests": actual_skills,
        "repoIdentitySha256": _path_hash(repo),
        "requestedRole": {
            "name": role["name"],
            "model": role["model"],
            "reasoningEffort": role["modelReasoningEffort"],
            "sandbox": role["sandboxMode"],
        },
        **generated_toml,
        "probeRepo": _repo_snapshot(repo),
    }


def static_parser_command(codex: str, repo: Path) -> list[str]:
    del repo
    return [codex, "app-server", "--listen", "off"]


def _redact(message: str, paths: tuple[Path, ...]) -> str:
    redacted = message
    for path in paths:
        redacted = redacted.replace(path.as_posix(), "<temporary-path>")
    redacted = redacted.replace(Path.home().as_posix(), "<home>")
    return " ".join(redacted.split())[:512]


def classify_parser_result(returncode: int, stdout: str, stderr: str) -> None:
    combined = f"{stdout}\n{stderr}"
    if "Project-local config, hooks, and exec policies are disabled" in combined:
        raise PreflightError("PROJECT_TRUST_NOT_EFFECTIVE", "project-scoped .codex layer was disabled")
    if "Ignoring malformed agent role definition" in combined:
        raise PreflightError("CUSTOM_ROLE_PARSE_FAILED", "Codex rejected the custom role definition")
    if "Error parsing project config" in combined:
        raise PreflightError("PROJECT_CONFIG_PARSE_FAILED", "Codex rejected the project configuration")
    if returncode != 1 or PARSER_SENTINEL not in stderr:
        raise PreflightError("STATIC_PARSER_UNEXPECTED_RESULT", "Codex did not reach the expected no-transport boundary")


def run_static_parser(codex: Path, repo: Path) -> dict[str, object]:
    repo = repo.resolve()
    production_before = _production_snapshot()
    repo_before = _repo_snapshot(repo)
    if repo_before["clean"] is not True:
        raise PreflightError("PROBE_REPO_NOT_CLEAN", "probe repository changed before static parser validation")
    result = subprocess.run(
        static_parser_command(codex.as_posix(), repo),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    production_after = _production_snapshot()
    repo_after = _repo_snapshot(repo)
    if production_before != production_after:
        raise PreflightError("PRODUCTION_CONFIG_CHANGED", "normal user configuration changed during static parsing")
    if repo_before != repo_after or repo_after["clean"] is not True:
        raise PreflightError("PROBE_REPO_CHANGED", "probe repository changed during static parsing")
    try:
        classify_parser_result(result.returncode, result.stdout, result.stderr)
    except PreflightError as error:
        raise PreflightError(error.code, _redact(f"{error}: {result.stderr}", (repo,))) from error
    return {
        "parserOutcome": "normal_environment_reached_no_transport",
        "normalEnvironmentReachedNoTransport": True,
        "productionConfigUnchanged": True,
        "productionConfigDigest": production_after["digest"],
        "productionConfigEntries": production_after["entries"],
        "probeRepoUnchanged": True,
        "probeRepo": repo_after,
    }


def live_command(codex: str | Path, repo: Path) -> list[str]:
    del repo
    return [codex, "exec", "--json", LIVE_PROMPT]


def live_argument_parser_command(codex: str | Path, repo: Path) -> list[str]:
    return [*live_command(codex, repo)[:-1], "--help"]


def _decode_event_records(records: list[dict[str, object]] | list[str], code: str) -> list[dict[str, object]]:
    decoded: list[dict[str, object]] = []
    for record in records:
        if isinstance(record, str):
            if not record.strip():
                continue
            try:
                value = json.loads(record)
            except json.JSONDecodeError as error:
                _unsupported(code, f"JSONL record is not valid JSON: {error.msg}")
            if not isinstance(value, dict):
                _unsupported(code, "JSONL record must be an object")
            record = value
        if not isinstance(record, dict):
            _unsupported(code, "event record must be an object")
        decoded.append(record)
    return decoded


def _rollout_format(parent_records: list[dict[str, object]], code: str) -> str:
    if not parent_records:
        _unsupported(code, "rollout contains no parent records")
    legacy = all(isinstance(record.get("payload"), dict) for record in parent_records)
    current = all("payload" not in record and isinstance(record.get("type"), str) for record in parent_records)
    if legacy and not current:
        return "legacy-payload-v1"
    if current and not legacy:
        return "current-direct-v1"
    _unsupported(code, "rollout records use mixed or unknown wrappers")
    raise AssertionError("unreachable")


def _validate_current_event(record: dict[str, object], code: str) -> None:
    """Accept only the direct JSONL shell observed in the current capture."""
    event_type = record.get("type")
    if "payload" in record or not isinstance(event_type, str) or event_type not in CURRENT_EVENT_TYPES:
        _unsupported(code, "current rollout event uses an unknown wrapper or event type")
    if event_type in {"item.started", "item.completed"}:
        item = record.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None
        if not isinstance(item, dict) or not isinstance(item_type, str) or item_type not in CURRENT_ITEM_TYPES:
            _unsupported(code, "current item event has an unsupported structured item")


def parse_rollout_records(
    parent_records: list[dict[str, object]] | list[str],
    child_rollouts: dict[str, list[dict[str, object]] | list[str]],
    cli_version: str = LEGACY_ROLLOUT_VERSION,
    source: str = "historical-rollout",
) -> dict[str, object]:
    """Parse a versioned rollout envelope without deriving handshake facts."""

    if not isinstance(cli_version, str) or not cli_version:
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "CLI version is required")
    if not isinstance(source, str) or not source:
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "rollout source is required")
    parent = _decode_event_records(parent_records, "UNSUPPORTED_ROLLOUT_FORMAT")
    if not isinstance(child_rollouts, dict):
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "child rollouts must be keyed by thread identity")
    children: dict[str, list[dict[str, object]]] = {}
    for thread_id, records in child_rollouts.items():
        if not isinstance(thread_id, str) or not thread_id:
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "child rollout identity is invalid")
        if not isinstance(records, list):
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "child rollout records must be a list")
        children[thread_id] = _decode_event_records(records, "UNSUPPORTED_ROLLOUT_FORMAT")
    format_name = _rollout_format(parent, "UNSUPPORTED_ROLLOUT_FORMAT")
    if format_name == "current-direct-v1":
        for record in parent:
            _validate_current_event(record, "UNSUPPORTED_ROLLOUT_FORMAT")
    for records in children.values():
        for record in records:
            if format_name == "legacy-payload-v1" and not isinstance(record.get("payload"), dict):
                _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "legacy child record is not payload-wrapped")
            if format_name == "current-direct-v1":
                _validate_current_event(record, "UNSUPPORTED_ROLLOUT_FORMAT")
    if cli_version == LEGACY_ROLLOUT_VERSION and format_name != "legacy-payload-v1":
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "legacy CLI requires payload-wrapped rollout records")
    if cli_version == CURRENT_ROLLOUT_VERSION and format_name != "current-direct-v1":
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "current CLI requires direct rollout records")
    if cli_version not in {LEGACY_ROLLOUT_VERSION, CURRENT_ROLLOUT_VERSION}:
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", f"unsupported CLI version: {cli_version}")
    return {
        "schemaVersion": ROLLOUT_ADAPTER_SCHEMA_VERSION,
        "cliVersion": cli_version,
        "source": source,
        "format": format_name,
        "parentRecords": parent,
        "childRollouts": children,
    }


def parse_host_events(
    events: list[dict[str, object]] | list[str],
    cli_version: str = CURRENT_ROLLOUT_VERSION,
    source: str = "codex-exec-jsonl",
) -> dict[str, object]:
    """Parse direct host JSONL events before reducing them to handshake facts."""

    if not isinstance(cli_version, str) or not cli_version or not isinstance(source, str) or not source:
        _unsupported("UNSUPPORTED_HOST_EVENT_FORMAT", "CLI version and event source are required")
    if cli_version not in {LEGACY_ROLLOUT_VERSION, CURRENT_ROLLOUT_VERSION}:
        _unsupported("UNSUPPORTED_HOST_EVENT_FORMAT", f"unsupported CLI version: {cli_version}")
    if cli_version != CURRENT_ROLLOUT_VERSION:
        _unsupported("UNSUPPORTED_HOST_EVENT_FORMAT", "direct host JSONL requires the current CLI version")
    decoded = _decode_event_records(events, "UNSUPPORTED_HOST_EVENT_FORMAT")
    for event in decoded:
        _validate_current_event(event, "UNSUPPORTED_HOST_EVENT_FORMAT")
    return {
        "schemaVersion": ROLLOUT_ADAPTER_SCHEMA_VERSION,
        "cliVersion": cli_version,
        "source": source,
        "format": "direct-host-jsonl-v1",
        "events": decoded,
    }


def _event_item(event: dict[str, object]) -> dict[str, object]:
    item = event.get("item")
    return item if isinstance(item, dict) else {}


def _thread_ids(event: dict[str, object]) -> set[str]:
    identities: set[str] = set()
    thread_id = event.get("thread_id")
    if isinstance(thread_id, str) and thread_id:
        identities.add(thread_id)
    return identities


def _event_type(event: dict[str, object]) -> str:
    event_type = event.get("type")
    if not isinstance(event_type, str) or not event_type:
        return "unknown"
    item = _event_item(event)
    item_type = item.get("type")
    if isinstance(item_type, str) and item_type:
        return f"{event_type}:{item_type}"
    return event_type


def _host_error(events: list[dict[str, object]], stderr: str, repo: Path) -> dict[str, str] | None:
    for event in events:
        event_type = event.get("type")
        if event_type not in {"error", "turn.failed"}:
            continue
        error = event.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message")
        else:
            code = event_type
            message = event.get("message") or error
        return {
            "code": code if isinstance(code, str) and code else str(event_type).upper().replace(".", "_"),
            "message": _redact(message if isinstance(message, str) else "Codex host reported a failure", (repo,)),
        }
    if stderr.strip():
        return {"code": "CODEX_STDERR", "message": _redact(stderr, (repo,))}
    return None


def normalize_host_events(
    events: list[dict[str, object]],
    codex_exit_code: int,
    stderr: str,
    repo: Path,
    cli_version: str = CURRENT_ROLLOUT_VERSION,
    source: str = "codex-exec-jsonl",
) -> dict[str, object]:
    """Reduce one live JSONL stream to path-free host-owned facts."""
    parsed = parse_host_events(events, cli_version, source)
    events = parsed["events"]
    if any(
        event.get("type") in {"item.started", "item.completed"}
        and _event_item(event).get("type") == "collab_tool_call"
        for event in events
    ):
        _unsupported(
            "UNSUPPORTED_HOST_EVENT_FORMAT",
            "current collaboration item fields are unsupported without a redacted capture",
        )
    if any(event.get("type") == "turn.started" for event in events) and not any(
        event.get("type") in {"turn.completed", "turn.failed"} for event in events
    ):
        _unsupported("UNSUPPORTED_HOST_EVENT_FORMAT", "current host stream has no terminal turn event")
    event_types = []
    for event in events:
        value = _event_type(event)
        if value not in event_types:
            event_types.append(value)
    host_error = _host_error(events, stderr, repo)
    parent_terminal_observed = any(event.get("type") == "turn.completed" for event in events)
    return {
        "parentTurnEntered": any(event.get("type") == "turn.started" for event in events),
        "spawnCount": 0,
        "spawnFacts": [],
        "activatedRoles": [],
        "unexpectedRoles": [],
        "downgradeObserved": False,
        "fallbackObserved": False,
        "childBindingValid": False,
        "childThreadIdentityHash": None,
        "childTerminalObserved": False,
        "parentTerminalObserved": parent_terminal_observed,
        "codexExitCode": codex_exit_code,
        "eventTypes": event_types,
        "threadIdentityHashes": sorted({sha256_bytes(value.encode("utf-8")) for event in events for value in _thread_ids(event)}),
        "hostError": host_error,
    }


def _normalize_legacy_rollout_facts(
    parent_records: list[dict[str, object]],
    child_rollouts: dict[str, list[dict[str, object]]],
    parent_thread_id: str,
    codex_exit_code: int,
) -> dict[str, object]:
    """Normalize authorized Codex rollout facts without retaining prompt text."""
    event_types: list[str] = []
    for record in parent_records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        if not isinstance(payload_type, str):
            continue
        value = payload_type
        if payload_type == "function_call":
            value = f"function_call:{payload.get('namespace', '')}.{payload.get('name', '')}"
        elif payload_type == "function_call_output":
            value = "function_call_output"
        if value not in event_types:
            event_types.append(value)

    spawn_calls: list[dict[str, object]] = []
    for record in parent_records:
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "function_call":
            continue
        if payload.get("namespace") != "agents" or payload.get("name") != "spawn_agent":
            continue
        arguments = payload.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as error:
                _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", f"spawn arguments are not valid JSON: {error.msg}")
        if not isinstance(arguments, dict):
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "spawn arguments are not an object")
        if any(not isinstance(arguments.get(key), str) or not arguments[key] for key in ("agent_type", "task_name", "fork_turns")):
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "spawn arguments are missing required fields")
        spawn_calls.append(arguments)
    spawn_facts = [
        {
            "agentType": call.get("agent_type"),
            "taskName": call.get("task_name"),
            "forkTurns": call.get("fork_turns"),
        }
        for call in spawn_calls
    ]
    activities = [
        payload
        for record in parent_records
        if isinstance((payload := record.get("payload")), dict)
        and payload.get("type") == "sub_agent_activity"
        and payload.get("kind") == "started"
    ]
    matching_activities = [
        payload
        for payload in activities
        if payload.get("agent_path") == f"/root/{SPAWN_TASK_NAME}"
        and isinstance(payload.get("agent_thread_id"), str)
        and payload.get("agent_thread_id")
    ]
    child_thread_id = matching_activities[0]["agent_thread_id"] if len(matching_activities) == 1 else None
    child_records = child_rollouts.get(child_thread_id, []) if isinstance(child_thread_id, str) else []
    child_metas = [
        record.get("payload")
        for record in child_records
        if record.get("type") == "session_meta" and isinstance(record.get("payload"), dict)
    ]
    child_meta = child_metas[0] if len(child_metas) == 1 else None
    spawn_source = child_meta.get("source", {}).get("subagent", {}).get("thread_spawn", {}) if isinstance(child_meta, dict) else {}
    child_binding_valid = (
        isinstance(child_thread_id, str)
        and isinstance(child_meta, dict)
        and child_meta.get("id") == child_thread_id
        and child_meta.get("session_id") == parent_thread_id
        and child_meta.get("thread_source") == "subagent"
        and spawn_source.get("parent_thread_id") == parent_thread_id
        and spawn_source.get("agent_path") == f"/root/{SPAWN_TASK_NAME}"
        and spawn_source.get("agent_role") == ROLE_NAME
    )
    child_terminal = child_binding_valid and any(
        isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "task_complete"
        and record["payload"].get("last_agent_message") == CHILD_TERMINAL_MARKER
        for record in child_records
    )
    parent_terminal = any(
        isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "task_complete"
        and record["payload"].get("last_agent_message") == PARENT_TERMINAL_MARKER
        for record in parent_records
    )
    if len(spawn_calls) == 1:
        if child_binding_valid and not child_terminal:
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "bound child rollout has no terminal marker")
        if child_binding_valid and not parent_terminal:
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "parent rollout has no terminal marker")
    child_thread_ids = {
        payload["agent_thread_id"]
        for payload in activities
        if isinstance(payload.get("agent_thread_id"), str) and payload.get("agent_thread_id")
    }
    thread_identity_hashes = sorted(
        {sha256_bytes(identity.encode("utf-8")) for identity in {parent_thread_id, *child_thread_ids} if identity}
    )
    structured_roles = {
        role
        for role in [
            *(call.get("agent_type") for call in spawn_calls),
            *(meta.get("source", {}).get("subagent", {}).get("thread_spawn", {}).get("agent_role") for meta in child_metas),
        ]
        if isinstance(role, str) and role
    }
    roles = sorted(structured_roles)
    unexpected = sorted(role for role in roles if role != ROLE_NAME)
    fallback = any(role in FALLBACK_ROLES for role in unexpected)
    return {
        "parentTurnEntered": any(
            isinstance(record.get("payload"), dict) and record["payload"].get("type") == "task_started"
            for record in parent_records
        ),
        "spawnCount": len(spawn_calls),
        "spawnFacts": spawn_facts,
        "activatedRoles": roles,
        "unexpectedRoles": unexpected,
        "downgradeObserved": any(role != ROLE_NAME for role in roles),
        "fallbackObserved": fallback,
        "childBindingValid": child_binding_valid,
        "childThreadIdentityHash": sha256_bytes(child_thread_id.encode("utf-8")) if isinstance(child_thread_id, str) else None,
        "childTerminalObserved": child_terminal,
        "parentTerminalObserved": parent_terminal,
        "codexExitCode": codex_exit_code,
        "eventTypes": event_types,
        "threadIdentityHashes": thread_identity_hashes,
        "hostError": None,
    }


def _normalize_current_rollout_facts(
    parsed: dict[str, object],
    parent_thread_id: str,
    codex_exit_code: int,
) -> dict[str, object]:
    parent_records = parsed["parentRecords"]
    children = parsed["childRollouts"]
    all_records = [*parent_records, *(record for records in children.values() for record in records)]
    event_types: list[str] = []
    thread_ids: set[str] = {parent_thread_id}
    parent_thread_ids = {
        record.get("thread_id")
        for record in parent_records
        if record.get("type") == "thread.started" and isinstance(record.get("thread_id"), str)
    }
    if parent_thread_ids and parent_thread_ids != {parent_thread_id}:
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "current parent thread identity drifted")
    for thread_id, records in children.items():
        child_thread_ids = {
            record.get("thread_id")
            for record in records
            if record.get("type") == "thread.started" and isinstance(record.get("thread_id"), str)
        }
        if child_thread_ids and child_thread_ids != {thread_id}:
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "current child thread identity drifted")
    if any(record.get("type") == "turn.started" for record in parent_records) and not any(
        record.get("type") in {"turn.completed", "turn.failed"} for record in parent_records
    ):
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "current parent stream has no terminal turn event")
    for records in children.values():
        if any(record.get("type") == "turn.started" for record in records) and not any(
            record.get("type") in {"turn.completed", "turn.failed"} for record in records
        ):
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "current child stream has no terminal turn event")
    for record in all_records:
        _validate_current_event(record, "UNSUPPORTED_ROLLOUT_FORMAT")
        event_type = record["type"]
        item = record.get("item") if isinstance(record.get("item"), dict) else None
        item_type = item.get("type") if isinstance(item, dict) else None
        if item_type == "collab_tool_call":
            _unsupported(
                "UNSUPPORTED_ROLLOUT_FORMAT",
                "current collaboration item fields are unsupported without a redacted capture",
            )
        rendered_type = f"{event_type}:{item_type}" if isinstance(item_type, str) else event_type
        if rendered_type not in event_types:
            event_types.append(rendered_type)
        identity = record.get("thread_id")
        if isinstance(identity, str) and identity:
            thread_ids.add(identity)
    return {
        "parentTurnEntered": any(record.get("type") == "turn.started" for record in parent_records),
        "spawnCount": 0,
        "spawnFacts": [],
        "activatedRoles": [],
        "unexpectedRoles": [],
        "downgradeObserved": False,
        "fallbackObserved": False,
        "childBindingValid": False,
        "childThreadIdentityHash": None,
        "childTerminalObserved": False,
        "parentTerminalObserved": any(record.get("type") == "turn.completed" for record in parent_records),
        "codexExitCode": codex_exit_code,
        "eventTypes": event_types,
        "threadIdentityHashes": sorted(sha256_bytes(identity.encode("utf-8")) for identity in thread_ids),
        "hostError": None,
    }


def normalize_rollout_facts(
    parent_records: list[dict[str, object]] | list[str] | dict[str, object],
    child_rollouts: dict[str, list[dict[str, object]] | list[str]] | None = None,
    parent_thread_id: str | None = None,
    codex_exit_code: int = 0,
    cli_version: str = LEGACY_ROLLOUT_VERSION,
    source: str = "historical-rollout",
) -> dict[str, object]:
    """Normalize parsed rollout facts while keeping raw format metadata separate."""

    if isinstance(parent_records, dict) and "parentRecords" in parent_records:
        parsed = parent_records
    else:
        if child_rollouts is None or parent_thread_id is None:
            _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "child rollouts and parent thread identity are required")
        parsed = parse_rollout_records(parent_records, child_rollouts, cli_version, source)
    if parsed.get("schemaVersion") != ROLLOUT_ADAPTER_SCHEMA_VERSION or not isinstance(parsed.get("parentRecords"), list):
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "parsed rollout adapter metadata is invalid")
    if not isinstance(parent_thread_id, str) or not parent_thread_id:
        _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "parent thread identity is required")
    if parsed.get("format") == "legacy-payload-v1":
        return _normalize_legacy_rollout_facts(parsed["parentRecords"], parsed["childRollouts"], parent_thread_id, codex_exit_code)
    if parsed.get("format") == "current-direct-v1":
        return _normalize_current_rollout_facts(parsed, parent_thread_id, codex_exit_code)
    _unsupported("UNSUPPORTED_ROLLOUT_FORMAT", "unknown parsed rollout format")
    raise AssertionError("unreachable")


def run_live_argument_parser(codex: Path, repo: Path) -> dict[str, object]:
    production_before = _production_snapshot()
    repo_before = _repo_snapshot(repo)
    result = subprocess.run(
        live_argument_parser_command(codex, repo),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    production_after = _production_snapshot()
    repo_after = _repo_snapshot(repo)
    if result.returncode != 0:
        raise PreflightError("LIVE_COMMAND_PARSE_FAILED", _redact(result.stderr, (repo,)))
    if production_before != production_after:
        raise PreflightError("PRODUCTION_CONFIG_CHANGED", "normal user configuration changed during argument parsing")
    if repo_before != repo_after or repo_after["clean"] is not True:
        raise PreflightError("PROBE_REPO_CHANGED", "probe repository changed during argument parsing")
    return {"liveCommandParsed": True, "productionConfigUnchanged": True, "probeRepoUnchanged": True}


def _historical_negative(value: dict[str, object]) -> dict[str, object]:
    nested = value.get("historicalNegativeEvidence")
    if isinstance(nested, dict):
        value = nested
    expected = {
        "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
        "evidenceClass": "host-runtime-model-rejection",
        "codexExitCode": 1,
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        raise PreflightError("INVALID_HISTORICAL_HANDSHAKE", "historical handshake is not the fixed isolation-mode rejection")
    host_error = value.get("hostError")
    digest = value.get("handshakeDigest")
    if not isinstance(host_error, dict) or not isinstance(digest, str) or len(digest) != 64:
        raise PreflightError("INVALID_HISTORICAL_HANDSHAKE", "historical handshake evidence is incomplete")
    return {**expected, "hostError": host_error, "handshakeDigest": digest}


def _historical_compatibility(value: dict[str, object]) -> dict[str, object]:
    nested = value.get("historicalCompatibilityEvidence")
    if isinstance(nested, dict):
        compatibility = nested
    else:
        failure = value.get("preflightFailure")
        if not isinstance(failure, dict) or failure.get("code") != "USER_CONFIG_PARSE_FAILED":
            raise PreflightError("INVALID_HISTORICAL_HANDSHAKE", "historical strict-config compatibility evidence is missing")
        compatibility = {
            "failure": "USER_CONFIG_PARSE_FAILED",
            "evidenceClass": "strict-user-config-compatibility-rejection",
            "strictConfigUsed": True,
            "message": failure.get("message"),
            "modelInvocations": value.get("modelInvocations"),
            "liveAttemptsConsumed": value.get("liveAttemptsConsumed"),
            "preflightDigest": value.get("preflightDigest"),
        }
    expected = {
        "failure": "USER_CONFIG_PARSE_FAILED",
        "evidenceClass": "strict-user-config-compatibility-rejection",
        "strictConfigUsed": True,
        "modelInvocations": 0,
        "liveAttemptsConsumed": 0,
    }
    if any(compatibility.get(key) != expected_value for key, expected_value in expected.items()):
        raise PreflightError("INVALID_HISTORICAL_HANDSHAKE", "historical strict-config compatibility evidence is invalid")
    message = compatibility.get("message")
    digest = compatibility.get("preflightDigest")
    if not isinstance(message, str) or not message or not isinstance(digest, str) or len(digest) != 64:
        raise PreflightError("INVALID_HISTORICAL_HANDSHAKE", "historical strict-config compatibility evidence is incomplete")
    return {**expected, "message": message, "preflightDigest": digest}


def pending_handshake(preflight: dict[str, object], historical: dict[str, object]) -> dict[str, object]:
    requested = preflight["requestedRole"]
    if requested != {"name": ROLE_NAME, "model": ROLE_MODEL, "reasoningEffort": ROLE_REASONING_EFFORT, "sandbox": ROLE_SANDBOX}:
        raise PreflightError("PROBE_ROLE_CONFIG_DRIFT", "requested role configuration does not match the fixed handshake")
    value = {
        "schemaVersion": 2,
        "outcome": "ready_for_live_diagnosis",
        "error": "LIVE_DIAGNOSIS_PENDING",
        "evidenceClass": "deterministic-production-environment-preflight",
        "attempts": 0,
        "modelInvocations": 0,
        "liveAttemptsConsumed": 0,
        "pathFree": True,
        "realOneHourWaitRun": False,
        "requestedRole": requested,
        "parentConfigurationSource": "normal-user-config",
        "parentModelOverride": False,
        "parentReasoningEffortOverride": False,
        "parentStrictConfig": False,
        "boundDigests": {
            "bundleDigest": preflight["bundleDigest"],
            "roleDigest": preflight["roleDigest"],
            "configDigest": preflight["configDigest"],
            "projectConfigDigest": preflight["projectConfigDigest"],
            "probeInstructionsDigest": preflight["probeInstructionsDigest"],
            "skillDigests": preflight["skillDigests"],
        },
        "setupFacts": {
            "codexExecutableResolution": "command-v",
            "codexExecutableDigest": preflight["codexExecutableDigest"],
            "generatedProjectConfigParsed": preflight["generatedProjectConfigParsed"],
            "generatedRoleConfigParsed": preflight["generatedRoleConfigParsed"],
            "normalEnvironmentReachedNoTransport": preflight["normalEnvironmentReachedNoTransport"],
            "trustedProjectLayerLoaded": preflight["trustedProjectLayerLoaded"],
            "agentsEnabled": preflight["agentsEnabled"],
            "projectRoleDefinitionAccepted": preflight["projectRoleDefinitionAccepted"],
            "customRoleActivationProven": False,
            "liveCommandParsed": preflight["liveCommandParsed"],
            "probeRepoClean": preflight["probeRepo"]["clean"],
            "probeRepoUnchanged": preflight["probeRepoUnchanged"],
            "productionConfigUnchanged": preflight["productionConfigUnchanged"],
        },
        "preflightDigest": preflight["preflightDigest"],
        "historicalNegativeEvidence": _historical_negative(historical),
        "historicalCompatibilityEvidence": _historical_compatibility(historical),
    }
    value["handshakeDigest"] = digest_object(value)
    return value


def completed_handshake(preflight: dict[str, object], host_facts: dict[str, object]) -> dict[str, object]:
    requested = preflight["requestedRole"]
    if requested != {"name": ROLE_NAME, "model": ROLE_MODEL, "reasoningEffort": ROLE_REASONING_EFFORT, "sandbox": ROLE_SANDBOX}:
        raise PreflightError("PROBE_ROLE_CONFIG_DRIFT", "requested role configuration does not match the fixed handshake")
    expected_fact_keys = {
        "parentTurnEntered",
        "spawnCount",
        "spawnFacts",
        "activatedRoles",
        "unexpectedRoles",
        "downgradeObserved",
        "fallbackObserved",
        "childBindingValid",
        "childThreadIdentityHash",
        "childTerminalObserved",
        "parentTerminalObserved",
        "codexExitCode",
        "eventTypes",
        "threadIdentityHashes",
        "hostError",
    }
    if set(host_facts) != expected_fact_keys:
        raise PreflightError("INVALID_HOST_FACTS", "host facts do not match the minimal handshake schema")
    if not isinstance(host_facts["eventTypes"], list) or not host_facts["eventTypes"] or any(not isinstance(item, str) or not item for item in host_facts["eventTypes"]):
        raise PreflightError("INVALID_HOST_FACTS", "host event types are invalid")
    if not isinstance(host_facts["threadIdentityHashes"], list) or any(not isinstance(item, str) or len(item) != 64 for item in host_facts["threadIdentityHashes"]):
        raise PreflightError("INVALID_HOST_FACTS", "host thread identities are invalid")
    if not isinstance(host_facts["activatedRoles"], list) or not isinstance(host_facts["unexpectedRoles"], list):
        raise PreflightError("INVALID_HOST_FACTS", "host role facts are invalid")
    if not isinstance(host_facts["spawnFacts"], list) or any(
        not isinstance(item, dict)
        or set(item) != {"agentType", "taskName", "forkTurns"}
        for item in host_facts["spawnFacts"]
    ):
        raise PreflightError("INVALID_HOST_FACTS", "host spawn facts are invalid")
    child_identity = host_facts["childThreadIdentityHash"]
    if child_identity is not None and (not isinstance(child_identity, str) or len(child_identity) != 64):
        raise PreflightError("INVALID_HOST_FACTS", "host child identity is invalid")
    exact_spawn = {
        "agentType": ROLE_NAME,
        "taskName": SPAWN_TASK_NAME,
        "forkTurns": SPAWN_FORK_TURNS,
    }
    ready = (
        host_facts["parentTurnEntered"] is True
        and host_facts["spawnCount"] == 1
        and host_facts["spawnFacts"] == [exact_spawn]
        and host_facts["activatedRoles"] == [ROLE_NAME]
        and host_facts["unexpectedRoles"] == []
        and host_facts["downgradeObserved"] is False
        and host_facts["fallbackObserved"] is False
        and host_facts["childBindingValid"] is True
        and isinstance(child_identity, str)
        and child_identity in host_facts["threadIdentityHashes"]
        and host_facts["childTerminalObserved"] is True
        and host_facts["parentTerminalObserved"] is True
        and host_facts["codexExitCode"] == 0
        and host_facts["hostError"] is None
    )
    activation_missing = (
        host_facts["parentTurnEntered"] is True
        and host_facts["spawnCount"] == 0
        and host_facts["spawnFacts"] == []
        and host_facts["activatedRoles"] == []
        and host_facts["unexpectedRoles"] == []
        and host_facts["downgradeObserved"] is False
        and host_facts["fallbackObserved"] is False
        and host_facts["childBindingValid"] is False
        and host_facts["childThreadIdentityHash"] is None
        and host_facts["childTerminalObserved"] is False
        and host_facts["parentTerminalObserved"] is True
        and host_facts["codexExitCode"] == 0
        and host_facts["hostError"] is None
    )
    orchestration_miss = activation_missing and any("collab_tool_call:wait" in event_type for event_type in host_facts["eventTypes"])
    outcome = "role_handshake_ready" if ready else "blocked"
    error = None if ready else "PROBE_ORCHESTRATION_MISS_WAIT_BEFORE_SPAWN" if orchestration_miss else "CUSTOM_ROLE_ACTIVATION_MISSING" if activation_missing else "CUSTOM_ROLE_HANDSHAKE_INCOMPLETE"
    setup = dict(preflight["setupFacts"])
    setup["customRoleActivationProven"] = ready
    value = {
        "schemaVersion": 2,
        "outcome": outcome,
        "error": error,
        "evidenceClass": "host-runtime-events-plus-deterministic-preflight",
        "attempts": 1,
        "modelInvocations": 1,
        "liveAttemptsConsumed": 1,
        "pathFree": True,
        "realOneHourWaitRun": False,
        "requestedRole": requested,
        "parentConfigurationSource": preflight["parentConfigurationSource"],
        "parentModelOverride": preflight["parentModelOverride"],
        "parentReasoningEffortOverride": preflight["parentReasoningEffortOverride"],
        "parentStrictConfig": preflight["parentStrictConfig"],
        "boundDigests": preflight["boundDigests"],
        "setupFacts": setup,
        "preflightDigest": preflight["preflightDigest"],
        "hostFacts": host_facts,
        "historicalNegativeEvidence": _historical_negative(preflight),
        "historicalCompatibilityEvidence": _historical_compatibility(preflight),
    }
    value["handshakeDigest"] = digest_object(value)
    return value


def blocked_preflight_handshake(
    setup: dict[str, object],
    codex_digest: str,
    error: PreflightError,
    historical: dict[str, object],
    live_command_parsed: bool,
) -> dict[str, object]:
    requested = setup["requestedRole"]
    if requested != {"name": ROLE_NAME, "model": ROLE_MODEL, "reasoningEffort": ROLE_REASONING_EFFORT, "sandbox": ROLE_SANDBOX}:
        raise PreflightError("PROBE_ROLE_CONFIG_DRIFT", "requested role configuration does not match the fixed handshake")
    preflight_failure = {"code": error.code, "message": _redact(str(error), ())}
    preflight_digest = digest_object(
        {
            "boundDigests": {
                "bundleDigest": setup["bundleDigest"],
                "roleDigest": setup["roleDigest"],
                "configDigest": setup["configDigest"],
                "projectConfigDigest": setup["projectConfigDigest"],
                "probeInstructionsDigest": setup["probeInstructionsDigest"],
                "skillDigests": setup["skillDigests"],
            },
            "codexExecutableDigest": codex_digest,
            "failure": preflight_failure,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
        }
    )
    value = {
        "schemaVersion": 2,
        "outcome": "blocked",
        "error": "STATIC_PREFLIGHT_FAILED",
        "evidenceClass": "deterministic-production-environment-preflight-failure",
        "attempts": 0,
        "modelInvocations": 0,
        "liveAttemptsConsumed": 0,
        "pathFree": True,
        "realOneHourWaitRun": False,
        "requestedRole": requested,
        "parentConfigurationSource": "normal-user-config",
        "parentModelOverride": False,
        "parentReasoningEffortOverride": False,
        "parentStrictConfig": False,
        "boundDigests": {
            "bundleDigest": setup["bundleDigest"],
            "roleDigest": setup["roleDigest"],
            "configDigest": setup["configDigest"],
            "projectConfigDigest": setup["projectConfigDigest"],
            "probeInstructionsDigest": setup["probeInstructionsDigest"],
            "skillDigests": setup["skillDigests"],
        },
        "setupFacts": {
            "codexExecutableResolution": "command-v",
            "codexExecutableDigest": codex_digest,
            "generatedProjectConfigParsed": setup["generatedProjectConfigParsed"],
            "generatedRoleConfigParsed": setup["generatedRoleConfigParsed"],
            "normalEnvironmentReachedNoTransport": False,
            "trustedProjectLayerLoaded": False,
            "agentsEnabled": True,
            "projectRoleDefinitionAccepted": False,
            "customRoleActivationProven": False,
            "liveCommandParsed": live_command_parsed,
            "probeRepoClean": setup["probeRepo"]["clean"],
            "probeRepoUnchanged": True,
            "productionConfigUnchanged": True,
        },
        "preflightDigest": preflight_digest,
        "preflightFailure": preflight_failure,
        "historicalNegativeEvidence": _historical_negative(historical),
        "historicalCompatibilityEvidence": _historical_compatibility(historical),
    }
    value["handshakeDigest"] = digest_object(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--historical-handshake", type=Path)
    parser.add_argument("--handshake-output", type=Path)
    args = parser.parse_args()
    setup: dict[str, object] | None = None
    codex: Path | None = None
    production_before: dict[str, object] | None = None
    argument_facts: dict[str, object] | None = None
    try:
        codex = discover_codex()
        production_before = _production_snapshot()
        setup = prepare_probe_repo(args.bundle_root, args.repo)
        argument_facts = run_live_argument_parser(codex, args.repo)
        parser_facts = run_static_parser(codex, args.repo)
        version = subprocess.run(
            [codex.as_posix(), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        result: dict[str, object] = {
            "schemaVersion": 1,
            "outcome": "ready_for_live_diagnosis",
            "codexVersion": version,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
            "trustedProjectLayerLoaded": True,
            "agentsEnabled": True,
            "projectRoleDefinitionAccepted": True,
            "customRoleActivationProven": False,
            "roleName": ROLE_NAME,
            "codexExecutableResolution": "command-v",
            "codexExecutableDigest": sha256_bytes(codex.read_bytes()),
            **parser_facts,
            **argument_facts,
            **setup,
        }
        unsigned = dict(result)
        result["preflightDigest"] = digest_object(unsigned)
        if (args.historical_handshake is None) != (args.handshake_output is None):
            raise PreflightError("HANDSHAKE_OUTPUT_ARGUMENT_MISMATCH", "historical handshake and output must be supplied together")
        if args.historical_handshake is not None and args.handshake_output is not None:
            historical = read_canonical_json(args.historical_handshake, "INVALID_HISTORICAL_HANDSHAKE", lambda value: value)
            atomic_write(args.handshake_output, canonical_bytes(pending_handshake(result, historical)))
    except (OSError, subprocess.CalledProcessError, PreflightError) as error:
        production_after = _production_snapshot() if production_before is not None else None
        if production_before is not None and production_before != production_after:
            error = PreflightError("PRODUCTION_CONFIG_CHANGED", "normal user configuration changed during static preflight")
        code = error.code if isinstance(error, PreflightError) else "STATIC_PREFLIGHT_FAILED"
        result = {
            "schemaVersion": 1,
            "outcome": "blocked",
            "error": code,
            "message": _redact(str(error), (args.repo.resolve(),)),
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
            "productionConfigUnchanged": production_before == production_after if production_before is not None else False,
        }
        if args.historical_handshake is not None and args.handshake_output is not None and setup is not None and codex is not None and isinstance(error, PreflightError):
            historical = read_canonical_json(args.historical_handshake, "INVALID_HISTORICAL_HANDSHAKE", lambda value: value)
            atomic_write(args.handshake_output, canonical_bytes(blocked_preflight_handshake(setup, sha256_bytes(codex.read_bytes()), error, historical, argument_facts is not None and argument_facts["liveCommandParsed"] is True)))
        print(canonical_bytes(result).decode("utf-8"), end="")
        return 1
    print(canonical_bytes(result).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
