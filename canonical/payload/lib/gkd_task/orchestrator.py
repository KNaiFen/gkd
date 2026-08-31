"""Read-only trusted-main task context and managed planning packages."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from gkd_bundle import BundleError, verify_bundle_root
from gkd_ci.policy import load_policy_binding
from gkd_role.project import inspect_project_inventory

from .canonical import digest_object, require_sha256, require_string, sha256_bytes
from .documents import DOCUMENT_NAMES, inspect_package
from .errors import TaskError
from .gitops import branch, common_dir, git_root, reject_symlink_ancestors, repository_identity, unique_branch_worktree, verified_relative_path, verify_identity
from .model import read_state
from .runtime import RuntimeStore


HUMAN_INPUTS = ("requirements", "plan", "implementation")
PLANNING_PACKAGES = "planning-packages"


def _task_records(root: Path) -> list[tuple[str, dict[str, Any]]]:
    tasks = root / "tasks"
    if not tasks.exists():
        return []
    if tasks.is_symlink() or not tasks.is_dir():
        raise TaskError("TASK_CONTEXT_INVALID")
    result: list[tuple[str, dict[str, Any]]] = []
    pending = [tasks]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir(), reverse=True):
            if path.is_symlink():
                raise TaskError("TASK_CONTEXT_INVALID")
            if path.is_dir():
                pending.append(path)
            elif path.is_file() and path.name == "task.json":
                task_root = path.parent
                relative = task_root.relative_to(root).as_posix()
                result.append((relative, read_state(path, task_root)))
    return sorted(result, key=lambda item: item[0])


def _state_for_candidate(root: Path, task_id: str | None) -> tuple[str, dict[str, Any]] | None:
    identity = repository_identity(root)
    current_branch = branch(root)
    matches = [
        (task_path, state)
        for task_path, state in _task_records(root)
        if state["repository"]["identity"] == identity
        and state["repository"]["taskBranch"] == current_branch
        and (task_id is None or state["taskId"] == task_id)
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise TaskError("TASK_CONTEXT_AMBIGUOUS")
    task_path, state = matches[0]
    if state["repository"]["taskPath"] != task_path:
        raise TaskError("TASK_CONTEXT_INVALID")
    return task_path, state


def _runtime_for_current(current: Path, runtime: RuntimeStore | None) -> RuntimeStore:
    if runtime is not None:
        return runtime
    return RuntimeStore.open_existing(common_dir(git_root(current)) / "gkd-runtime")


def _attachment_candidate(attachment: dict[str, Any]) -> tuple[Path, str, dict[str, Any]]:
    repository = attachment["repository"]
    task_id = attachment["taskId"]
    task_branch = attachment["taskBranch"]
    task_path = attachment["taskPath"]
    candidate = Path(attachment["candidateRoot"])
    common = Path(attachment["commonDir"])
    reject_symlink_ancestors(candidate, "CANDIDATE_SYMLINK")
    reject_symlink_ancestors(common, "CANDIDATE_SYMLINK")
    root = verify_identity(candidate, repository, task_branch, common)
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
    return root, task_path, state


def _main_checkout(candidate: Path, state: dict[str, Any]) -> Path:
    repository = state["repository"]
    main = unique_branch_worktree(candidate, repository["baseBranch"])
    return verify_identity(
        main,
        repository["identity"],
        repository["baseBranch"],
        common_dir(candidate),
    )


@dataclass(frozen=True)
class TrustedTaskContext:
    """Private resolved facts with a path-free public projection."""

    candidate_root: Path
    trusted_main_root: Path
    runtime: RuntimeStore
    task_id: str
    task_path: str
    repository: str
    task_branch: str
    base_branch: str
    base_sha: str
    policy: dict[str, Any]
    bundle: dict[str, Any]
    project: dict[str, Any]
    snapshot: dict[str, Any]

    def inspect(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "taskSelector": self.task_id,
            "policyDigest": self.policy["digest"],
            "bundle": {
                "contentDigest": self.bundle["contentDigest"],
                "layout": self.bundle["layout"],
            },
            "projectInventoryDigest": self.project["inventoryDigest"],
            "snapshot": self.snapshot,
            "allowedNextActions": [
                "inspect",
                "preflight",
                "planning_create",
                "planning_inspect",
            ],
        }

    def preflight(self) -> dict[str, Any]:
        result = self.inspect()
        result["requiredHumanInputs"] = list(HUMAN_INPUTS)
        return result


def _build_context(
    candidate: Path,
    task_path: str,
    state: dict[str, Any],
    runtime: RuntimeStore,
    bundle_root: Path,
) -> TrustedTaskContext:
    repository = state["repository"]
    try:
        bundle = verify_bundle_root(bundle_root)
    except BundleError:
        raise TaskError("BUNDLE_CONTENT_MISMATCH") from None
    policy = repository.get("policy")
    if policy is None or load_policy_binding(candidate, repository["identity"]) != policy:
        raise TaskError("TASK_POLICY_MISMATCH")
    trusted_main = _main_checkout(candidate, state)
    project = inspect_project_inventory(trusted_main)
    if (
        project["executionBundleDigest"] != bundle["contentDigest"]
        or project.get("policy") != policy
    ):
        raise TaskError("PROJECT_CONTEXT_MISMATCH")
    claim = state["lifecycle"]["claim"]
    if claim is not None and "executionBundleDigest" in claim and claim["executionBundleDigest"] != bundle["contentDigest"]:
        raise TaskError("EXECUTION_BUNDLE_MISMATCH")
    snapshot = {
        "phase": state["lifecycle"]["phase"],
        "requirementsReady": state["documents"]["requirements"]["status"] == "ready",
        "planApproved": state["approval"] is not None,
        "implementationAuthorized": state["implementationAuthorization"] is not None,
        "blocked": state["lifecycle"]["blocked"] is not None,
    }
    return TrustedTaskContext(
        candidate_root=candidate,
        trusted_main_root=trusted_main,
        runtime=runtime,
        task_id=state["taskId"],
        task_path=task_path,
        repository=repository["identity"],
        task_branch=repository["taskBranch"],
        base_branch=repository["baseBranch"],
        base_sha=repository["baseSha"],
        policy=policy,
        bundle=bundle,
        project=project,
        snapshot=snapshot,
    )


def _attachment_contexts(
    runtime: RuntimeStore,
    bundle_root: Path,
    task_id: str | None,
    trusted_main: Path | None,
) -> list[TrustedTaskContext]:
    contexts: list[TrustedTaskContext] = []
    for attachment in runtime.attachments():
        if task_id is not None and attachment["taskId"] != task_id:
            continue
        candidate, task_path, state = _attachment_candidate(attachment)
        if trusted_main is not None:
            repository = state["repository"]
            if (
                common_dir(trusted_main) != common_dir(candidate)
                or branch(trusted_main) != repository["baseBranch"]
                or repository_identity(trusted_main) != repository["identity"]
            ):
                continue
        contexts.append(_build_context(candidate, task_path, state, runtime, bundle_root))
    return contexts


def resolve_trusted_task_context(
    current_path: Path,
    bundle_root: Path,
    task_id: str | None = None,
    runtime: RuntimeStore | None = None,
) -> TrustedTaskContext:
    """Resolve one task from candidate cwd, trusted-main cwd, or one attachment."""

    if task_id is not None:
        require_string(task_id, "INVALID_TASK_SELECTOR")
    reject_symlink_ancestors(current_path, "TASK_CONTEXT_SYMLINK")
    if current_path.is_symlink():
        raise TaskError("TASK_CONTEXT_SYMLINK")
    current = git_root(current_path)
    store = _runtime_for_current(current, runtime)
    if task_id is None:
        candidate_state = _state_for_candidate(current, None)
        if candidate_state is not None:
            task_path, state = candidate_state
            attachment = store.read_attachment_readonly(
                state["repository"]["identity"],
                state["taskId"],
                state["repository"]["taskBranch"],
            )
            candidate, attachment_path, attached_state = _attachment_candidate(attachment)
            if candidate != current or attachment_path != task_path or attached_state != state:
                raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
            return _build_context(candidate, task_path, state, store, bundle_root)
    else:
        try:
            attachment = store.read_attachment_readonly(
                repository_identity(current),
                task_id,
                branch(current),
            )
        except TaskError as error:
            if error.code != "worktree_missing":
                raise
        else:
            candidate, task_path, state = _attachment_candidate(attachment)
            if candidate != current:
                raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
            return _build_context(candidate, task_path, state, store, bundle_root)
    if task_id is None:
        raise TaskError("TASK_SELECTOR_REQUIRED")
    contexts = _attachment_contexts(store, bundle_root, task_id, current)
    if not contexts:
        raise TaskError("TASK_CONTEXT_NOT_FOUND")
    if len(contexts) != 1:
        raise TaskError("TASK_CONTEXT_AMBIGUOUS")
    return contexts[0]


def resolve_trusted_task_context_from_runtime(
    runtime: RuntimeStore,
    bundle_root: Path,
    task_id: str | None = None,
) -> TrustedTaskContext:
    """Resolve one unique attachment for trusted code that already owns the runtime."""

    if task_id is not None:
        require_string(task_id, "INVALID_TASK_SELECTOR")
    contexts = _attachment_contexts(runtime, bundle_root, task_id, None)
    if not contexts:
        raise TaskError("TASK_CONTEXT_NOT_FOUND")
    if len(contexts) != 1:
        raise TaskError("TASK_CONTEXT_AMBIGUOUS")
    return contexts[0]


class PlanningPackageStore:
    """Private, atomic package publisher associated with one existing runtime."""

    def __init__(self, runtime: RuntimeStore) -> None:
        self.runtime = runtime

    def _root(self, create: bool) -> Path | None:
        root = self.runtime.root / PLANNING_PACKAGES
        if root.exists() or root.is_symlink():
            if root.is_symlink() or not root.is_dir():
                raise TaskError("INVALID_PLANNING_PACKAGE")
            return root
        if not create:
            return None
        root.mkdir(mode=0o700)
        return root

    @staticmethod
    def _validate_raw(raw_documents: dict[str, str]) -> tuple[dict[str, bytes], dict[str, Any]]:
        if set(raw_documents) != set(DOCUMENT_NAMES) or any(not isinstance(value, str) for value in raw_documents.values()):
            raise TaskError("INVALID_PLANNING_DOCUMENT")
        try:
            encoded = {name: raw_documents[name].encode("utf-8") for name in DOCUMENT_NAMES}
        except UnicodeEncodeError:
            raise TaskError("INVALID_PLANNING_DOCUMENT") from None
        with tempfile.TemporaryDirectory(prefix="gkd-planning-validate-") as directory:
            root = Path(directory)
            for name in DOCUMENT_NAMES:
                (root / name).write_bytes(encoded[name])
            records, _ = inspect_package(root)
        return encoded, records

    @staticmethod
    def _selector(records: dict[str, Any]) -> str:
        return digest_object({name: records[name]["digest"] for name in sorted(records)})

    @staticmethod
    def _inspect_exact(root: Path) -> dict[str, Any]:
        if root.is_symlink() or not root.is_dir():
            raise TaskError("INVALID_PLANNING_PACKAGE")
        if sorted(path.name for path in root.iterdir()) != sorted(DOCUMENT_NAMES):
            raise TaskError("INVALID_PLANNING_PACKAGE")
        return inspect_package(root)[0]

    def create(self, raw_documents: dict[str, str]) -> dict[str, Any]:
        encoded, records = self._validate_raw(raw_documents)
        selector = self._selector(records)
        root = self._root(create=True)
        if root is None:
            raise TaskError("INVALID_PLANNING_PACKAGE")
        destination = root / selector
        if destination.exists() or destination.is_symlink():
            if self._inspect_exact(destination) != records:
                raise TaskError("INVALID_PLANNING_PACKAGE")
            return {"status": "already_created", "packageSelector": selector, "packageDigest": selector}
        staging = Path(tempfile.mkdtemp(prefix=".planning-", dir=root))
        try:
            for name in DOCUMENT_NAMES:
                path = staging / name
                path.write_bytes(encoded[name])
                os.chmod(path, 0o600)
            if self._inspect_exact(staging) != records:
                raise TaskError("INVALID_PLANNING_PACKAGE")
            os.replace(staging, destination)
        except OSError:
            raise TaskError("PLANNING_PACKAGE_PUBLISH_FAILED") from None
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return {"status": "created", "packageSelector": selector, "packageDigest": selector}

    def inspect(self, selector: str) -> dict[str, Any]:
        require_sha256(selector, "INVALID_PLANNING_SELECTOR")
        root = self._root(create=False)
        if root is None:
            return {
                "status": "missing",
                "packageSelector": selector,
                "missingHumanInputs": list(HUMAN_INPUTS),
            }
        package = root / selector
        if not package.exists() and not package.is_symlink():
            return {
                "status": "missing",
                "packageSelector": selector,
                "missingHumanInputs": list(HUMAN_INPUTS),
            }
        records = self._inspect_exact(package)
        if self._selector(records) != selector:
            raise TaskError("INVALID_PLANNING_PACKAGE")
        return {
            "status": "ready",
            "packageSelector": selector,
            "packageDigest": selector,
            "missingHumanInputs": [],
        }
