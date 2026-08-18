"""Portable, fail-closed candidate discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import TaskError
from .gitops import branch, common_dir, git_root, repository_identity, unique_branch_worktree, verified_relative_path, verify_identity
from .model import read_state
from .runtime import RuntimeStore


def _validated_candidate(
    candidate: Path,
    repository: str,
    task_id: str,
    task_branch: str,
    task_path: str,
    expected_common: Path | None = None,
) -> Path:
    root = verify_identity(candidate.resolve(), repository, task_branch, expected_common)
    task_root = verified_relative_path(root, task_path)
    state = read_state(task_root / "task.json", task_root)
    durable = state["repository"]
    if (
        state["taskId"] != task_id
        or durable["identity"] != repository
        or durable["taskBranch"] != task_branch
        or durable["taskPath"] != task_path
    ):
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    return root


def resolve_candidate(
    repository: str,
    task_id: str,
    task_branch: str,
    task_path: str,
    runtime: RuntimeStore,
    explicit_candidate: Path | None = None,
    current_path: Path | None = None,
) -> Path:
    if explicit_candidate is not None:
        return _validated_candidate(explicit_candidate, repository, task_id, task_branch, task_path)

    anchor: Path | None = None
    anchor_common: Path | None = None
    if current_path is not None:
        try:
            anchor = git_root(current_path)
            anchor_common = common_dir(anchor)
        except TaskError:
            anchor = None
            anchor_common = None
        if anchor is not None and branch(anchor) == task_branch:
            try:
                return _validated_candidate(anchor, repository, task_id, task_branch, task_path, anchor_common)
            except TaskError as error:
                if error.code not in {"INVALID_TASK_STATE", "CANDIDATE_IDENTITY_MISMATCH"}:
                    raise
        if anchor is not None and repository_identity(anchor) == repository:
            try:
                candidate = unique_branch_worktree(anchor, task_branch)
                return _validated_candidate(candidate, repository, task_id, task_branch, task_path, anchor_common)
            except TaskError as error:
                if error.code not in {"worktree_missing"}:
                    raise

    try:
        attachment = runtime.read_attachment(repository, task_id, task_branch)
    except TaskError as error:
        if error.code == "worktree_missing":
            raise TaskError("worktree_missing") from None
        raise
    candidate = Path(attachment["candidateRoot"])
    expected_common = Path(attachment["commonDir"])
    return _validated_candidate(candidate, repository, task_id, task_branch, task_path, expected_common)
