"""Trusted fixed-tree acceptance and one-shot conditional merge."""

from __future__ import annotations

from copy import deepcopy
import base64
import json
from pathlib import Path
import stat
import subprocess
from typing import Any, Protocol

from gkd_ci.policy import load_policy_binding
from .canonical import CHECK_NAME_RE, CREDENTIAL_RE, SystemClock, SystemNonce, canonical_bytes, digest_object, require_keys, require_sha1, require_sha256, require_string, sha256_bytes
from .documents import PLAN_MATERIAL_SECTIONS, PLAN_SECTIONS, parse_sections
from .errors import TaskError
from .gitops import branch, changed_paths, common_dir, git, head, is_ancestor, is_clean, read_tree_file, repository_identity, require_regular_tree_file, verify_identity
from .model import TASK_POLICY_REWORK_VERSION, TASK_POLICY_VERSION, TASK_STATE_REWORK_VERSION, advance_state, validate_authorization, validate_offer, validate_state
from .runtime import RuntimeStore, runtime_key, validate_claim_receipt
from .transaction import TransactionChange, TransactionManager


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
        require_string(check["name"], "INVALID_GITHUB_RESPONSE", CHECK_NAME_RE)
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
    findings = value["findings"]
    if (
        not isinstance(findings, list)
        or any(not isinstance(item, str) for item in findings)
        or len(findings) != len(set(findings))
        or any(
            not isinstance(item, str)
            or not item
            or item != item.strip()
            or len(item) > 512
            or any(character in item for character in "\r\n\x00")
            or CREDENTIAL_RE.search(item)
            for item in findings
        )
    ):
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


def _tree_path_exists(root: Path, commit: str, path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{commit}:{path}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode not in {0, 1, 128}:
        raise TaskError("CANDIDATE_INVALID")
    return result.returncode == 0


def _validate_delivery_sequence(
    candidate_root: Path,
    task_path: str,
    candidate_head: str,
    claim_base_head: str,
    delivery: dict[str, Any],
    allow_existing_document: bool,
) -> None:
    required = {"deliveryDocumentCommit", "deliveryDocumentPath", "deliveryDocumentDigest"}
    if not required.issubset(delivery):
        raise TaskError("DELIVERY_DOCUMENT_BINDING_REQUIRED")
    expected_path = f"{task_path}/delivery.md"
    if delivery["deliveryDocumentPath"] != expected_path:
        raise TaskError("CANDIDATE_INVALID")
    document_commit = delivery["deliveryDocumentCommit"]
    implementation_head = delivery["implementationHead"]
    try:
        final_parent = git(candidate_root, "rev-parse", f"{candidate_head}^", code="CANDIDATE_INVALID").decode("ascii").strip()
        document_parent = git(candidate_root, "rev-parse", f"{document_commit}^", code="CANDIDATE_INVALID").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("CANDIDATE_INVALID") from None
    if (
        final_parent != document_commit
        or document_parent != implementation_head
        or not is_ancestor(candidate_root, claim_base_head, implementation_head)
        or changed_paths(candidate_root, candidate_head) != [f"{task_path}/task.json"]
        or changed_paths(candidate_root, document_commit) != [expected_path]
    ):
        raise TaskError("CANDIDATE_INVALID")
    if _tree_path_exists(candidate_root, implementation_head, expected_path) and not allow_existing_document:
        raise TaskError("DUPLICATE_DELIVERY_DOCUMENT")
    try:
        document_raw = read_tree_file(candidate_root, document_commit, expected_path)
    except TaskError:
        raise TaskError("CANDIDATE_INVALID") from None
    require_regular_tree_file(candidate_root, document_commit, expected_path)
    if sha256_bytes(document_raw) != delivery["deliveryDocumentDigest"]:
        raise TaskError("CANDIDATE_INVALID")


def _journal_image(record: dict[str, Any]) -> bytes | None:
    if record["postimage"] is None:
        return None
    try:
        return base64.b64decode(record["postimage"].encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None


def _validate_claim_receipt(
    candidate_root: Path,
    task_path: str,
    candidate_head: str,
    state: dict[str, Any],
    repository: str,
    runtime: RuntimeStore,
) -> dict[str, Any]:
    claim = state["lifecycle"]["claim"]
    if claim is None:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    receipt = runtime.read_claim_receipt(claim["claimId"])
    validate_claim_receipt(receipt)
    durable = state["repository"]
    if (
        receipt["taskId"] != state["taskId"]
        or receipt["repository"] != repository
        or receipt["taskBranch"] != durable["taskBranch"]
        or receipt["taskPath"] != task_path
        or receipt["offerId"] != claim["offerId"]
        or receipt["claimId"] != claim["claimId"]
        or receipt["epoch"] != claim["epoch"]
        or receipt["claimBaseHead"] != claim["claimBaseHead"]
        or not is_ancestor(candidate_root, receipt["claimCommit"], candidate_head)
        or not is_ancestor(candidate_root, receipt["claimBaseHead"], receipt["claimCommit"])
    ):
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    journal = runtime.read_journal(receipt["transactionId"])
    if (
        journal["status"] != "committed"
        or journal["transactionId"] != receipt["transactionId"]
        or journal["journalDigest"] != receipt["transactionDigest"]
        or journal["runtimeKey"] != runtime_key(repository, state["taskId"], durable["taskBranch"])
        or journal["expectedHead"] != receipt["claimBaseHead"]
        or journal["committedHead"] != receipt["claimCommit"]
    ):
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    state_path = f"{task_path}/task.json"
    offer_path = f"{task_path}/offer.json"
    expected_paths = sorted({state_path, offer_path})
    records = {record["path"]: record for record in journal["files"]}
    if sorted(records) != expected_paths:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    runtime_records = {record["path"]: record for record in journal.get("runtimeFiles", [])}
    if "executionBundleDigest" in claim:
        activation_path = f"activations/{claim['activationId']}.json"
        if sorted(runtime_records) != [activation_path] or runtime_records[activation_path]["preimage"] is not None:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        activation_raw = _journal_image(runtime_records[activation_path])
        if activation_raw is None:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        try:
            activation = json.loads(activation_raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None
        if not isinstance(activation, dict) or activation_raw != canonical_bytes(activation):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        from gkd_role.activation import validate_activation

        validate_activation(activation)
        if activation["activationId"] != claim["activationId"]:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        try:
            durable_activation = runtime.read_activation(claim["activationId"])
        except TaskError:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None
        if canonical_bytes(durable_activation) != activation_raw:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    elif runtime_records:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    try:
        parent = git(candidate_root, "rev-parse", f"{receipt['claimCommit']}^", code="CLAIM_RECEIPT_UNAVAILABLE").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None
    if parent != receipt["claimBaseHead"] or changed_paths(candidate_root, receipt["claimCommit"]) != expected_paths:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    state_raw = _journal_image(records[state_path])
    offer_raw = _journal_image(records[offer_path])
    if state_raw is None or offer_raw is None:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    if (
        read_tree_file(candidate_root, receipt["claimCommit"], state_path) != state_raw
        or read_tree_file(candidate_root, receipt["claimCommit"], offer_path) != offer_raw
        or sha256_bytes(state_raw) != receipt["claimStateDigest"]
        or sha256_bytes(offer_raw) != receipt["offerDigest"]
    ):
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    anchored_state = _fixed_json(candidate_root, receipt["claimCommit"], state_path, "CLAIM_RECEIPT_UNAVAILABLE")
    anchored_offer = _fixed_json(candidate_root, receipt["claimCommit"], offer_path, "CLAIM_RECEIPT_UNAVAILABLE")
    validate_state(anchored_state)
    validate_offer(anchored_offer)
    if (
        anchored_state["lifecycle"]["phase"] != "implementing"
        or anchored_state["lifecycle"]["claim"] is None
        or anchored_state["lifecycle"]["claim"]["claimId"] != claim["claimId"]
        or anchored_offer["offerId"] != claim["offerId"]
        or anchored_offer["status"] != "consumed"
        or anchored_offer["consumedByDigest"] != digest_object(anchored_state["lifecycle"]["claim"])
    ):
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    return receipt


def _validate_fixed_candidate(
    candidate_root: Path,
    task_path: str,
    candidate_head: str,
    runtime: RuntimeStore,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str | None]]:
    if head(candidate_root) != candidate_head or not is_clean(candidate_root):
        raise TaskError("candidate_head_changed")
    state = _fixed_json(candidate_root, candidate_head, f"{task_path}/task.json", "CANDIDATE_INVALID")
    validate_state(state)
    if state["repository"]["taskPath"] != task_path:
        raise TaskError("CANDIDATE_INVALID")
    if state["schemaVersion"] in {TASK_POLICY_VERSION, TASK_POLICY_REWORK_VERSION} and (
        load_policy_binding(candidate_root, state["repository"]["identity"]) != state["repository"]["policy"]
    ):
        raise TaskError("TASK_POLICY_DRIFT")
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
    _validate_delivery_sequence(
        candidate_root,
        task_path,
        candidate_head,
        claim["claimBaseHead"],
        delivery,
        bool(state["lifecycle"].get("rejectedAttempts")),
    )
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
    claim_receipt = _validate_claim_receipt(candidate_root, task_path, candidate_head, state, anchored_state["repository"]["identity"], runtime)
    claimed_state = _fixed_json(
        candidate_root,
        claim_receipt["claimCommit"],
        f"{task_path}/task.json",
        "CLAIM_RECEIPT_UNAVAILABLE",
    )
    claimed_offer = _fixed_json(
        candidate_root,
        claim_receipt["claimCommit"],
        f"{task_path}/offer.json",
        "CLAIM_RECEIPT_UNAVAILABLE",
    )
    expected_consumed_offer = deepcopy(anchored_offer)
    expected_consumed_offer["status"] = "consumed"
    expected_consumed_offer["consumedByDigest"] = digest_object(claim)
    current_offer = _fixed_json(candidate_root, candidate_head, f"{task_path}/offer.json", "INVALID_OFFER")
    validate_offer(current_offer)
    if claimed_state["lifecycle"]["claim"] != claim or claimed_offer != expected_consumed_offer or current_offer != claimed_offer:
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
    activation_receipt_digest: str | None = None
    if anchored_offer["schemaVersion"] in {2, 3, 4}:
        from gkd_role.activation import validate_activation, validate_activation_receipt

        activation_receipt = runtime.read_claim_activation_receipt(claim["claimId"])
        validate_activation_receipt(activation_receipt)
        activation_indexed_receipt = runtime.read_activation_receipt(claim["activationId"])
        validate_activation_receipt(activation_indexed_receipt)
        activation = runtime.read_activation(activation_receipt["activationId"])
        validate_activation(activation)
        if (
            activation_receipt != activation_indexed_receipt
            or activation_receipt["activationId"] != activation["activationId"]
            or activation_receipt["claimId"] != claim["claimId"]
            or activation_receipt["claimCommit"] != claim_receipt["claimCommit"]
            or activation_receipt["claimReceiptDigest"] != claim_receipt["receiptDigest"]
            or activation_receipt["activationDigest"] != activation["activationDigest"]
            or activation["activationId"] != claim.get("activationId")
            or activation["envelopeId"] != claim.get("envelopeId")
            or activation["offerId"] != anchored_offer["offerId"]
            or anchored_offer["epoch"] != claim["epoch"]
            or activation["taskId"] != state["taskId"]
            or anchored_offer["taskId"] != state["taskId"]
            or activation["repository"] != state["repository"]["identity"]
            or anchored_offer["repository"] != state["repository"]["identity"]
            or activation["taskBranch"] != state["repository"]["taskBranch"]
            or anchored_offer["taskBranch"] != state["repository"]["taskBranch"]
            or activation["roleName"] != anchored_offer["roleName"]
            or activation["roleDigest"] != anchored_offer["roleDigest"]
            or activation["roleDigest"] != claim["roleDigest"]
            or activation["configDigest"] != anchored_offer["configDigest"]
            or activation["configDigest"] != claim["configDigest"]
            or activation["bundleDigest"] != anchored_offer["bundleDigest"]
            or activation["route"] != anchored_offer["route"]
            or activation["offerCreatedAt"] != anchored_offer["createdAt"]
            or activation["offerExpiresAt"] != anchored_offer["expiresAt"]
        ):
            raise TaskError("INVALID_ACTIVATION_RECEIPT")
        if activation["schemaVersion"] == 2:
            if (
                anchored_offer.get("hostContract") is None
                or activation["executorTaskName"] != claim["writerId"]
                or activation["executorAttemptDigest"] != claim["sessionDigest"]
                or activation["executorTaskName"] != claim.get("executorTaskName")
                or activation["executorAttemptDigest"] != claim.get("executorAttemptDigest")
            ):
                raise TaskError("INVALID_ACTIVATION_RECEIPT")
        elif activation["agentId"] != claim["writerId"] or activation["threadDigest"] != claim["sessionDigest"]:
            raise TaskError("INVALID_ACTIVATION_RECEIPT")
        if anchored_offer["schemaVersion"] in {3, 4} and (
            claim.get("executionBundleDigest") != anchored_offer["bundleDigest"]
            or claim.get("routeDecisionDigest") != anchored_offer["routeDecisionDigest"]
            or activation.get("routeDecisionDigest") != anchored_offer["routeDecisionDigest"]
        ):
            raise TaskError("INVALID_ACTIVATION_RECEIPT")
        activation_receipt_digest = activation_receipt["receiptDigest"]
    return state, authorization, {
        "claimReceiptDigest": claim_receipt["receiptDigest"],
        "activationReceiptDigest": activation_receipt_digest,
    }


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


def _validate_trusted_context(trusted: Path, repository: str, base_branch: str) -> None:
    if repository_identity(trusted) != repository or branch(trusted) != base_branch or not is_clean(trusted):
        raise TaskError("TRUSTED_CONTEXT_INVALID")
    try:
        remote_head = git(trusted, "rev-parse", f"refs/remotes/origin/{base_branch}", code="TRUSTED_CONTEXT_INVALID").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("TRUSTED_CONTEXT_INVALID") from None
    if head(trusted) != remote_head:
        raise TaskError("TRUSTED_CONTEXT_INVALID")


def _check_rework_snapshot(
    snapshot: dict[str, Any],
    repository: str,
    pr_number: int,
    base_branch: str,
    task_branch: str,
    candidate_head: str,
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
        or snapshot["mergedHead"] is not None
    ):
        raise TaskError("PR_FACT_MISMATCH")


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
    runtime: RuntimeStore | None = None,
) -> dict[str, Any]:
    if actor_role not in {"acceptor", "main"}:
        raise TaskError("EXECUTOR_ACCEPTANCE_FORBIDDEN")
    require_sha1(candidate_head, "CANDIDATE_INVALID")
    if not isinstance(pr_number, int) or pr_number < 1:
        raise TaskError("INVALID_PR")
    if required_checks != sorted(set(required_checks)):
        raise TaskError("INVALID_REQUIRED_CHECKS")
    if trusted_root.is_symlink() or candidate_root.is_symlink():
        raise TaskError("CANDIDATE_SYMLINK")
    trusted = trusted_root.resolve()
    candidate = candidate_root.resolve()
    if trusted == candidate or common_dir(trusted) != common_dir(candidate):
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    runtime = runtime or RuntimeStore(common_dir(candidate) / "gkd-runtime")
    state, authorization, _ = _validate_fixed_candidate(candidate, task_path, candidate_head, runtime)
    repo = state["repository"]
    verify_identity(candidate, repository, repo["taskBranch"], common_dir(trusted))
    _validate_trusted_context(trusted, repository, repo["baseBranch"])
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

    state_again, authorization_again, _ = _validate_fixed_candidate(candidate, task_path, candidate_head, runtime)
    _validate_trusted_context(trusted, repository, repo["baseBranch"])
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


def rework_candidate(
    trusted_root: Path,
    candidate_root: Path,
    task_path: str,
    repository: str,
    pr_number: int,
    candidate_head: str,
    review: dict[str, Any],
    adapter: GitHubAdapter,
    actor_role: str,
    runtime: RuntimeStore | None = None,
    clock: Any | None = None,
    nonce: Any | None = None,
    failure_hook: Any | None = None,
) -> dict[str, Any]:
    if actor_role not in {"acceptor", "main"}:
        raise TaskError("EXECUTOR_REWORK_FORBIDDEN")
    require_sha1(candidate_head, "CANDIDATE_INVALID")
    if not isinstance(pr_number, int) or pr_number < 1:
        raise TaskError("INVALID_PR")
    if trusted_root.is_symlink() or candidate_root.is_symlink():
        raise TaskError("CANDIDATE_SYMLINK")
    trusted = trusted_root.resolve()
    candidate = candidate_root.resolve()
    if trusted == candidate or common_dir(trusted) != common_dir(candidate):
        raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
    runtime = runtime or RuntimeStore(common_dir(candidate) / "gkd-runtime")
    state, authorization, receipt_facts = _validate_fixed_candidate(candidate, task_path, candidate_head, runtime)
    repo = state["repository"]
    verify_identity(candidate, repository, repo["taskBranch"], common_dir(trusted))
    _validate_trusted_context(trusted, repository, repo["baseBranch"])
    _authorization_preflight(state, authorization, repository, candidate_head, "ci_repair")
    validate_review(review)
    claim = state["lifecycle"]["claim"]
    if (
        review["taskId"] != state["taskId"]
        or review["candidateHead"] != candidate_head
        or review["outcome"] != "rejected"
        or not review["findings"]
        or (claim is not None and review["reviewerDigest"] == claim["sessionDigest"])
    ):
        raise TaskError("INDEPENDENT_REJECTION_REQUIRED")

    first = adapter.snapshot(repository, pr_number)
    _check_rework_snapshot(first, repository, pr_number, repo["baseBranch"], repo["taskBranch"], candidate_head)
    state_again, authorization_again, receipt_facts_again = _validate_fixed_candidate(candidate, task_path, candidate_head, runtime)
    _validate_trusted_context(trusted, repository, repo["baseBranch"])
    _authorization_preflight(state_again, authorization_again, repository, candidate_head, "ci_repair")
    second = adapter.snapshot(repository, pr_number)
    _check_rework_snapshot(second, repository, pr_number, repo["baseBranch"], repo["taskBranch"], candidate_head)
    if first != second or state_again != state or authorization_again != authorization or receipt_facts_again != receipt_facts:
        raise TaskError("PR_FACT_MISMATCH")

    current_offer = _fixed_json(candidate, candidate_head, f"{task_path}/offer.json", "INVALID_OFFER")
    validate_offer(current_offer)
    at_clock = clock or SystemClock()
    rejected_at = at_clock.now()
    attempt = {
        "schemaVersion": 1,
        "taskId": state["taskId"],
        "repository": repository,
        "prNumber": pr_number,
        "baseBranch": repo["baseBranch"],
        "taskBranch": repo["taskBranch"],
        "candidateHead": candidate_head,
        "epoch": state["lifecycle"]["epoch"],
        "offer": deepcopy(current_offer),
        "claim": deepcopy(claim),
        "delivery": deepcopy(state["lifecycle"]["delivery"]),
        "claimReceiptDigest": receipt_facts["claimReceiptDigest"],
        "activationReceiptDigest": receipt_facts["activationReceiptDigest"],
        "reviewDigest": review["reviewDigest"],
        "findingsDigest": digest_object(review["findings"]),
        "rejectedAt": rejected_at,
    }
    retired = {
        "offerId": current_offer["offerId"],
        "claim": deepcopy(claim),
        "epoch": state["lifecycle"]["epoch"],
        "reason": "rejected-review",
        "retiredAt": rejected_at,
    }
    updated_offer = deepcopy(current_offer)
    updated_offer["status"] = "revoked"

    def builder(current: dict[str, Any]) -> TransactionChange:
        if current != state or current["lifecycle"]["phase"] != "delivered" or current["lifecycle"]["blocked"] is not None:
            raise TaskError("INVALID_TRANSITION")
        updated = deepcopy(current)
        updated["schemaVersion"] = (
            TASK_POLICY_REWORK_VERSION
            if current["schemaVersion"] in {TASK_POLICY_VERSION, TASK_POLICY_REWORK_VERSION}
            else TASK_STATE_REWORK_VERSION
        )
        updated["lifecycle"].setdefault("rejectedAttempts", []).append(attempt)
        updated["lifecycle"]["phase"] = "planning"
        updated["lifecycle"]["epoch"] += 1
        updated["lifecycle"]["writer"] = None
        updated["lifecycle"]["offer"] = None
        updated["lifecycle"]["claim"] = None
        updated["lifecycle"]["retiredClaims"].append(retired)
        updated["lifecycle"]["delivery"] = None
        updated["lifecycle"]["acceptance"] = None
        updated["lifecycle"]["completion"] = None
        updated = advance_state(updated, "reworked", rejected_at, candidate_head, attempt)
        return TransactionChange(
            {
                f"{task_path}/task.json": canonical_bytes(updated),
                f"{task_path}/offer.json": canonical_bytes(updated_offer),
            },
            "记录拒绝并返回返工",
            {
                "status": "reworked",
                "taskId": current["taskId"],
                "revision": updated["revision"],
                "epoch": updated["lifecycle"]["epoch"],
                "rejectedHead": candidate_head,
                "reviewDigest": review["reviewDigest"],
                "findingsDigest": attempt["findingsDigest"],
            },
        )

    manager = TransactionManager(
        candidate,
        task_path,
        runtime,
        runtime_key(repository, state["taskId"], repo["taskBranch"]),
        at_clock,
        nonce or SystemNonce(),
        failure_hook,
    )
    return manager.execute(candidate_head, state["revision"], builder)


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
