"""Trusted fixed-tree acceptance and one-shot conditional merge."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import stat
import subprocess
from typing import Any, Protocol

from .canonical import canonical_bytes, digest_object, require_keys, require_sha1, require_sha256, require_string, sha256_bytes
from .documents import PLAN_MATERIAL_SECTIONS, PLAN_SECTIONS, parse_sections
from .errors import TaskError
from .gitops import branch, changed_paths, common_dir, git, head, is_ancestor, is_clean, read_tree_file, repository_identity, verify_identity
from .model import validate_authorization, validate_offer, validate_state


class MergeIndeterminate(Exception):
    """The adapter cannot tell whether the single merge write took effect."""


class GitHubAdapter(Protocol):
    def snapshot(self, repository: str, pr_number: int) -> dict[str, Any]: ...

    def merge(self, repository: str, pr_number: int, expected_head: str) -> dict[str, Any]: ...


def validate_snapshot(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "repository",
            "prNumber",
            "baseBranch",
            "headBranch",
            "headSha",
            "state",
            "draft",
            "mergeable",
            "checks",
            "mergedHead",
        },
        "INVALID_GITHUB_RESPONSE",
    )
    for field in ("repository", "baseBranch", "headBranch"):
        require_string(value[field], "INVALID_GITHUB_RESPONSE")
    if not isinstance(value["prNumber"], int) or value["prNumber"] < 1:
        raise TaskError("INVALID_GITHUB_RESPONSE")
    require_sha1(value["headSha"], "INVALID_GITHUB_RESPONSE")
    if value["state"] not in {"open", "closed", "merged"} or not isinstance(value["draft"], bool) or not isinstance(value["mergeable"], bool):
        raise TaskError("INVALID_GITHUB_RESPONSE")
    if value["mergedHead"] is not None:
        require_sha1(value["mergedHead"], "INVALID_GITHUB_RESPONSE")
    if not isinstance(value["checks"], list):
        raise TaskError("INVALID_GITHUB_RESPONSE")
    names: list[str] = []
    for check in value["checks"]:
        if not isinstance(check, dict):
            raise TaskError("INVALID_GITHUB_RESPONSE")
        require_keys(check, {"name", "status"}, "INVALID_GITHUB_RESPONSE")
        require_string(check["name"], "INVALID_GITHUB_RESPONSE")
        if check["status"] not in {"success", "failure", "pending", "skipped"}:
            raise TaskError("INVALID_GITHUB_RESPONSE")
        names.append(check["name"])
    if len(names) != len(set(names)):
        raise TaskError("INVALID_GITHUB_RESPONSE")


def validate_review(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "taskId", "candidateHead", "reviewerRole", "reviewerDigest", "outcome", "findings", "reviewDigest"},
        "INVALID_REVIEW",
    )
    if value["schemaVersion"] != 1 or value["reviewerRole"] not in {"acceptor", "main"} or value["outcome"] not in {"accepted", "rejected"}:
        raise TaskError("INVALID_REVIEW")
    require_string(value["taskId"], "INVALID_REVIEW")
    require_sha1(value["candidateHead"], "INVALID_REVIEW")
    require_sha256(value["reviewerDigest"], "INVALID_REVIEW")
    if not isinstance(value["findings"], list) or any(not isinstance(item, str) or not item for item in value["findings"]):
        raise TaskError("INVALID_REVIEW")
    require_sha256(value["reviewDigest"], "INVALID_REVIEW")
    unsigned = deepcopy(value)
    actual = unsigned.pop("reviewDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_REVIEW")


def make_review(
    task_id: str,
    candidate_head: str,
    reviewer_role: str,
    reviewer_digest: str,
    outcome: str,
    findings: list[str],
) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "taskId": task_id,
        "candidateHead": candidate_head,
        "reviewerRole": reviewer_role,
        "reviewerDigest": reviewer_digest,
        "outcome": outcome,
        "findings": findings,
    }
    value["reviewDigest"] = digest_object(value)
    validate_review(value)
    return value


def _fixed_json(root: Path, commit: str, path: str, code: str) -> dict[str, Any]:
    raw = read_tree_file(root, commit, path)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError(code) from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError(code)
    return value


def _validate_fixed_candidate(
    candidate_root: Path,
    task_path: str,
    candidate_head: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if head(candidate_root) != candidate_head or not is_clean(candidate_root):
        raise TaskError("candidate_head_changed")
    state = _fixed_json(candidate_root, candidate_head, f"{task_path}/task.json", "CANDIDATE_INVALID")
    validate_state(state)
    authorization = _fixed_json(candidate_root, candidate_head, f"{task_path}/authorization.json", "INVALID_AUTHORIZATION")
    validate_authorization(authorization)
    requirements = read_tree_file(candidate_root, candidate_head, f"{task_path}/requirements.md")
    plan = read_tree_file(candidate_root, candidate_head, f"{task_path}/plan.md")
    implementation = read_tree_file(candidate_root, candidate_head, f"{task_path}/implementation.md")
    plan_sections = parse_sections(plan, PLAN_SECTIONS)
    if __import__("hashlib").sha256(requirements).hexdigest() != state["documents"]["requirements"]["digest"]:
        raise TaskError("CANDIDATE_INVALID")
    if __import__("hashlib").sha256(plan).hexdigest() != state["documents"]["plan"]["digest"]:
        raise TaskError("CANDIDATE_INVALID")
    material = {name: plan_sections[name] for name in PLAN_MATERIAL_SECTIONS}
    if sha256_bytes(canonical_bytes(material)) != state["documents"]["plan"]["materialDigest"]:
        raise TaskError("CANDIDATE_INVALID")
    if __import__("hashlib").sha256(implementation).hexdigest() != state["documents"]["implementation"]["digest"]:
        raise TaskError("CANDIDATE_INVALID")
    claim = state["lifecycle"]["claim"]
    if claim is None or not is_ancestor(candidate_root, claim["claimBaseHead"], candidate_head):
        raise TaskError("CANDIDATE_INVALID")
    delivery = state["lifecycle"]["delivery"]
    if delivery is None:
        raise TaskError("CANDIDATE_INVALID")
    try:
        parent = git(candidate_root, "rev-parse", f"{candidate_head}^", code="CANDIDATE_INVALID").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("CANDIDATE_INVALID") from None
    if parent != delivery["implementationHead"] or changed_paths(candidate_root, candidate_head) != [f"{task_path}/task.json"]:
        raise TaskError("CANDIDATE_INVALID")
    anchored_state = _fixed_json(candidate_root, claim["claimBaseHead"], f"{task_path}/task.json", "CANDIDATE_INVALID")
    validate_state(anchored_state)
    anchored_authorization_raw = read_tree_file(candidate_root, claim["claimBaseHead"], f"{task_path}/authorization.json")
    if anchored_authorization_raw != canonical_bytes(authorization):
        raise TaskError("authorization_mismatch")
    anchored_offer = _fixed_json(candidate_root, claim["claimBaseHead"], f"{task_path}/offer.json", "INVALID_OFFER")
    validate_offer(anchored_offer)
    if (
        anchored_state["lifecycle"]["phase"] != "awaiting_claim"
        or anchored_offer["status"] != "active"
        or anchored_offer["offerId"] != claim["offerId"]
        or anchored_offer["authorizationDigest"] != authorization["authorizationDigest"]
    ):
        raise TaskError("authorization_mismatch")
    return state, authorization


def _authorization_preflight(
    state: dict[str, Any],
    authorization: dict[str, Any],
    repository: str,
    candidate_head: str,
    required_action: str,
) -> None:
    repo = state["repository"]
    plan = state["documents"]["plan"]
    delivery = state["lifecycle"]["delivery"]
    if (
        state["lifecycle"]["phase"] != "delivered"
        or delivery is None
        or state["actionAuthorizationDigest"] != authorization["authorizationDigest"]
        or authorization["taskId"] != state["taskId"]
        or authorization["repository"] != repository
        or authorization["baseBranch"] != repo["baseBranch"]
        or authorization["baseSha"] != repo["baseSha"]
        or authorization["taskBranch"] != repo["taskBranch"]
        or authorization["planVersion"] != plan["version"]
        or authorization["materialDigest"] != plan["materialDigest"]
        or required_action not in authorization["allowedActions"]
    ):
        raise TaskError("authorization_mismatch")
    if not isinstance(delivery["implementationHead"], str) or delivery["implementationHead"] == candidate_head:
        raise TaskError("CANDIDATE_INVALID")


def _check_snapshot(
    snapshot: dict[str, Any],
    repository: str,
    pr_number: int,
    base_branch: str,
    task_branch: str,
    candidate_head: str,
    required_checks: list[str],
) -> None:
    validate_snapshot(snapshot)
    if (
        snapshot["repository"] != repository
        or snapshot["prNumber"] != pr_number
        or snapshot["baseBranch"] != base_branch
        or snapshot["headBranch"] != task_branch
        or snapshot["headSha"] != candidate_head
        or snapshot["state"] != "open"
        or snapshot["draft"]
        or not snapshot["mergeable"]
    ):
        raise TaskError("PR_FACT_MISMATCH")
    check_map = {item["name"]: item["status"] for item in snapshot["checks"]}
    if any(check_map.get(name) != "success" for name in required_checks):
        raise TaskError("REQUIRED_CHECK_FAILURE")


def accept_candidate(
    trusted_root: Path,
    candidate_root: Path,
    task_path: str,
    repository: str,
    pr_number: int,
    candidate_head: str,
    required_checks: list[str],
    review: dict[str, Any],
    adapter: GitHubAdapter,
    actor_role: str,
    merge: bool,
) -> dict[str, Any]:
    if actor_role not in {"acceptor", "main"}:
        raise TaskError("EXECUTOR_ACCEPTANCE_FORBIDDEN")
    require_sha1(candidate_head, "CANDIDATE_INVALID")
    if not isinstance(pr_number, int) or pr_number < 1:
        raise TaskError("INVALID_PR")
    if required_checks != sorted(set(required_checks)):
        raise TaskError("INVALID_REQUIRED_CHECKS")
    trusted = trusted_root.resolve()
    candidate = candidate_root.resolve()
    if trusted == candidate or common_dir(trusted) != common_dir(candidate):
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    state, authorization = _validate_fixed_candidate(candidate, task_path, candidate_head)
    repo = state["repository"]
    verify_identity(candidate, repository, repo["taskBranch"], common_dir(trusted))
    if repository_identity(trusted) != repository or branch(trusted) != repo["baseBranch"] or not is_clean(trusted):
        raise TaskError("TRUSTED_CONTEXT_INVALID")
    try:
        remote_head = git(trusted, "rev-parse", f"refs/remotes/origin/{repo['baseBranch']}", code="TRUSTED_CONTEXT_INVALID").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("TRUSTED_CONTEXT_INVALID") from None
    if head(trusted) != remote_head:
        raise TaskError("TRUSTED_CONTEXT_INVALID")
    _authorization_preflight(state, authorization, repository, candidate_head, "conditional_merge" if merge else "ready_for_review")
    validate_review(review)
    claim = state["lifecycle"]["claim"]
    if (
        review["taskId"] != state["taskId"]
        or review["candidateHead"] != candidate_head
        or review["outcome"] != "accepted"
        or review["findings"]
        or (claim is not None and review["reviewerDigest"] == claim["sessionDigest"])
    ):
        raise TaskError("INDEPENDENT_REVIEW_REQUIRED")

    first = adapter.snapshot(repository, pr_number)
    _check_snapshot(first, repository, pr_number, repo["baseBranch"], repo["taskBranch"], candidate_head, required_checks)
    if not merge:
        return {
            "status": "accepted",
            "taskId": state["taskId"],
            "candidateHead": candidate_head,
            "reviewDigest": review["reviewDigest"],
            "merged": False,
        }
    if authorization["mode"] != "implement_and_merge_on_acceptance":
        raise TaskError("authorization_mismatch")

    state_again, authorization_again = _validate_fixed_candidate(candidate, task_path, candidate_head)
    _authorization_preflight(state_again, authorization_again, repository, candidate_head, "conditional_merge")
    second = adapter.snapshot(repository, pr_number)
    _check_snapshot(second, repository, pr_number, repo["baseBranch"], repo["taskBranch"], candidate_head, required_checks)
    try:
        result = adapter.merge(repository, pr_number, candidate_head)
    except MergeIndeterminate:
        reconciled = adapter.snapshot(repository, pr_number)
        validate_snapshot(reconciled)
        if reconciled["state"] != "merged" or reconciled["mergedHead"] != candidate_head:
            raise TaskError("MERGE_INDETERMINATE") from None
        result = {"status": "merged", "mergedHead": candidate_head}
    if result != {"status": "merged", "mergedHead": candidate_head}:
        raise TaskError("MERGE_REJECTED")
    return {
        "status": "accepted",
        "taskId": state["taskId"],
        "candidateHead": candidate_head,
        "reviewDigest": review["reviewDigest"],
        "merged": True,
    }


class SubprocessGitHubAdapter:
    """Narrow JSON adapter used by tests and later repository policy layers."""

    def __init__(self, executable: Path) -> None:
        if executable.is_symlink() or not executable.is_file() or not stat.S_IMODE(executable.stat().st_mode) & 0o111:
            raise TaskError("INVALID_GITHUB_ADAPTER")
        self.executable = executable.resolve()

    def _call(self, request: dict[str, Any]) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [str(self.executable)],
                input=canonical_bytes(request),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise TaskError("GITHUB_ADAPTER_FAILED") from None
        if result.returncode == 75 and request["operation"] == "merge":
            raise MergeIndeterminate()
        if result.returncode != 0:
            raise TaskError("GITHUB_ADAPTER_FAILED")
        if len(result.stdout) > 4 * 1024 * 1024:
            raise TaskError("INVALID_GITHUB_RESPONSE")
        try:
            value = json.loads(result.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TaskError("INVALID_GITHUB_RESPONSE") from None
        if not isinstance(value, dict) or result.stdout != canonical_bytes(value):
            raise TaskError("INVALID_GITHUB_RESPONSE")
        return value

    def snapshot(self, repository: str, pr_number: int) -> dict[str, Any]:
        return self._call({"operation": "snapshot", "repository": repository, "prNumber": pr_number})

    def merge(self, repository: str, pr_number: int, expected_head: str) -> dict[str, Any]:
        return self._call(
            {"operation": "merge", "repository": repository, "prNumber": pr_number, "expectedHead": expected_head}
        )
