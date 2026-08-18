"""Idempotent migration for the legacy v1 tracked worktree path."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes, digest_object, read_canonical_json, require_keys, require_sha256
from .errors import TaskError
from .gitops import common_dir, head, verify_identity
from .model import advance_state, validate_state
from .runtime import RUNTIME_SCHEMA_VERSION, RuntimeStore, runtime_key
from .transaction import TransactionChange, TransactionManager


def validate_legacy_v1(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "kind", "task", "worktreePath", "archived", "legacyDigest"},
        "INVALID_LEGACY_STATE",
    )
    if value["schemaVersion"] != 1 or value["kind"] != "legacy-v1-task-path" or not isinstance(value["archived"], bool):
        raise TaskError("INVALID_LEGACY_STATE")
    if value["worktreePath"] is not None and (not isinstance(value["worktreePath"], str) or not value["worktreePath"].startswith("/")):
        raise TaskError("INVALID_LEGACY_STATE")
    if not isinstance(value["task"], dict):
        raise TaskError("INVALID_LEGACY_STATE")
    validate_state(value["task"])
    require_sha256(value["legacyDigest"], "INVALID_LEGACY_STATE")
    unsigned = deepcopy(value)
    actual = unsigned.pop("legacyDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_LEGACY_STATE")


def make_legacy_v1(state: dict[str, Any], worktree_path: str | None, archived: bool) -> dict[str, Any]:
    validate_state(state)
    value = {
        "schemaVersion": 1,
        "kind": "legacy-v1-task-path",
        "task": deepcopy(state),
        "worktreePath": worktree_path,
        "archived": archived,
    }
    value["legacyDigest"] = digest_object(value)
    validate_legacy_v1(value)
    return value


def migrate_v1(
    git_root: Path,
    task_path: str,
    runtime: RuntimeStore,
    expected_head: str,
    expected_revision: int,
    clock: Any,
    nonce: Any,
) -> dict[str, Any]:
    state_path = git_root / task_path / "task.json"
    try:
        current = read_canonical_json(state_path, "INVALID_TASK_STATE")
        validate_state(current)
    except TaskError as current_error:
        if current_error.code not in {"INVALID_TASK_STATE", "TASK_STATE_TAMPERED"}:
            raise
    else:
        return {
            "status": "already_migrated",
            "taskId": current["taskId"],
            "revision": current["revision"],
            "head": head(git_root),
        }

    legacy = read_canonical_json(state_path, "INVALID_LEGACY_STATE", validate_legacy_v1)
    state = legacy["task"]
    if state["revision"] != expected_revision:
        raise TaskError("REVISION_MISMATCH")
    repository = state["repository"]
    key = runtime_key(repository["identity"], state["taskId"], repository["taskBranch"])
    if legacy["archived"]:
        if state["lifecycle"]["phase"] != "completed":
            raise TaskError("INVALID_LEGACY_STATE")
    else:
        if legacy["worktreePath"] is None:
            raise TaskError("worktree_missing")
        old_root = Path(legacy["worktreePath"])
        if not old_root.is_dir() or old_root.is_symlink():
            raise TaskError("worktree_missing")
        if old_root.resolve() != git_root.resolve():
            raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
        verify_identity(old_root.resolve(), repository["identity"], repository["taskBranch"])

    manager = TransactionManager(git_root, task_path, runtime, key, clock, nonce)

    def loader() -> dict[str, Any]:
        raw = read_canonical_json(state_path, "INVALID_LEGACY_STATE", validate_legacy_v1)
        return raw["task"]

    runtime_change: dict[str, Any] = {"attempted": False, "previous": None}

    def builder(loaded: dict[str, Any]) -> TransactionChange:
        try:
            runtime_change["previous"] = runtime.read_attachment(
                repository["identity"], state["taskId"], repository["taskBranch"]
            )
        except TaskError as error:
            if error.code != "worktree_missing":
                raise
        runtime_change["attempted"] = True
        if legacy["archived"]:
            runtime.delete_attachment(repository["identity"], state["taskId"], repository["taskBranch"])
        else:
            runtime.write_attachment(
                {
                    "schemaVersion": RUNTIME_SCHEMA_VERSION,
                    "kind": "attachment",
                    "repository": repository["identity"],
                    "taskId": state["taskId"],
                    "taskBranch": repository["taskBranch"],
                    "taskPath": repository["taskPath"],
                    "candidateRoot": os.fspath(git_root.resolve()),
                    "commonDir": os.fspath(common_dir(git_root)),
                    "updatedAt": clock.now(),
                }
            )
        record = {"legacyDigest": legacy["legacyDigest"], "archived": legacy["archived"]}
        updated = advance_state(loaded, "migrated_v1", clock.now(), expected_head, record)
        return TransactionChange(
            {f"{task_path}/task.json": canonical_bytes(updated)},
            "迁移任务定位记录",
            {"status": "migrated_v1", "taskId": updated["taskId"], "revision": updated["revision"]},
        )

    try:
        return manager.execute(expected_head, expected_revision, builder, state_loader=loader)
    except Exception:
        try:
            if runtime_change["attempted"] and head(git_root) == expected_head:
                if runtime_change["previous"] is None:
                    runtime.delete_attachment(repository["identity"], state["taskId"], repository["taskBranch"])
                else:
                    runtime.write_attachment(runtime_change["previous"])
        except Exception:
            pass
        raise
