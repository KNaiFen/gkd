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
import tempfile

from gkd_role.roles import load_role_source, locked_bundle_digest, role_catalog, role_files, role_record
from gkd_task.canonical import canonical_bytes, digest_object, sha256_bytes


ROLE_NAME = "gkd_executor"
PARSER_SENTINEL = "no transport configured; use --listen or enable remote control"
LIVE_PROMPT = (
    "Perform one no-side-effect custom-role handshake. Spawn exactly one agent with "
    'agent_type="gkd_executor", task_name="gkd_executor_handshake", and fork_turns="none". '
    "The child must not read or modify any repository file and must return exactly "
    "GKD_EXECUTOR_CHILD_TERMINAL. After that child reaches terminal state, return exactly "
    "GKD_PARENT_TERMINAL. Do not spawn another agent, retry, change role, or change model."
)


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


def trust_override(repo: Path) -> str:
    canonical_repo = repo.resolve()
    return f"projects={{{json.dumps(canonical_repo.as_posix())}={{trust_level=\"trusted\"}}}}"


def _project_config(description: str) -> bytes:
    return (
        "[agents]\n"
        "enabled = true\n"
        "\n"
        f"[agents.{ROLE_NAME}]\n"
        f"description = {json.dumps(description, ensure_ascii=True)}\n"
        f'config_file = "agents/{ROLE_NAME}.toml"\n'
    ).encode("utf-8")


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

    actual_skills = {name: _skill_tree_digest(skills / name) for name in role["skills"]}
    expected_skills = {name: catalog["skillDigests"][name] for name in role["skills"]}
    if sha256_bytes(role_bytes) != role["configDigest"] or actual_skills != expected_skills:
        raise PreflightError("PROBE_DIGEST_MISMATCH", "generated role or Skill bytes do not match the fixed bundle")

    add_result = subprocess.run(
        ["git", "add", "--", ".codex"],
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
        "skillDigests": actual_skills,
        "repoIdentitySha256": _path_hash(repo),
    }


def static_parser_command(codex: str, repo: Path) -> list[str]:
    return [
        codex,
        "app-server",
        "--strict-config",
        "--listen",
        "off",
        "-c",
        trust_override(repo),
        "-c",
        "agents.enabled=true",
    ]


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
    if "unknown configuration field" in combined or "Error parsing project config" in combined:
        raise PreflightError("PROJECT_CONFIG_PARSE_FAILED", "Codex rejected the project configuration")
    if returncode != 1 or PARSER_SENTINEL not in stderr:
        raise PreflightError("STATIC_PARSER_UNEXPECTED_RESULT", "Codex did not reach the expected no-transport boundary")


def run_static_parser(codex: str, repo: Path) -> str:
    repo = repo.resolve()
    with tempfile.TemporaryDirectory(prefix="gkd-codex-parser-", dir=repo.parent) as home_name:
        parser_home = Path(home_name).resolve()
        environment = dict(os.environ)
        environment["CODEX_HOME"] = parser_home.as_posix()
        result = subprocess.run(
            static_parser_command(codex, repo),
            cwd=repo,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        try:
            classify_parser_result(result.returncode, result.stdout, result.stderr)
        except PreflightError as error:
            raise PreflightError(error.code, _redact(f"{error}: {result.stderr}", (repo, parser_home))) from error
    return "loaded_before_no_transport"


def live_command(codex: str, repo: Path) -> list[str]:
    repo = repo.resolve()
    return [
        codex,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--json",
        "--cd",
        repo.as_posix(),
        "--model",
        "gpt-5.6-sol",
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "-c",
        'model_reasoning_effort="xhigh"',
        "-c",
        trust_override(repo),
        "-c",
        "agents.enabled=true",
        LIVE_PROMPT,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    try:
        setup = prepare_probe_repo(args.bundle_root, args.repo)
        parser_outcome = run_static_parser(args.codex, args.repo)
        version = subprocess.run(
            [args.codex, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        result = {
            "schemaVersion": 1,
            "outcome": "ready_for_authorized_live_probe",
            "codexVersion": version,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
            "trustedProjectLayerLoaded": True,
            "agentsEnabled": True,
            "customRoleDiscovered": True,
            "roleName": ROLE_NAME,
            "parserOutcome": parser_outcome,
            **setup,
        }
    except (OSError, subprocess.CalledProcessError, PreflightError) as error:
        code = error.code if isinstance(error, PreflightError) else "STATIC_PREFLIGHT_FAILED"
        result = {
            "schemaVersion": 1,
            "outcome": "blocked",
            "error": code,
            "message": _redact(str(error), (args.repo.resolve(),)),
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
        }
        print(canonical_bytes(result).decode("utf-8"), end="")
        return 1
    print(canonical_bytes(result).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
