"""Trusted-main facades for delivery, CI, acceptance, and rework."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Protocol

from gkd_ci.github import GitHubClient
from gkd_ci.monitor import MonitorRequest, monitor_fixed_head, validate_terminal_result
from gkd_ci.policy import POLICY_PATH, load_validated_policy, policy_binding
from gkd_task.acceptance import (
    GitHubAdapter,
    accept_candidate,
    rework_candidate,
    validate_review,
)
from gkd_task.canonical import canonical_bytes, require_sha1, sha256_bytes
from gkd_task.delivery_artifacts import artifact_paths, load_automatic_delivery_artifacts
from gkd_task.errors import TaskError
from gkd_task.gitops import (
    branch,
    common_dir,
    git,
    git_root,
    head,
    is_clean,
    repository_identity,
    read_tree_file,
)
from gkd_task.model import validate_result_manifest
from gkd_task.orchestrator import TrustedTaskContext, resolve_trusted_task_context
from gkd_task.runtime import RuntimeStore
from .facts import render_machine_facts
from gkd_role.project import refresh_project


class PullRequestLocator(Protocol):
    def find_open_pull_requests(self, repository: str, head_branch: str) -> list[int]: ...


def _trusted_main(context: TrustedTaskContext) -> Path:
    trusted = context.trusted_main_root
    if (
        repository_identity(trusted) != context.repository
        or branch(trusted) != context.base_branch
        or common_dir(trusted) != common_dir(context.candidate_root)
        or not is_clean(trusted)
    ):
        raise TaskError("TRUSTED_CONTEXT_INVALID")
    try:
        remote = git(
            trusted,
            "rev-parse",
            f"refs/remotes/origin/{context.base_branch}",
            code="TRUSTED_CONTEXT_INVALID",
        ).decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("TRUSTED_CONTEXT_INVALID") from None
    require_sha1(remote, "TRUSTED_CONTEXT_INVALID")
    if head(trusted) != remote:
        raise TaskError("TRUSTED_CONTEXT_INVALID")
    if policy_binding(load_validated_policy(trusted, context.repository, POLICY_PATH)) != context.policy:
        raise TaskError("TASK_POLICY_MISMATCH")
    return trusted


def _fixed_manifest(root: Path, commit: str, path: str) -> dict[str, Any]:
    try:
        raw = read_tree_file(root, commit, path)
        value = json.loads(raw)
    except (TaskError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_RESULT_MANIFEST") from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise TaskError("INVALID_RESULT_MANIFEST")
    validate_result_manifest(value)
    return value


class TrustedMainCIFacade:
    """Derive repository policy facts before invoking the fixed-head monitor."""

    def __init__(self, checkout: Path, github: GitHubClient | Any | None = None) -> None:
        self.checkout = git_root(checkout)
        self.repository = repository_identity(self.checkout)
        self.github = github

    def monitor(
        self,
        pull_request: int,
        expected_head: str,
        timeout_seconds: int = 3600,
        poll_interval_seconds: int = 60,
    ) -> dict[str, Any]:
        policy = load_validated_policy(self.checkout, self.repository, POLICY_PATH)
        if branch(self.checkout) != policy.base_branch or not is_clean(self.checkout):
            raise TaskError("TRUSTED_CONTEXT_INVALID")
        request = MonitorRequest(
            checkout=self.checkout,
            repository=policy.repository,
            pull_request=pull_request,
            expected_head=expected_head,
            policy_path=POLICY_PATH,
            policy_digest=policy.digest,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        return monitor_fixed_head(request, github=self.github)


class TrustedMainStageFacade:
    """Derive the development bundle digest and refresh one owned project stage."""

    def __init__(self, bundle_root: Path) -> None:
        self.bundle_root = Path(bundle_root)

    def transition(
        self,
        project_root: Path,
        production_root: Path,
        *,
        refresh: bool = False,
        packs: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        if not isinstance(refresh, bool):
            raise TaskError("INVALID_STAGE_ACTION")
        if refresh:
            return refresh_project(self.bundle_root, project_root, production_root, packs)
        from gkd_role.project import verify_project
        from gkd_bundle import BundleError, verify_bundle_root

        source = self.bundle_root
        if source.name != "payload" and (source / "payload").is_dir() and (source / "source.toml").is_file():
            source = source / "payload"
        try:
            digest = verify_bundle_root(source)["contentDigest"]
        except BundleError:
            raise TaskError("BUNDLE_CONTENT_MISMATCH") from None
        return verify_project(source, digest, project_root, production_root, packs)

    stage = transition


class TrustedMainOrchestrator:
    """Trusted-main-only high-level operations over canonical task services."""

    def __init__(
        self,
        context: TrustedTaskContext,
        acceptance_adapter: GitHubAdapter | PullRequestLocator | None = None,
        ci_github: GitHubClient | Any | None = None,
        bundle_root: Path | None = None,
    ) -> None:
        self.context = context
        self.acceptance_adapter = acceptance_adapter
        self.ci_github = ci_github
        self.bundle_root = Path(bundle_root) if bundle_root is not None else None

    @classmethod
    def from_current(
        cls,
        bundle_root: Path,
        task_id: str | None = None,
        current_path: Path | None = None,
        runtime: RuntimeStore | None = None,
        acceptance_adapter: GitHubAdapter | PullRequestLocator | None = None,
        ci_github: GitHubClient | Any | None = None,
    ) -> "TrustedMainOrchestrator":
        current = current_path or Path.cwd()
        context = resolve_trusted_task_context(current, bundle_root, task_id, runtime=runtime)
        return cls(context, acceptance_adapter, ci_github, bundle_root)

    def stage_project(
        self,
        project_root: Path | None,
        production_root: Path,
        *,
        refresh: bool = False,
        packs: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        """Validate or refresh a development stage using the bound bundle source."""

        if self.bundle_root is None:
            raise TaskError("BUNDLE_SOURCE_UNAVAILABLE")
        project = project_root or self.context.trusted_main_root
        return TrustedMainStageFacade(self.bundle_root).transition(
            project,
            production_root,
            refresh=refresh,
            packs=packs,
        )

    stage = stage_project

    def _service(self):
        from gkd_task.service import TaskService

        return TaskService(self.context.candidate_root, self.context.task_path, runtime=self.context.runtime)

    def deliver(self) -> dict[str, Any]:
        """Derive all delivery paths and digests from the fixed candidate tree."""

        _trusted_main(self.context)
        service = self._service()
        status = service.status()
        state = service._state()
        claim = state["lifecycle"]["claim"]
        if claim is None or state["lifecycle"]["phase"] != "implementing":
            raise TaskError("INVALID_TRANSITION")
        delivery_path = f"{self.context.task_path}/delivery.md"
        try:
            document_raw = read_tree_file(self.context.candidate_root, status["head"], delivery_path)
        except TaskError:
            raise TaskError("DELIVERY_DOCUMENT_REQUIRED") from None
        document_digest = sha256_bytes(document_raw)
        candidate_digest: str | None = None
        results_path: str | None = None
        evidence_path: str | None = None
        if "executionBundleDigest" in claim:
            try:
                implementation_head = git(
                    self.context.candidate_root,
                    "rev-parse",
                    f"{status['head']}^",
                    code="INVALID_DELIVERY_DOCUMENT",
                ).decode("ascii").strip()
            except UnicodeDecodeError:
                raise TaskError("INVALID_DELIVERY_DOCUMENT") from None
            paths = artifact_paths(self.context.task_path)
            manifest = _fixed_manifest(self.context.candidate_root, implementation_head, paths["manifest"])
            candidate_digest = manifest["candidateOutputBundleDigest"]
            results_path = paths["results"]
            evidence_path = paths["evidence"]
        return service.deliver(
            status["head"],
            status["revision"],
            claim["claimId"],
            candidate_digest,
            delivery_path,
            document_digest,
            results_path,
            evidence_path,
        )

    def render_facts(
        self,
        document: str,
        *,
        review: dict[str, Any] | None = None,
        ci: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Render path-free facts from the current fixed task/artifact tree."""

        _trusted_main(self.context)
        service = self._service()
        state = service._state()
        candidate_head = head(self.context.candidate_root)
        if review is not None:
            try:
                validate_review(review)
            except TaskError:
                raise
            if review["taskId"] != state["taskId"] or review["candidateHead"] != candidate_head:
                raise TaskError("INVALID_REVIEW")
        if ci is not None:
            try:
                validate_terminal_result(ci)
            except TaskError:
                raise
            if (
                ci["repository"] != self.context.repository
                or ci["baseBranch"] != self.context.base_branch
                or ci["headBranch"] != self.context.task_branch
                or ci["expectedHead"] != candidate_head
                or ci["observedHead"] not in {None, candidate_head}
            ):
                raise TaskError("TERMINAL_RESULT_INVALID")
        result_manifest = None
        verifier_results = None
        evidence = None
        requirements_digest = state["documents"]["requirements"]["digest"]
        plan_digest = state["documents"]["plan"]["digest"]
        implementation_digest = state["documents"]["implementation"]["digest"]
        if document in {"delivery", "acceptance"}:
            delivery = state["lifecycle"].get("delivery")
            if delivery is not None:
                implementation_head = delivery["implementationHead"]
                paths = artifact_paths(self.context.task_path)
                if "executionBundleDigest" in state["lifecycle"].get("claim", {}):
                    load_automatic_delivery_artifacts(
                        self.context.candidate_root,
                        implementation_head,
                        state,
                        delivery["candidateOutputBundleDigest"],
                        paths["results"],
                        paths["evidence"],
                    )
                try:
                    result_manifest = json.loads(read_tree_file(self.context.candidate_root, implementation_head, paths["manifest"]))
                    verifier_results = json.loads(read_tree_file(self.context.candidate_root, implementation_head, paths["results"]))
                    evidence = json.loads(read_tree_file(self.context.candidate_root, implementation_head, paths["evidence"]))
                except (TaskError, UnicodeDecodeError, json.JSONDecodeError):
                    if "executionBundleDigest" in state["lifecycle"].get("claim", {}):
                        raise TaskError("INVALID_RESULT_MANIFEST") from None
        return render_machine_facts(
            document,
            state,
            result=result_manifest,
            verifier_results=verifier_results,
            evidence=evidence,
            review=review,
            ci=ci,
            requirements_digest=requirements_digest,
            plan_digest=plan_digest,
            implementation_digest=implementation_digest,
        )

    def monitor_ci(
        self,
        pull_request: int,
        expected_head: str,
        timeout_seconds: int = 3600,
        poll_interval_seconds: int = 60,
    ) -> dict[str, Any]:
        _trusted_main(self.context)
        return TrustedMainCIFacade(self.context.trusted_main_root, self.ci_github).monitor(
            pull_request,
            expected_head,
            timeout_seconds,
            poll_interval_seconds,
        )

    monitor = monitor_ci

    def _adapter(self) -> GitHubAdapter | PullRequestLocator:
        if self.acceptance_adapter is None:
            from gkd_task.acceptance import SubprocessGitHubAdapter

            executable = Path(__file__).resolve().parents[2] / "bin" / "gkd-github-acceptance"
            self.acceptance_adapter = SubprocessGitHubAdapter(executable)
        return self.acceptance_adapter

    def _delivered_facts(self) -> tuple[dict[str, Any], int, str, list[str]]:
        _trusted_main(self.context)
        service = self._service()
        state = service._state()
        delivery = state["lifecycle"]["delivery"]
        if state["lifecycle"]["phase"] != "delivered" or delivery is None:
            raise TaskError("INVALID_TRANSITION")
        candidate_head = head(self.context.candidate_root)
        policy = load_validated_policy(self.context.trusted_main_root, self.context.repository, POLICY_PATH)
        adapter = self._adapter()
        finder = getattr(adapter, "find_open_pull_requests", None)
        if finder is None:
            raise TaskError("PR_DISCOVERY_UNAVAILABLE")
        try:
            pull_requests = finder(self.context.repository, self.context.task_branch)
        except TaskError:
            raise
        except (OSError, TypeError, ValueError, KeyError):
            raise TaskError("PR_DISCOVERY_FAILED") from None
        if not isinstance(pull_requests, list) or len(pull_requests) != 1:
            raise TaskError("PR_NOT_UNIQUE")
        pr_number = pull_requests[0]
        if isinstance(pr_number, dict):
            pr_number = pr_number.get("number")
        if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number < 1:
            raise TaskError("PR_DISCOVERY_FAILED")
        return state, pr_number, candidate_head, list(policy.required_checks)

    def accept(self, review: dict[str, Any], merge: bool = False) -> dict[str, Any]:
        """Accept one independent review; merging requires explicit ``merge=True``."""

        if not isinstance(merge, bool):
            raise TaskError("INVALID_ACCEPT_INTENT")
        validate_review(review)
        state, pr_number, candidate_head, required_checks = self._delivered_facts()
        del state
        return accept_candidate(
            self.context.trusted_main_root,
            self.context.candidate_root,
            self.context.task_path,
            self.context.repository,
            pr_number,
            candidate_head,
            required_checks,
            review,
            self._adapter(),
            "main",
            merge,
            runtime=self.context.runtime,
        )

    def rework(self, review: dict[str, Any]) -> dict[str, Any]:
        """Return one independently rejected delivered candidate to a fresh epoch."""

        validate_review(review)
        state, pr_number, candidate_head, _ = self._delivered_facts()
        del state
        return rework_candidate(
            self.context.trusted_main_root,
            self.context.candidate_root,
            self.context.task_path,
            self.context.repository,
            pr_number,
            candidate_head,
            review,
            self._adapter(),
            "main",
            runtime=self.context.runtime,
        )
