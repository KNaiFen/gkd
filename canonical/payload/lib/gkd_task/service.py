"""Deterministic task bootstrap and lifecycle service."""

from __future__ import annotations

from copy import deepcopy
import base64
import json
from pathlib import Path
import os
import re
import subprocess
from typing import Any, Protocol

from .canonical import (
    SystemClock,
    SystemNonce,
    atomic_write,
    canonical_bytes,
    digest_object,
    read_canonical_json,
    relative_path,
    require_sha1,
    require_sha256,
    require_string,
    require_utc,
    sha256_bytes,
)
from .documents import IMPLEMENTATION_SECTIONS, PLAN_SECTIONS, inspect_package, inspect_plan, parse_sections
from .errors import TaskError
from .gitops import (
    branch,
    commit_exact,
    common_dir,
    changed_paths,
    git,
    git_root,
    head,
    is_ancestor,
    repository_identity,
    require_clean,
    is_clean,
    read_tree_file,
    verified_relative_path,
    verify_identity,
)
from .model import (
    ACTION_MODES,
    KNOWN_ACTIONS,
    TASK_SCHEMA_VERSION,
    advance_state,
    authorization_digest,
    finalize_state,
    new_state,
    read_state,
    validate_authorization,
    validate_offer,
    validate_runtime_evidence,
    validate_state,
)
from .runtime import RUNTIME_SCHEMA_VERSION, RuntimeStore, runtime_key, validate_claim_receipt
from .transaction import TransactionChange, TransactionManager


def _check_branch_name(value: str) -> str:
    if not value or value.startswith("-") or "\x00" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise TaskError("INVALID_GIT_BRANCH")
    try:
        result = subprocess.run(
            ["git", "check-ref-format", "--branch", value],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        raise TaskError("INVALID_GIT_BRANCH") from None
    if result.returncode != 0:
        raise TaskError("INVALID_GIT_BRANCH")
    return value


def _paths_overlap(first: Path, second: Path) -> bool:
    try:
        first.relative_to(second)
        return True
    except ValueError:
        pass
    try:
        second.relative_to(first)
        return True
    except ValueError:
        return False


def _worktree_add(main_root: Path, candidate_root: Path, task_branch: str, base_sha: str) -> None:
    git(
        main_root,
        "worktree",
        "add",
        "-b",
        task_branch,
        os.fspath(candidate_root),
        base_sha,
        code="WORKTREE_CREATE_FAILED",
    )


def bootstrap_task(
    main_root_value: Path,
    candidate_root_value: Path,
    package_root: Path,
    task_id: str,
    task_path: str,
    repository: str,
    base_branch: str,
    base_sha: str,
    task_branch: str,
    runtime_root: Path | None = None,
    clock: Any | None = None,
) -> dict[str, Any]:
    clock = clock or SystemClock()
    require_string(task_id, "INVALID_TASK_ID")
    relative_path(task_path, "INVALID_TASK_PATH")
    require_string(repository, "INVALID_REPOSITORY_IDENTITY")
    _check_branch_name(base_branch)
    _check_branch_name(task_branch)
    require_sha1(base_sha, "INVALID_BASE_SHA")
    documents, raw_documents = inspect_package(package_root)

    main_root = git_root(main_root_value)
    if main_root != main_root_value.resolve() or branch(main_root) != base_branch:
        raise TaskError("INVALID_MAIN_CHECKOUT")
    require_clean(main_root)
    if repository_identity(main_root) != repository:
        raise TaskError("INVALID_REPOSITORY_IDENTITY")
    git(main_root, "fetch", "origin", base_branch, code="FETCH_FAILED")
    remote_ref = f"refs/remotes/origin/{base_branch}"
    try:
        remote_head = git(main_root, "rev-parse", remote_ref, code="BASE_NOT_FETCHED").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("BASE_NOT_FETCHED") from None
    require_sha1(remote_head, "BASE_NOT_FETCHED")
    if not is_ancestor(main_root, base_sha, remote_head) or not is_ancestor(main_root, head(main_root), remote_head):
        raise TaskError("BASE_NOT_FETCHED")
    for ref in (f"refs/heads/{task_branch}", f"refs/remotes/origin/{task_branch}"):
        result = subprocess.run(
            ["git", "-C", os.fspath(main_root), "show-ref", "--verify", "--quiet", ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            raise TaskError("TASK_BRANCH_EXISTS")
        if result.returncode not in {0, 1}:
            raise TaskError("GIT_OPERATION_FAILED")

    candidate_parent = candidate_root_value.parent
    if candidate_parent.is_symlink() or not candidate_parent.is_dir():
        raise TaskError("INVALID_CANDIDATE_PARENT")
    candidate_root = candidate_parent.resolve() / candidate_root_value.name
    if candidate_root.exists() or candidate_root.is_symlink():
        raise TaskError("CANDIDATE_ALREADY_EXISTS")
    if runtime_root is not None and _paths_overlap(runtime_root.resolve(strict=False), candidate_root):
        raise TaskError("RUNTIME_ROOT_OVERLAP")
    _worktree_add(main_root, candidate_root, task_branch, base_sha)
    verify_identity(candidate_root, repository, task_branch, common_dir(main_root))
    if head(candidate_root) != base_sha:
        raise TaskError("BASE_HEAD_MISMATCH")

    durable_repository = {
        "identity": repository,
        "baseBranch": base_branch,
        "baseSha": base_sha,
        "taskBranch": task_branch,
        "taskPath": task_path,
    }
    task_root = verified_relative_path(candidate_root, task_path)
    task_root.mkdir(parents=True, exist_ok=False)
    for name, content in raw_documents.items():
        atomic_write(task_root / name, content)
    state = new_state(task_id, durable_repository, documents, clock.now(), base_sha)
    atomic_write(task_root / "task.json", canonical_bytes(state))
    committed_head = commit_exact(
        candidate_root,
        [f"{task_path}/{name}" for name in (*raw_documents.keys(), "task.json")],
        f"初始化任务 {task_id}",
    )
    runtime_path = runtime_root or (common_dir(candidate_root) / "gkd-runtime")
    if _paths_overlap(runtime_path.resolve(strict=False), candidate_root.resolve()):
        raise TaskError("RUNTIME_ROOT_OVERLAP")
    runtime = RuntimeStore(runtime_path)
    runtime.write_attachment(
        {
            "schemaVersion": RUNTIME_SCHEMA_VERSION,
            "kind": "attachment",
            "repository": repository,
            "taskId": task_id,
            "taskBranch": task_branch,
            "taskPath": task_path,
            "candidateRoot": os.fspath(candidate_root),
            "commonDir": os.fspath(common_dir(candidate_root)),
            "updatedAt": clock.now(),
        }
    )
    require_clean(main_root)
    require_clean(candidate_root)
    return {
        "status": "bootstrapped",
        "taskId": task_id,
        "baseSha": base_sha,
        "head": committed_head,
        "revision": 0,
    }


class RuntimeEvidenceProvider(Protocol):
    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]: ...


class UnavailableEvidenceProvider:
    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]:
        del purpose, expected
        raise TaskError("RUNTIME_EVIDENCE_UNAVAILABLE")


class FixtureEvidenceProvider:
    """Internal provider for deterministic L1/L2 fixtures."""

    def __init__(self, evidence: dict[str, Any]) -> None:
        validate_runtime_evidence(evidence)
        self.evidence = evidence

    def observe(self, purpose: str, expected: dict[str, Any]) -> dict[str, Any]:
        del purpose, expected
        return deepcopy(self.evidence)


def make_fixture_evidence(
    writer_id: str,
    session_digest: str,
    role_digest: str,
    config_digest: str,
    route: str,
    status: str,
    observed_at: str,
) -> dict[str, Any]:
    value = {
        "schemaVersion": TASK_SCHEMA_VERSION,
        "provider": "fixture",
        "writerId": writer_id,
        "sessionDigest": session_digest,
        "roleDigest": role_digest,
        "configDigest": config_digest,
        "route": route,
        "status": status,
        "observedAt": observed_at,
    }
    value["evidenceDigest"] = digest_object(value)
    validate_runtime_evidence(value)
    return value


class TaskService:
    def __init__(
        self,
        candidate_root: Path,
        task_path: str,
        runtime: RuntimeStore | None = None,
        clock: Any | None = None,
        nonce: Any | None = None,
        evidence_provider: RuntimeEvidenceProvider | None = None,
        failure_hook: Any | None = None,
    ) -> None:
        if candidate_root.is_symlink():
            raise TaskError("CANDIDATE_SYMLINK")
        if not candidate_root.is_dir():
            raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
        self.candidate_root = git_root(candidate_root)
        self.task_path = relative_path(task_path, "INVALID_TASK_PATH")
        self.task_root = verified_relative_path(self.candidate_root, self.task_path)
        self.clock = clock or SystemClock()
        self.nonce = nonce or SystemNonce()
        self.evidence_provider = evidence_provider or UnavailableEvidenceProvider()
        initial = read_state(self.task_root / "task.json", self.task_root)
        repository = initial["repository"]
        verify_identity(
            self.candidate_root,
            repository["identity"],
            repository["taskBranch"],
        )
        self.key = runtime_key(repository["identity"], initial["taskId"], repository["taskBranch"])
        self.runtime = runtime or RuntimeStore(common_dir(self.candidate_root) / "gkd-runtime")
        if _paths_overlap(self.runtime.root, self.candidate_root):
            raise TaskError("RUNTIME_ROOT_OVERLAP")
        self.transactions = TransactionManager(
            self.candidate_root,
            self.task_path,
            self.runtime,
            self.key,
            self.clock,
            self.nonce,
            failure_hook,
        )

    def _state(self) -> dict[str, Any]:
        return read_state(self.task_root / "task.json", self.task_root)

    def _authorization(self) -> dict[str, Any]:
        return read_canonical_json(
            self.task_root / "authorization.json",
            "INVALID_AUTHORIZATION",
            validate_authorization,
        )

    def _offer(self) -> dict[str, Any]:
        return read_canonical_json(self.task_root / "offer.json", "INVALID_OFFER", validate_offer)

    @staticmethod
    def _journal_image(record: dict[str, Any]) -> bytes | None:
        encoded = record["postimage"]
        if encoded is None:
            return None
        try:
            return base64.b64decode(encoded.encode("ascii"), validate=True)
        except (ValueError, UnicodeEncodeError):
            raise TaskError("INVALID_TRANSACTION_JOURNAL") from None

    def _claim_receipt_for_journal(
        self,
        claim: dict[str, Any],
        journal: dict[str, Any],
        recorded_at: str | None = None,
    ) -> dict[str, Any]:
        if (
            journal["status"] != "committed"
            or journal["runtimeKey"] != self.key
            or journal["committedHead"] is None
            or journal["expectedHead"] != claim["claimBaseHead"]
        ):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        state_path = f"{self.task_path}/task.json"
        offer_path = f"{self.task_path}/offer.json"
        expected_paths = sorted({state_path, offer_path})
        records = {record["path"]: record for record in journal["files"]}
        if sorted(records) != expected_paths:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        if not is_ancestor(self.candidate_root, claim["claimBaseHead"], journal["committedHead"]):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        try:
            parent = git(self.candidate_root, "rev-parse", f"{journal['committedHead']}^", code="CLAIM_RECEIPT_UNAVAILABLE").decode("ascii").strip()
        except UnicodeDecodeError:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None
        if parent != claim["claimBaseHead"] or changed_paths(self.candidate_root, journal["committedHead"]) != expected_paths:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        state_raw = self._journal_image(records[state_path])
        offer_raw = self._journal_image(records[offer_path])
        if state_raw is None or offer_raw is None:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        if read_tree_file(self.candidate_root, journal["committedHead"], state_path) != state_raw:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        if read_tree_file(self.candidate_root, journal["committedHead"], offer_path) != offer_raw:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        try:
            state = json.loads(state_raw)
            offer = json.loads(offer_raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE") from None
        if not isinstance(state, dict) or state_raw != canonical_bytes(state) or not isinstance(offer, dict) or offer_raw != canonical_bytes(offer):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        validate_state(state)
        validate_offer(offer)
        state_claim = state["lifecycle"]["claim"]
        if (
            state["lifecycle"]["phase"] != "implementing"
            or state_claim is None
            or state_claim["claimId"] != claim["claimId"]
            or state_claim["claimBaseHead"] != claim["claimBaseHead"]
            or offer["offerId"] != claim["offerId"]
            or offer["status"] != "consumed"
        ):
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        receipt = {
            "schemaVersion": RUNTIME_SCHEMA_VERSION,
            "kind": "claim-receipt",
            "taskId": state["taskId"],
            "repository": state["repository"]["identity"],
            "taskBranch": state["repository"]["taskBranch"],
            "taskPath": state["repository"]["taskPath"],
            "offerId": claim["offerId"],
            "claimId": claim["claimId"],
            "epoch": claim["epoch"],
            "claimBaseHead": claim["claimBaseHead"],
            "claimCommit": journal["committedHead"],
            "claimStateDigest": sha256_bytes(state_raw),
            "offerDigest": sha256_bytes(offer_raw),
            "transactionId": journal["transactionId"],
            "transactionDigest": journal["journalDigest"],
            "recordedAt": recorded_at or self.clock.now(),
        }
        receipt["receiptDigest"] = digest_object(receipt)
        validate_claim_receipt(receipt)
        return receipt

    def _ensure_claim_receipt(self, claim_id: str) -> dict[str, Any]:
        state = self._state()
        claim = state["lifecycle"]["claim"]
        if claim is None or claim["claimId"] != claim_id:
            raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
        try:
            receipt = self.runtime.read_claim_receipt(claim_id)
        except TaskError as error:
            if error.code != "CLAIM_RECEIPT_UNAVAILABLE":
                raise
        else:
            expected = self._claim_receipt_for_journal(
                claim,
                self.runtime.read_journal(receipt["transactionId"]),
                receipt["recordedAt"],
            )
            if receipt != expected:
                raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")
            self.runtime.delete_capability(claim["offerId"])
            self.runtime.delete_envelopes_for_offer(claim["offerId"])
            return receipt
        for journal in self.runtime.committed_journals():
            try:
                receipt = self._claim_receipt_for_journal(claim, journal)
            except TaskError as error:
                if error.code == "CLAIM_RECEIPT_UNAVAILABLE":
                    continue
                raise
            self.runtime.write_claim_receipt(claim_id, receipt)
            self.runtime.delete_capability(claim["offerId"])
            self.runtime.delete_envelopes_for_offer(claim["offerId"])
            return receipt
        raise TaskError("CLAIM_RECEIPT_UNAVAILABLE")

    @staticmethod
    def _require_unblocked(state: dict[str, Any]) -> None:
        if state["lifecycle"]["blocked"] is not None:
            raise TaskError("TASK_BLOCKED")

    @staticmethod
    def _require_planning(state: dict[str, Any]) -> None:
        if state["lifecycle"]["phase"] != "planning":
            raise TaskError("INVALID_TRANSITION")

    def _transact(
        self,
        expected_head: str,
        expected_revision: int,
        builder: Any,
    ) -> dict[str, Any]:
        return self.transactions.execute(expected_head, expected_revision, builder)

    def status(self) -> dict[str, Any]:
        state = self._state()
        phase = state["lifecycle"]["phase"]
        if self.runtime.doubt_path(self.key).exists():
            phase = "transaction_in_doubt"
        return {
            "status": "ok",
            "taskId": state["taskId"],
            "phase": phase,
            "revision": state["revision"],
            "head": head(self.candidate_root),
            "requirementsReady": state["documents"]["requirements"]["status"] == "ready",
            "planApproved": state["approval"] is not None,
            "implementationAuthorized": state["implementationAuthorization"] is not None,
            "blocked": state["lifecycle"]["blocked"] is not None,
        }

    def requirements_ready(self, expected_head: str, expected_revision: int) -> dict[str, Any]:
        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            self._require_planning(state)
            record = deepcopy(state["documents"]["requirements"])
            record["status"] = "ready"
            updated = deepcopy(state)
            updated["documents"]["requirements"] = record
            updated = advance_state(updated, "requirements_ready", self.clock.now(), expected_head, record)
            return TransactionChange(
                {f"{self.task_path}/task.json": canonical_bytes(updated)},
                "标记需求已就绪",
                {"status": "requirements_ready", "revision": updated["revision"]},
            )

        return self._transact(expected_head, expected_revision, builder)

    def propose_plan(
        self,
        expected_head: str,
        expected_revision: int,
        plan_file: Path,
        implementation_file: Path | None = None,
    ) -> dict[str, Any]:
        if plan_file.is_symlink() or not plan_file.is_file():
            raise TaskError("INVALID_PLANNING_DOCUMENT")
        plan_raw = plan_file.read_bytes()
        plan_digest, material_digest = inspect_plan(plan_raw)
        implementation_raw: bytes | None = None
        if implementation_file is not None:
            if implementation_file.is_symlink() or not implementation_file.is_file():
                raise TaskError("INVALID_PLANNING_DOCUMENT")
            implementation_raw = implementation_file.read_bytes()
            parse_sections(implementation_raw, IMPLEMENTATION_SECTIONS)

        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            self._require_planning(state)
            current = state["documents"]["plan"]
            material_changed = current["materialDigest"] != material_digest
            updated = deepcopy(state)
            plan = deepcopy(current)
            plan["digest"] = plan_digest
            plan["documentRevision"] += 1
            if material_changed:
                plan["version"] += 1
                plan["materialDigest"] = material_digest
                plan["status"] = "proposed"
                updated["approval"] = None
                updated["implementationAuthorization"] = None
                updated["actionAuthorizationDigest"] = None
            updated["documents"]["plan"] = plan
            files: dict[str, bytes | None] = {
                f"{self.task_path}/plan.md": plan_raw,
                f"{self.task_path}/task.json": b"",
            }
            if implementation_raw is not None:
                implementation = deepcopy(updated["documents"]["implementation"])
                implementation["digest"] = sha256_bytes(implementation_raw)
                implementation["documentRevision"] += 1
                implementation["version"] += 1
                updated["documents"]["implementation"] = implementation
                files[f"{self.task_path}/implementation.md"] = implementation_raw
            if material_changed:
                files[f"{self.task_path}/authorization.json"] = None
                files[f"{self.task_path}/offer.json"] = None
            event = {
                "planVersion": plan["version"],
                "documentRevision": plan["documentRevision"],
                "materialChanged": material_changed,
                "materialDigest": material_digest,
            }
            updated = advance_state(updated, "plan_proposed", self.clock.now(), expected_head, event)
            files[f"{self.task_path}/task.json"] = canonical_bytes(updated)
            return TransactionChange(
                files,
                "更新任务计划",
                {"status": "plan_proposed", "revision": updated["revision"], **event},
            )

        return self._transact(expected_head, expected_revision, builder)

    def _new_authorization(
        self,
        state: dict[str, Any],
        decision_ref: str,
        mode: str,
        allowed_actions: list[str],
    ) -> dict[str, Any]:
        require_string(decision_ref, "INVALID_DECISION_REF")
        if mode not in ACTION_MODES:
            raise TaskError("INVALID_AUTHORIZATION")
        actions = sorted(set(allowed_actions))
        if actions != allowed_actions or not set(actions).issubset(KNOWN_ACTIONS):
            raise TaskError("INVALID_AUTHORIZATION")
        if mode == "implement_only" and "conditional_merge" in actions:
            raise TaskError("INVALID_AUTHORIZATION")
        plan = state["documents"]["plan"]
        repo = state["repository"]
        nonce = self.nonce.token()
        value = {
            "schemaVersion": TASK_SCHEMA_VERSION,
            "authorizationId": digest_object({"taskId": state["taskId"], "nonce": nonce}),
            "taskId": state["taskId"],
            "repository": repo["identity"],
            "baseBranch": repo["baseBranch"],
            "baseSha": repo["baseSha"],
            "taskBranch": repo["taskBranch"],
            "planVersion": plan["version"],
            "materialDigest": plan["materialDigest"],
            "mode": mode,
            "allowedActions": actions,
            "decisionRef": decision_ref,
            "recordedAt": self.clock.now(),
        }
        value["authorizationDigest"] = authorization_digest(value)
        validate_authorization(value)
        return value

    def approve_plan(
        self,
        expected_head: str,
        expected_revision: int,
        decision_ref: str,
        authorize_implementation: bool = False,
        mode: str | None = None,
        allowed_actions: list[str] | None = None,
    ) -> dict[str, Any]:
        require_string(decision_ref, "INVALID_DECISION_REF")
        if authorize_implementation and (mode is None or allowed_actions is None):
            raise TaskError("INVALID_AUTHORIZATION")
        if not authorize_implementation and (mode is not None or allowed_actions is not None):
            raise TaskError("INVALID_AUTHORIZATION")

        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            self._require_planning(state)
            if state["documents"]["requirements"]["status"] != "ready":
                raise TaskError("REQUIREMENTS_NOT_READY")
            plan = state["documents"]["plan"]
            approval = {
                "planVersion": plan["version"],
                "materialDigest": plan["materialDigest"],
                "decisionRef": decision_ref,
                "approvedAt": self.clock.now(),
            }
            updated = deepcopy(state)
            updated["documents"]["plan"]["status"] = "approved"
            updated["approval"] = approval
            files: dict[str, bytes | None] = {}
            event: dict[str, Any] = {"approval": approval, "authorizedTogether": authorize_implementation}
            if authorize_implementation:
                authorization = self._new_authorization(updated, decision_ref, mode or "", allowed_actions or [])
                updated["implementationAuthorization"] = {
                    "planVersion": plan["version"],
                    "materialDigest": plan["materialDigest"],
                    "decisionRef": decision_ref,
                    "authorizedAt": self.clock.now(),
                }
                updated["actionAuthorizationDigest"] = authorization["authorizationDigest"]
                files[f"{self.task_path}/authorization.json"] = canonical_bytes(authorization)
                event["authorizationDigest"] = authorization["authorizationDigest"]
            updated = advance_state(updated, "plan_approved", self.clock.now(), expected_head, event)
            files[f"{self.task_path}/task.json"] = canonical_bytes(updated)
            return TransactionChange(
                files,
                "批准任务计划",
                {"status": "plan_approved", "revision": updated["revision"], "authorizedTogether": authorize_implementation},
            )

        return self._transact(expected_head, expected_revision, builder)

    def authorize(
        self,
        expected_head: str,
        expected_revision: int,
        decision_ref: str,
        mode: str,
        allowed_actions: list[str],
    ) -> dict[str, Any]:
        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            self._require_planning(state)
            plan = state["documents"]["plan"]
            approval = state["approval"]
            if approval is None or approval["planVersion"] != plan["version"] or approval["materialDigest"] != plan["materialDigest"]:
                raise TaskError("PLAN_NOT_APPROVED")
            authorization = self._new_authorization(state, decision_ref, mode, allowed_actions)
            updated = deepcopy(state)
            updated["implementationAuthorization"] = {
                "planVersion": plan["version"],
                "materialDigest": plan["materialDigest"],
                "decisionRef": decision_ref,
                "authorizedAt": self.clock.now(),
            }
            updated["actionAuthorizationDigest"] = authorization["authorizationDigest"]
            updated = advance_state(updated, "authorized", self.clock.now(), expected_head, authorization)
            return TransactionChange(
                {
                    f"{self.task_path}/task.json": canonical_bytes(updated),
                    f"{self.task_path}/authorization.json": canonical_bytes(authorization),
                },
                "记录实施授权",
                {"status": "authorized", "revision": updated["revision"], "authorizationDigest": authorization["authorizationDigest"]},
            )

        return self._transact(expected_head, expected_revision, builder)

    def offer(
        self,
        expected_head: str,
        expected_revision: int,
        route: str,
        role_digest: str,
        config_digest: str,
        expires_at: str,
        role_name: str | None = None,
        bundle_digest: str | None = None,
    ) -> dict[str, Any]:
        require_string(route, "INVALID_ROUTE")
        require_sha256(role_digest, "INVALID_ROLE_DIGEST")
        require_sha256(config_digest, "INVALID_CONFIG_DIGEST")
        require_utc(expires_at, "INVALID_OFFER_EXPIRY")
        if (role_name is None) != (bundle_digest is None):
            raise TaskError("INVALID_OFFER")
        if role_name is not None:
            require_string(role_name, "INVALID_ROLE_NAME")
            require_sha256(bundle_digest, "INVALID_BUNDLE_DIGEST")
        capability = self.nonce.token(48)
        capability_digest = sha256_bytes(capability.encode("utf-8"))
        state_before = self._state()
        offer_id = digest_object({"taskId": state_before["taskId"], "epoch": state_before["lifecycle"]["epoch"], "nonce": self.nonce.token()})
        created_at = self.clock.now()
        capability_record = {
            "schemaVersion": RUNTIME_SCHEMA_VERSION,
            "kind": "capability",
            "offerId": offer_id,
            "epoch": state_before["lifecycle"]["epoch"],
            "capability": capability,
            "capabilityDigest": capability_digest,
            "createdAt": created_at,
        }
        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            self._require_planning(state)
            plan = state["documents"]["plan"]
            implementation = state["implementationAuthorization"]
            if state["approval"] is None or implementation is None:
                raise TaskError("IMPLEMENTATION_NOT_AUTHORIZED")
            authorization = self._authorization()
            if (
                authorization["authorizationDigest"] != state["actionAuthorizationDigest"]
                or authorization["planVersion"] != plan["version"]
                or authorization["materialDigest"] != plan["materialDigest"]
            ):
                raise TaskError("authorization_mismatch")
            if expires_at <= self.clock.now():
                raise TaskError("OFFER_EXPIRED")
            value = {
                "schemaVersion": 2 if role_name is not None else TASK_SCHEMA_VERSION,
                "offerId": offer_id,
                "status": "active",
                "epoch": state["lifecycle"]["epoch"],
                "taskId": state["taskId"],
                "repository": state["repository"]["identity"],
                "taskBranch": state["repository"]["taskBranch"],
                "expectedHead": expected_head,
                "expectedRevision": expected_revision,
                "route": route,
                "planVersion": plan["version"],
                "planMaterialDigest": plan["materialDigest"],
                "authorizationDigest": authorization["authorizationDigest"],
                "allowedActions": authorization["allowedActions"],
                "roleDigest": role_digest,
                "configDigest": config_digest,
                "capabilityDigest": capability_digest,
                "createdAt": created_at,
                "expiresAt": expires_at,
                "consumedByDigest": None,
            }
            if role_name is not None:
                value["roleName"] = role_name
                value["bundleDigest"] = bundle_digest
            validate_offer(value)
            updated = deepcopy(state)
            updated["lifecycle"]["phase"] = "awaiting_claim"
            updated["lifecycle"]["writer"] = None
            updated["lifecycle"]["offer"] = {
                "offerId": offer_id,
                "epoch": value["epoch"],
                "authorizationDigest": value["authorizationDigest"],
            }
            updated = advance_state(updated, "offer_created", self.clock.now(), expected_head, value)
            return TransactionChange(
                {
                    f"{self.task_path}/task.json": canonical_bytes(updated),
                    f"{self.task_path}/offer.json": canonical_bytes(value),
                },
                "创建执行要约",
                {"status": "awaiting_claim", "revision": updated["revision"], "offerId": offer_id},
            )

        self.runtime.write_capability(offer_id, capability_record)
        try:
            return self._transact(expected_head, expected_revision, builder)
        except Exception:
            try:
                current_head = head(self.candidate_root)
                current_offer = self._state()["lifecycle"]["offer"]
                committed_this_offer = (
                    current_head != expected_head
                    and current_offer is not None
                    and current_offer["offerId"] == offer_id
                )
                if not committed_this_offer:
                    self.runtime.delete_capability(offer_id)
            except Exception:
                pass
            raise

    def handoff(self) -> dict[str, Any]:
        before = head(self.candidate_root)
        require_clean(self.candidate_root)
        state = self._state()
        if state["lifecycle"]["phase"] != "awaiting_claim":
            raise TaskError("INVALID_TRANSITION")
        offer = self._offer()
        capability = self.runtime.read_capability(offer["offerId"])
        if (
            offer["status"] != "active"
            or offer["offerId"] != capability["offerId"]
            or offer["epoch"] != capability["epoch"]
            or offer["capabilityDigest"] != capability["capabilityDigest"]
        ):
            raise TaskError("CAPABILITY_MISMATCH")
        envelope_id = digest_object({"offerId": offer["offerId"], "nonce": self.nonce.token()})
        envelope = {
            "schemaVersion": RUNTIME_SCHEMA_VERSION,
            "kind": "launch-envelope",
            "envelopeId": envelope_id,
            "offerId": offer["offerId"],
            "epoch": offer["epoch"],
            "capability": capability["capability"],
            "candidateRoot": os.fspath(self.candidate_root),
            "taskPath": self.task_path,
            "route": offer["route"],
            "roleDigest": offer["roleDigest"],
            "configDigest": offer["configDigest"],
            "createdAt": self.clock.now(),
        }
        if offer["schemaVersion"] == 2:
            envelope["roleName"] = offer["roleName"]
            envelope["bundleDigest"] = offer["bundleDigest"]
        envelope["envelopeDigest"] = digest_object(envelope)
        self.runtime.write_envelope(envelope_id, envelope)
        if head(self.candidate_root) != before or not is_clean(self.candidate_root):
            raise TaskError("HANDOFF_TRACKED_STATE_CHANGED")
        return {"status": "handoff_ready", "offerId": offer["offerId"], "envelopeId": envelope_id}

    def claim(self, expected_head: str, expected_revision: int, envelope_id: str) -> dict[str, Any]:
        require_sha256(envelope_id, "INVALID_LAUNCH_ENVELOPE")
        envelope = self.runtime.read_envelope(envelope_id)
        holder: dict[str, Any] = {}

        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            if state["lifecycle"]["phase"] != "awaiting_claim":
                raise TaskError("OFFER_CONFLICT")
            offer = self._offer()
            if (
                offer["status"] != "active"
                or offer["offerId"] != envelope["offerId"]
                or offer["epoch"] != envelope["epoch"]
                or offer["epoch"] != state["lifecycle"]["epoch"]
                or sha256_bytes(envelope["capability"].encode("utf-8")) != offer["capabilityDigest"]
                or envelope["route"] != offer["route"]
                or envelope["roleDigest"] != offer["roleDigest"]
                or envelope["configDigest"] != offer["configDigest"]
                or offer["authorizationDigest"] != state["actionAuthorizationDigest"]
            ):
                raise TaskError("CAPABILITY_MISMATCH")
            if offer["schemaVersion"] == 2 and (
                envelope.get("roleName") != offer["roleName"]
                or envelope.get("bundleDigest") != offer["bundleDigest"]
            ):
                raise TaskError("CAPABILITY_MISMATCH")
            if offer["expiresAt"] <= self.clock.now():
                raise TaskError("OFFER_EXPIRED")
            evidence_expectation = {
                "route": offer["route"],
                "roleDigest": offer["roleDigest"],
                "configDigest": offer["configDigest"],
            }
            if offer["schemaVersion"] == 2:
                evidence_expectation.update(
                    {
                        "taskId": state["taskId"],
                        "repository": state["repository"]["identity"],
                        "taskBranch": state["repository"]["taskBranch"],
                        "offerId": offer["offerId"],
                        "envelopeId": envelope["envelopeId"],
                        "roleName": offer["roleName"],
                        "bundleDigest": offer["bundleDigest"],
                    }
                )
            evidence = self.evidence_provider.observe("claim", evidence_expectation)
            validate_runtime_evidence(evidence)
            if (
                evidence["status"] != "active"
                or evidence["route"] != offer["route"]
                or evidence["roleDigest"] != offer["roleDigest"]
                or evidence["configDigest"] != offer["configDigest"]
            ):
                raise TaskError("RUNTIME_EVIDENCE_MISMATCH")
            claim_id = digest_object({"offerId": offer["offerId"], "sessionDigest": evidence["sessionDigest"], "nonce": self.nonce.token()})
            claim = {
                "claimId": claim_id,
                "offerId": offer["offerId"],
                "epoch": offer["epoch"],
                "writerId": evidence["writerId"],
                "sessionDigest": evidence["sessionDigest"],
                "roleDigest": evidence["roleDigest"],
                "configDigest": evidence["configDigest"],
                "claimedAt": self.clock.now(),
                "claimBaseHead": expected_head,
            }
            updated_offer = deepcopy(offer)
            updated_offer["status"] = "consumed"
            updated_offer["consumedByDigest"] = digest_object(claim)
            updated = deepcopy(state)
            updated["lifecycle"]["phase"] = "implementing"
            updated["lifecycle"]["writer"] = {
                "claimId": claim_id,
                "writerId": evidence["writerId"],
                "sessionDigest": evidence["sessionDigest"],
            }
            updated["lifecycle"]["claim"] = claim
            updated = advance_state(updated, "claimed", self.clock.now(), expected_head, claim)
            holder["claim"] = claim
            return TransactionChange(
                {
                    f"{self.task_path}/task.json": canonical_bytes(updated),
                    f"{self.task_path}/offer.json": canonical_bytes(updated_offer),
                },
                "认领任务执行权",
                {"status": "implementing", "revision": updated["revision"], "claimId": claim_id},
            )

        result = self._transact(expected_head, expected_revision, builder)
        claim = holder["claim"]
        receipt = self._claim_receipt_for_journal(claim, self.runtime.read_journal(result["transactionId"]))
        self.runtime.write_claim_receipt(claim["claimId"], receipt)
        self.runtime.delete_capability(claim["offerId"])
        self.runtime.delete_envelopes_for_offer(claim["offerId"])
        consume = getattr(self.evidence_provider, "consume", None)
        if consume is not None:
            consume(claim["claimId"], result["head"], receipt["receiptDigest"], self.clock.now())
        return result

    def _retire(
        self,
        expected_head: str,
        expected_revision: int,
        event_type: str,
        reason: str,
        require_terminal_evidence: bool,
    ) -> dict[str, Any]:
        require_string(reason, "INVALID_RETIRE_REASON")
        offer_id_holder: dict[str, str] = {}

        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            phase = state["lifecycle"]["phase"]
            if phase not in {"awaiting_claim", "implementing"}:
                raise TaskError("INVALID_TRANSITION")
            if require_terminal_evidence:
                if phase != "implementing" or state["lifecycle"]["claim"] is None:
                    raise TaskError("INVALID_TRANSITION")
                claim = state["lifecycle"]["claim"]
                evidence = self.evidence_provider.observe("reclaim", claim)
                validate_runtime_evidence(evidence)
                offer = self._offer()
                if (
                    evidence["status"] not in {"terminal", "missing"}
                    or evidence["writerId"] != claim["writerId"]
                    or evidence["sessionDigest"] != claim["sessionDigest"]
                    or evidence["roleDigest"] != claim["roleDigest"]
                    or evidence["configDigest"] != claim["configDigest"]
                    or evidence["route"] != offer["route"]
                ):
                    raise TaskError("WRITER_STILL_ACTIVE")
            offer = self._offer()
            offer_id_holder["offerId"] = offer["offerId"]
            retired = {
                "offerId": offer["offerId"],
                "claim": deepcopy(state["lifecycle"]["claim"]),
                "epoch": state["lifecycle"]["epoch"],
                "reason": reason,
                "retiredAt": self.clock.now(),
            }
            updated_offer = deepcopy(offer)
            updated_offer["status"] = "revoked"
            updated = deepcopy(state)
            updated["lifecycle"]["phase"] = "planning"
            updated["lifecycle"]["epoch"] += 1
            updated["lifecycle"]["writer"] = None
            updated["lifecycle"]["offer"] = None
            updated["lifecycle"]["claim"] = None
            updated["lifecycle"]["retiredClaims"].append(retired)
            updated = advance_state(updated, event_type, self.clock.now(), expected_head, retired)
            return TransactionChange(
                {
                    f"{self.task_path}/task.json": canonical_bytes(updated),
                    f"{self.task_path}/offer.json": canonical_bytes(updated_offer),
                },
                "撤销任务执行权" if event_type == "revoked" else "回收任务执行权",
                {"status": event_type, "revision": updated["revision"], "epoch": updated["lifecycle"]["epoch"]},
            )

        result = self._transact(expected_head, expected_revision, builder)
        offer_id = offer_id_holder["offerId"]
        self.runtime.delete_capability(offer_id)
        self.runtime.delete_envelopes_for_offer(offer_id)
        return result

    def recover_activation(self) -> dict[str, Any]:
        recover = getattr(self.evidence_provider, "recover_consumption", None)
        if recover is None:
            raise TaskError("RUNTIME_EVIDENCE_UNAVAILABLE")
        state = self._state()
        claim = state["lifecycle"]["claim"]
        if state["lifecycle"]["phase"] != "implementing" or claim is None:
            raise TaskError("INVALID_TRANSITION")
        receipt = self._ensure_claim_receipt(claim["claimId"])
        return recover(state, claim, receipt, self.clock.now())

    def _require_activation_receipt(self, claim: dict[str, Any], claim_receipt: dict[str, Any]) -> None:
        offer = self._offer()
        if offer["schemaVersion"] == TASK_SCHEMA_VERSION:
            return
        from gkd_role.activation import validate_activation, validate_activation_receipt

        receipt = self.runtime.read_claim_activation_receipt(claim["claimId"])
        validate_activation_receipt(receipt)
        activation = self.runtime.read_activation(receipt["activationId"])
        validate_activation(activation)
        if (
            receipt["claimId"] != claim["claimId"]
            or receipt["claimCommit"] != claim_receipt["claimCommit"]
            or receipt["claimReceiptDigest"] != claim_receipt["receiptDigest"]
            or receipt["activationDigest"] != activation["activationDigest"]
            or activation["offerId"] != claim["offerId"]
            or activation["agentId"] != claim["writerId"]
            or activation["threadDigest"] != claim["sessionDigest"]
            or activation["roleName"] != offer["roleName"]
            or activation["roleDigest"] != offer["roleDigest"]
            or activation["configDigest"] != offer["configDigest"]
            or activation["bundleDigest"] != offer["bundleDigest"]
            or activation["route"] != offer["route"]
        ):
            raise TaskError("INVALID_ACTIVATION_RECEIPT")

    def revoke(self, expected_head: str, expected_revision: int, reason: str) -> dict[str, Any]:
        return self._retire(expected_head, expected_revision, "revoked", reason, False)

    def reclaim(self, expected_head: str, expected_revision: int, reason: str) -> dict[str, Any]:
        return self._retire(expected_head, expected_revision, "reclaimed", reason, True)

    def block(self, expected_head: str, expected_revision: int, reason: str, owner: str) -> dict[str, Any]:
        require_string(reason, "INVALID_BLOCK")
        require_string(owner, "INVALID_BLOCK")

        def builder(state: dict[str, Any]) -> TransactionChange:
            if state["lifecycle"]["blocked"] is not None or state["lifecycle"]["phase"] in {"completed"}:
                raise TaskError("INVALID_TRANSITION")
            record = {"reason": reason, "owner": owner, "blockedAt": self.clock.now()}
            updated = deepcopy(state)
            updated["lifecycle"]["blocked"] = record
            updated = advance_state(updated, "blocked", self.clock.now(), expected_head, record)
            return TransactionChange(
                {f"{self.task_path}/task.json": canonical_bytes(updated)},
                "记录任务阻塞",
                {"status": "blocked", "revision": updated["revision"]},
            )

        return self._transact(expected_head, expected_revision, builder)

    def resume(self, expected_head: str, expected_revision: int) -> dict[str, Any]:
        def builder(state: dict[str, Any]) -> TransactionChange:
            if state["lifecycle"]["blocked"] is None:
                raise TaskError("INVALID_TRANSITION")
            record = state["lifecycle"]["blocked"]
            updated = deepcopy(state)
            updated["lifecycle"]["blocked"] = None
            updated = advance_state(updated, "resumed", self.clock.now(), expected_head, record)
            return TransactionChange(
                {f"{self.task_path}/task.json": canonical_bytes(updated)},
                "恢复任务执行",
                {"status": "resumed", "revision": updated["revision"]},
            )

        return self._transact(expected_head, expected_revision, builder)

    def deliver(self, expected_head: str, expected_revision: int, claim_id: str) -> dict[str, Any]:
        require_sha256(claim_id, "CLAIM_MISMATCH")
        current_claim = self._state()["lifecycle"]["claim"]
        if current_claim is None or current_claim["claimId"] != claim_id:
            raise TaskError("CLAIM_MISMATCH")
        claim_receipt = self._ensure_claim_receipt(claim_id)
        self._require_activation_receipt(current_claim, claim_receipt)

        def builder(state: dict[str, Any]) -> TransactionChange:
            self._require_unblocked(state)
            if state["lifecycle"]["phase"] != "implementing":
                raise TaskError("INVALID_TRANSITION")
            claim = state["lifecycle"]["claim"]
            if claim is None or claim["claimId"] != claim_id or claim["epoch"] != state["lifecycle"]["epoch"]:
                raise TaskError("CLAIM_MISMATCH")
            authorization = self._authorization()
            if authorization["authorizationDigest"] != state["actionAuthorizationDigest"]:
                raise TaskError("authorization_mismatch")
            record = {"implementationHead": expected_head, "claimId": claim_id, "deliveredAt": self.clock.now()}
            updated = deepcopy(state)
            updated["lifecycle"]["phase"] = "delivered"
            updated["lifecycle"]["writer"] = None
            updated["lifecycle"]["delivery"] = record
            updated = advance_state(updated, "delivered", self.clock.now(), expected_head, record)
            return TransactionChange(
                {f"{self.task_path}/task.json": canonical_bytes(updated)},
                "交付任务候选",
                {"status": "delivered", "revision": updated["revision"], "implementationHead": expected_head},
            )

        return self._transact(expected_head, expected_revision, builder)

    def doctor(self, mode: str) -> dict[str, Any]:
        if mode not in {"static", "live", "historical"}:
            raise TaskError("INVALID_DOCTOR_MODE")
        state = self._state()
        if state["actionAuthorizationDigest"] is not None:
            authorization = self._authorization()
            if authorization["authorizationDigest"] != state["actionAuthorizationDigest"]:
                raise TaskError("authorization_mismatch")
        if state["lifecycle"]["offer"] is not None or (self.task_root / "offer.json").exists():
            offer = self._offer()
            summary = state["lifecycle"]["offer"]
            if summary is not None and offer["offerId"] != summary["offerId"]:
                raise TaskError("OFFER_MISMATCH")
        if mode == "live":
            if self.runtime.doubt_path(self.key).exists():
                raise TaskError("transaction_in_doubt")
            if self.transactions._current_active() is not None:
                raise TaskError("TRANSACTION_RECOVERY_REQUIRED")
            verify_identity(
                self.candidate_root,
                state["repository"]["identity"],
                state["repository"]["taskBranch"],
            )
            attachment = self.runtime.read_attachment(
                state["repository"]["identity"], state["taskId"], state["repository"]["taskBranch"]
            )
            if Path(attachment["candidateRoot"]).resolve() != self.candidate_root:
                raise TaskError("CANDIDATE_IDENTITY_MISMATCH")
        if mode == "historical":
            if state["lifecycle"]["phase"] != "completed":
                raise TaskError("HISTORICAL_STATE_INCOMPLETE")
            try:
                self.runtime.read_attachment(
                    state["repository"]["identity"], state["taskId"], state["repository"]["taskBranch"]
                )
            except TaskError as error:
                if error.code != "worktree_missing":
                    raise
            else:
                raise TaskError("HISTORICAL_RUNTIME_PRESENT")
        return {"status": "valid", "mode": mode, "taskId": state["taskId"], "phase": state["lifecycle"]["phase"], "revision": state["revision"]}

    def recover(self) -> dict[str, Any]:
        return self.transactions.recover()

    def attach(self) -> dict[str, Any]:
        state = self._state()
        repository = state["repository"]
        self.runtime.write_attachment(
            {
                "schemaVersion": RUNTIME_SCHEMA_VERSION,
                "kind": "attachment",
                "repository": repository["identity"],
                "taskId": state["taskId"],
                "taskBranch": repository["taskBranch"],
                "taskPath": repository["taskPath"],
                "candidateRoot": os.fspath(self.candidate_root),
                "commonDir": os.fspath(common_dir(self.candidate_root)),
                "updatedAt": self.clock.now(),
            }
        )
        return {"status": "attached", "taskId": state["taskId"]}
