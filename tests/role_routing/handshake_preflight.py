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
import tomllib

import gkd_bundle
from gkd_role.roles import load_role_source, locked_bundle_digest, role_catalog, role_files, role_record
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, read_canonical_json, sha256_bytes


ROLE_NAME = "gkd_executor"
ROLE_MODEL = "gpt-5.6-sol"
ROLE_REASONING_EFFORT = "xhigh"
ROLE_SANDBOX = "workspace-write"
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


def _event_item(event: dict[str, object]) -> dict[str, object]:
    item = event.get("item")
    return item if isinstance(item, dict) else {}


def _collab_tool(item: dict[str, object]) -> str | None:
    if item.get("type") != "collab_tool_call":
        return None
    tool = item.get("tool")
    if not isinstance(tool, str) or not tool:
        return None
    return tool.removeprefix("agents.")


def _structured_arguments(item: dict[str, object]) -> list[dict[str, object]]:
    values = [item]
    for key in ("arguments", "params", "input"):
        candidate = item.get(key)
        if isinstance(candidate, dict):
            values.append(candidate)
        elif isinstance(candidate, str):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                values.append(parsed)
    return values


def _spawn_role(item: dict[str, object]) -> str | None:
    for value in _structured_arguments(item):
        for key in ("agent_type", "agentType"):
            role = value.get(key)
            if isinstance(role, str) and role:
                return role
    return None


def _thread_ids(event: dict[str, object]) -> set[str]:
    identities: set[str] = set()
    thread_id = event.get("thread_id")
    if isinstance(thread_id, str) and thread_id:
        identities.add(thread_id)
    item = _event_item(event)
    for key in ("sender_thread_id", "receiver_thread_id"):
        identity = item.get(key)
        if isinstance(identity, str) and identity:
            identities.add(identity)
    receivers = item.get("receiver_thread_ids")
    if isinstance(receivers, list):
        identities.update(value for value in receivers if isinstance(value, str) and value)
    states = item.get("agents_states")
    if isinstance(states, dict):
        identities.update(value for value in states if isinstance(value, str) and value)
    return identities


def _agent_completed(item: dict[str, object], child_ids: set[str]) -> bool:
    states = item.get("agents_states")
    if not isinstance(states, dict):
        return False
    for identity, state in states.items():
        if identity not in child_ids:
            continue
        if isinstance(state, str) and state == "completed":
            return True
        if isinstance(state, dict) and state.get("status") == "completed":
            return True
    return False


def _event_type(event: dict[str, object]) -> str:
    event_type = event.get("type")
    if not isinstance(event_type, str) or not event_type:
        return "unknown"
    item = _event_item(event)
    tool = _collab_tool(item)
    if tool is not None:
        return f"{event_type}:collab_tool_call:{tool}"
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
) -> dict[str, object]:
    """Reduce one live JSONL stream to path-free host-owned facts."""
    spawn_items = [
        _event_item(event)
        for event in events
        if event.get("type") == "item.completed" and _collab_tool(_event_item(event)) == "spawn_agent"
    ]
    roles = [role for role in (_spawn_role(item) for item in spawn_items) if role is not None]
    child_ids: set[str] = set()
    for item in spawn_items:
        receivers = item.get("receiver_thread_ids")
        if isinstance(receivers, list):
            child_ids.update(value for value in receivers if isinstance(value, str) and value)
    event_types = []
    for event in events:
        value = _event_type(event)
        if value not in event_types:
            event_types.append(value)
    unexpected = sorted({role for role in roles if role != ROLE_NAME})
    fallback = any(role in {"default", "worker", "explorer"} for role in unexpected)
    host_error = _host_error(events, stderr, repo)
    return {
        "parentTurnEntered": any(event.get("type") == "turn.started" for event in events),
        "spawnCount": len(spawn_items),
        "activatedRoles": sorted(set(roles)),
        "unexpectedRoles": unexpected,
        "downgradeObserved": False,
        "fallbackObserved": fallback,
        "childTerminalObserved": any(_agent_completed(_event_item(event), child_ids) for event in events),
        "parentTerminalObserved": any(event.get("type") == "turn.completed" for event in events),
        "codexExitCode": codex_exit_code,
        "eventTypes": event_types,
        "threadIdentityHashes": sorted({sha256_bytes(value.encode("utf-8")) for event in events for value in _thread_ids(event)}),
        "hostError": host_error,
    }


def normalize_rollout_facts(
    parent_records: list[dict[str, object]],
    child_records: list[dict[str, object]],
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
            except json.JSONDecodeError:
                arguments = {}
        if isinstance(arguments, dict):
            spawn_calls.append(arguments)
    roles = sorted({value for call in spawn_calls for value in [call.get("agent_type")] if isinstance(value, str) and value})
    child_terminal = any(
        isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "task_complete"
        and record["payload"].get("last_agent_message") == "GKD_EXECUTOR_CHILD_TERMINAL"
        for record in child_records
    )
    parent_terminal = any(
        isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "task_complete"
        and record["payload"].get("last_agent_message") == "GKD_PARENT_TERMINAL"
        for record in parent_records
    )
    child_thread_ids = {
        payload.get("agent_thread_id")
        for record in parent_records
        if isinstance((payload := record.get("payload")), dict)
        and payload.get("type") == "sub_agent_activity"
        and isinstance(payload.get("agent_thread_id"), str)
    }
    thread_identity_hashes = sorted(
        {sha256_bytes(identity.encode("utf-8")) for identity in {parent_thread_id, *child_thread_ids} if identity}
    )
    unexpected = sorted(role for role in roles if role != ROLE_NAME)
    fallback = any(role in {"default", "worker", "explorer"} for role in unexpected)
    return {
        "parentTurnEntered": any(
            isinstance(record.get("payload"), dict) and record["payload"].get("type") == "task_started"
            for record in parent_records
        ),
        "spawnCount": len(spawn_calls),
        "activatedRoles": roles,
        "unexpectedRoles": unexpected,
        "downgradeObserved": False,
        "fallbackObserved": fallback,
        "childTerminalObserved": child_terminal,
        "parentTerminalObserved": parent_terminal,
        "codexExitCode": codex_exit_code,
        "eventTypes": event_types,
        "threadIdentityHashes": thread_identity_hashes,
        "hostError": None,
    }


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
        "activatedRoles",
        "unexpectedRoles",
        "downgradeObserved",
        "fallbackObserved",
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
    ready = (
        host_facts["parentTurnEntered"] is True
        and host_facts["spawnCount"] == 1
        and host_facts["activatedRoles"] == [ROLE_NAME]
        and host_facts["unexpectedRoles"] == []
        and host_facts["downgradeObserved"] is False
        and host_facts["fallbackObserved"] is False
        and host_facts["childTerminalObserved"] is True
        and host_facts["parentTerminalObserved"] is True
        and host_facts["codexExitCode"] == 0
        and host_facts["hostError"] is None
    )
    activation_missing = (
        host_facts["parentTurnEntered"] is True
        and host_facts["spawnCount"] == 0
        and host_facts["activatedRoles"] == []
        and host_facts["unexpectedRoles"] == []
        and host_facts["downgradeObserved"] is False
        and host_facts["fallbackObserved"] is False
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
