"""Isolated bare-origin and task fixtures."""

from __future__ import annotations

from copy import deepcopy
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

from gkd_task.acceptance import MergeIndeterminate
from gkd_task.canonical import FixedClock, SystemNonce, canonical_bytes, digest_object
from gkd_task.documents import PLAN_MATERIAL_SECTIONS
from gkd_task.model import read_state, validate_state
from gkd_task.results import DEFAULT_LANE, DEFAULT_PROFILE, lane_profile_scopes
from gkd_task.runtime import RuntimeStore
from gkd_task.service import TaskService, bootstrap_task
from tests.task_core.evidence_support import FixtureEvidenceProvider, make_fixture_evidence


FIXED_TIME = "2026-01-02T03:04:05Z"
FUTURE_TIME = "2027-01-02T03:04:05Z"
ROLE_DIGEST = hashlib.sha256(b"role-policy-v1").hexdigest()
CONFIG_DIGEST = hashlib.sha256(b"role-config-v1").hexdigest()
SESSION_DIGEST = hashlib.sha256(b"session-v1").hexdigest()
REVIEWER_DIGEST = hashlib.sha256(b"independent-reviewer").hexdigest()


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
    return value


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"command failed: {args!r}: {result.stderr}")
    return result.stdout.strip()


def _section_document(title: str, sections: list[tuple[str, str]]) -> str:
    chunks = [f"# {title}", ""]
    for heading, body in sections:
        chunks.extend((f"## {heading}", "", body, ""))
    return "\n".join(chunks)


def planning_documents(material_overrides: dict[str, str] | None = None, notes: str = "Initial notes.") -> dict[str, str]:
    overrides = material_overrides or {}
    requirements = _section_document(
        "Fixture Requirements",
        [
            ("Goal", "Build a deterministic fixture."),
            ("User Decisions", "Use the reviewed generic policy."),
            ("Scope", "Only the fixture repository."),
            ("Non-Goals", "No production installation."),
            ("Acceptance Criteria", "All fixture contracts pass."),
        ],
    )
    plan = _section_document(
        "Fixture Plan",
        [(heading, overrides.get(heading, f"Approved {heading.lower()} contract.")) for heading in PLAN_MATERIAL_SECTIONS]
        + [("Implementation Notes", notes)],
    )
    implementation = _section_document(
        "Fixture Implementation",
        [("Internal Design", "Use standard-library components."), ("Execution Details", "Run inside temporary repositories.")],
    )
    return {"requirements.md": requirements, "plan.md": plan, "implementation.md": implementation}


class TaskRepo:
    def __init__(self, identity: str = "github.com/team/repository", base_branch: str = "trunk") -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-task-contract-")
        self.root = Path(self.temporary.name)
        self.origin = self.root / "origin.git"
        self.main = self.root / "main"
        self.candidate = self.root / "candidate"
        self.package = self.root / "package"
        self.runtime_root = self.root / "runtime"
        self.runtime_root.mkdir()
        self.production = self.root / "production-codex"
        self.production.mkdir()
        self.task_id = "TASK-ALPHA"
        self.task_path = "tasks/task-alpha"
        self.task_branch = "task/task-alpha"
        self.base_branch = base_branch
        self.identity = identity
        run("git", "init", "--bare", f"--initial-branch={base_branch}", str(self.origin))
        run("git", "clone", str(self.origin), str(self.main))
        run("git", "config", "user.name", "Fixture", cwd=self.main)
        run("git", "config", "user.email", "fixture@example.test", cwd=self.main)
        run("git", "config", "remote.origin.gkdIdentity", identity, cwd=self.main)
        (self.main / ".git" / "info" / "exclude").write_text(
            ".codex/\n.agents/\n.gkd/runtime-project.json\n",
            encoding="utf-8",
        )
        (self.main / "README.md").write_text("fixture\n", encoding="utf-8")
        (self.main / ".gkd").mkdir()
        (self.main / ".gkd" / "policy.json").write_bytes(
            canonical_bytes(
                {
                    "schemaVersion": 1,
                    "provider": "github",
                    "repository": identity,
                    "baseBranch": base_branch,
                    "requiredChecks": ["contract"],
                }
            )
        )
        run("git", "add", "README.md", ".gkd/policy.json", cwd=self.main)
        run("git", "commit", "-m", "base", cwd=self.main)
        run("git", "push", "-u", "origin", base_branch, cwd=self.main)
        self.base_sha = run("git", "rev-parse", "HEAD", cwd=self.main)
        github_remote = f"https://{identity}.git"
        run("git", "remote", "set-url", "origin", github_remote, cwd=self.main)
        run("git", "config", "--local", f"url.file://{self.origin}.insteadOf", github_remote, cwd=self.main)
        self.write_package(planning_documents())
        bootstrap_task(
            self.main,
            self.candidate,
            self.package,
            self.task_id,
            self.task_path,
            self.identity,
            self.base_branch,
            self.base_sha,
            self.task_branch,
            self.runtime_root,
            FixedClock(FIXED_TIME),
        )
        run("git", "config", "user.name", "Fixture", cwd=self.candidate)
        run("git", "config", "user.email", "fixture@example.test", cwd=self.candidate)

    def close(self) -> None:
        for _ in range(100):
            try:
                self.temporary.cleanup()
                return
            except OSError as error:
                if error.errno != errno.ENOTEMPTY:
                    raise
                time.sleep(0.01)
        self.temporary.cleanup()

    def write_package(self, values: dict[str, str]) -> None:
        self.package.mkdir(exist_ok=True)
        for name, content in values.items():
            (self.package / name).write_text(content, encoding="utf-8")

    @property
    def task_root(self) -> Path:
        return self.candidate / self.task_path

    def state(self) -> dict[str, Any]:
        return read_state(self.task_root / "task.json", self.task_root)

    def head(self) -> str:
        return run("git", "rev-parse", "HEAD", cwd=self.candidate)

    def commits(self) -> int:
        return int(run("git", "rev-list", "--count", "HEAD", cwd=self.candidate))

    def service(self, evidence_status: str = "active", failure_hook: Any | None = None) -> TaskService:
        evidence = make_fixture_evidence(
            "writer-one",
            SESSION_DIGEST,
            ROLE_DIGEST,
            CONFIG_DIGEST,
            "manual",
            evidence_status,
            FIXED_TIME,
        )
        return TaskService(
            self.candidate,
            self.task_path,
            RuntimeStore(self.runtime_root),
            FixedClock(FIXED_TIME),
            SystemNonce(),
            FixtureEvidenceProvider(evidence),
            failure_hook,
        )

    def cas(self) -> tuple[str, int]:
        return self.head(), self.state()["revision"]

    def ready_and_authorized(self, mode: str = "implement_and_merge_on_acceptance") -> TaskService:
        service = self.service()
        head, revision = self.cas()
        service.requirements_ready(head, revision)
        head, revision = self.cas()
        service.approve_plan(head, revision, "decision-plan")
        actions = ["commit", "push", "pr_update", "ci_repair", "ready_for_review"]
        if mode == "implement_and_merge_on_acceptance":
            actions.append("conditional_merge")
        head, revision = self.cas()
        service.authorize(head, revision, "decision-implementation", mode, sorted(actions))
        return service

    def offer_and_claim(self) -> tuple[TaskService, str]:
        service = self.ready_and_authorized()
        head, revision = self.cas()
        service.offer(head, revision, "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        head, revision = self.cas()
        result = service.claim(head, revision, handoff["envelopeId"])
        return service, result["claimId"]

    def prepare_delivery_document(self) -> tuple[str, str]:
        path = self.task_root / "delivery.md"
        path.write_text(f"# Fixture Delivery\n\nImplementation head: {self.head()}\n", encoding="utf-8")
        relative = f"{self.task_path}/delivery.md"
        run("git", "add", relative, cwd=self.candidate)
        run("git", "commit", "-m", "prepare delivery document", "--", relative, cwd=self.candidate)
        return relative, hashlib.sha256(path.read_bytes()).hexdigest()

    def prepare_automatic_artifacts(
        self,
        candidate_output_bundle_digest: str,
        lane: str = DEFAULT_LANE,
        profile: str = DEFAULT_PROFILE,
        scope_names: tuple[str, ...] | None = None,
    ) -> tuple[str, str]:
        state = self.state()
        expected_scope_names = lane_profile_scopes(lane, profile)
        if expected_scope_names is None:
            raise AssertionError("unknown verification lane")
        scopes = scope_names or expected_scope_names
        results_path = self.task_root / "verification-results.json"
        evidence_path = self.task_root / "verification-evidence.json"
        manifest_path = self.task_root / "result-manifest.json"
        results = {
            "baseSha": state["repository"]["baseSha"],
            "canonicalResultsDigest": hashlib.sha256(self.head().encode("ascii")).hexdigest(),
            "dependenciesInstalled": False,
            "outcome": "pass",
            "lane": lane,
            "profile": profile,
            "schemaVersion": 2,
            "scopes": {scope: 1 for scope in scopes},
            "tests": len(scopes),
        }
        results_raw = canonical_bytes(results)
        verifier_digest = hashlib.sha256(results_raw).hexdigest()
        evidence = {
            "schemaVersion": 1,
            "kind": "automatic-delivery-evidence",
            "outcome": "pass",
            "candidateOutputBundleDigest": candidate_output_bundle_digest,
            "verifierResultDigest": verifier_digest,
        }
        evidence["evidenceDigest"] = digest_object(evidence)
        evidence_raw = canonical_bytes(evidence)
        manifest = {
            "lane": lane,
            "profile": profile,
            "schemaVersion": 2,
            "scopes": list(scopes),
            "kind": "automatic-delivery-result-manifest",
            "taskId": state["taskId"],
            "repository": state["repository"]["identity"],
            "taskBranch": state["repository"]["taskBranch"],
            "taskPath": state["repository"]["taskPath"],
            "baseSha": state["repository"]["baseSha"],
            "candidateOutputBundleDigest": candidate_output_bundle_digest,
            "verifierResultDigest": verifier_digest,
            "evidenceDigest": hashlib.sha256(evidence_raw).hexdigest(),
        }
        manifest["manifestDigest"] = digest_object(manifest)
        results_path.write_bytes(results_raw)
        evidence_path.write_bytes(evidence_raw)
        manifest_path.write_bytes(canonical_bytes(manifest))
        results_relative = f"{self.task_path}/verification-results.json"
        evidence_relative = f"{self.task_path}/verification-evidence.json"
        manifest_relative = f"{self.task_path}/result-manifest.json"
        run("git", "add", results_relative, evidence_relative, manifest_relative, cwd=self.candidate)
        run(
            "git",
            "commit",
            "-m",
            "prepare automatic delivery artifacts",
            "--",
            results_relative,
            evidence_relative,
            manifest_relative,
            cwd=self.candidate,
        )
        return results_relative, evidence_relative

    def deliver(
        self,
        service: TaskService,
        claim_id: str,
        candidate_output_bundle_digest: str | None = None,
        lane: str = DEFAULT_LANE,
        profile: str = DEFAULT_PROFILE,
        scope_names: tuple[str, ...] | None = None,
    ):
        artifacts = (
            self.prepare_automatic_artifacts(candidate_output_bundle_digest, lane, profile, scope_names)
            if candidate_output_bundle_digest is not None
            else (None, None)
        )
        document_path, document_digest = self.prepare_delivery_document()
        return service.deliver(
            *self.cas(),
            claim_id,
            candidate_output_bundle_digest,
            document_path,
            document_digest,
            *artifacts,
        )

    def delivered(self) -> tuple[TaskService, str]:
        service, claim_id = self.offer_and_claim()
        self.deliver(service, claim_id)
        return service, self.head()


class FakeGitHub:
    def __init__(self, snapshot: dict[str, Any], merge_result: dict[str, Any] | Exception | None = None) -> None:
        self.current = deepcopy(snapshot)
        self.merge_result = merge_result or {"status": "merged", "mergedHead": snapshot["headSha"]}
        self.calls: list[tuple[str, Any]] = []

    def snapshot(self, repository: str, pr_number: int) -> dict[str, Any]:
        self.calls.append(("snapshot", repository, pr_number))
        return deepcopy(self.current)

    def merge(self, repository: str, pr_number: int, expected_head: str) -> dict[str, Any]:
        self.calls.append(("merge", repository, pr_number, expected_head))
        if isinstance(self.merge_result, Exception):
            if isinstance(self.merge_result, MergeIndeterminate):
                self.current["state"] = "merged"
                self.current["mergedHead"] = expected_head
            raise self.merge_result
        return deepcopy(self.merge_result)


def github_snapshot(repo: TaskRepo, candidate_head: str, checks: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "repository": repo.identity,
        "prNumber": 7,
        "baseBranch": repo.base_branch,
        "headBranch": repo.task_branch,
        "headSha": candidate_head,
        "state": "open",
        "draft": False,
        "mergeable": True,
        "checks": checks if checks is not None else [{"name": "contract", "status": "success"}],
        "mergedHead": None,
    }
