"""Deterministic machine-facts rendering for task documents.

The renderer is deliberately pure: callers provide already validated task and
artifact objects and receive a canonical JSON value or a stable Markdown block.
Paths, capabilities and host/runtime details are never copied into the output.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from gkd_ci.monitor import validate_terminal_result
from gkd_task.acceptance import validate_review
from gkd_task.canonical import (
    canonical_bytes,
    digest_object,
    require_sha1,
    require_sha256,
    require_string,
    sha256_bytes,
)
from gkd_task.errors import TaskError
from gkd_task.model import validate_result_manifest, validate_state


FACTS_SCHEMA_VERSION = 1
FACTS_KIND = "gkd-document-machine-facts"
FACTS_BEGIN = "<!-- gkd-machine-facts:v1 -->"
FACTS_END = "<!-- /gkd-machine-facts -->"
DOCUMENT_KINDS = {"requirements", "plan", "implementation", "delivery", "acceptance"}


def _invalid(code: str = "INVALID_DOCUMENT_FACTS") -> None:
    raise TaskError(code)


def _sha1(value: Any) -> str:
    try:
        return require_sha1(value, "INVALID_DOCUMENT_FACTS")
    except TaskError:
        _invalid()
    raise AssertionError


def _sha256(value: Any) -> str:
    try:
        return require_sha256(value, "INVALID_DOCUMENT_FACTS")
    except TaskError:
        _invalid()
    raise AssertionError


def _safe_string(value: Any) -> str:
    try:
        return require_string(value, "INVALID_DOCUMENT_FACTS")
    except TaskError:
        _invalid()
    raise AssertionError


def _task_facts(task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(task, dict):
        _invalid("INVALID_TASK_STATE")
    try:
        validate_state(task)
    except TaskError:
        _invalid("INVALID_TASK_STATE")
    repository = task["repository"]
    lifecycle = task["lifecycle"]
    result: dict[str, Any] = {
        "taskId": _safe_string(task["taskId"]),
        "repository": _safe_string(repository["identity"]),
        "taskBranch": _safe_string(repository["taskBranch"]),
        "baseSha": _sha1(repository["baseSha"]),
        "revision": task["revision"],
        "epoch": lifecycle["epoch"],
        "phase": lifecycle["phase"],
    }
    claim = lifecycle.get("claim")
    if claim is not None:
        result["claimId"] = _sha256(claim["claimId"])
        result["claimBaseHead"] = _sha1(claim["claimBaseHead"])
    delivery = lifecycle.get("delivery")
    if delivery is not None:
        result["implementationHead"] = _sha1(delivery["implementationHead"])
        result["deliveredAt"] = delivery["deliveredAt"]
    acceptance = lifecycle.get("acceptance")
    if acceptance is not None:
        result["candidateHead"] = _sha1(acceptance["candidateHead"])
        result["acceptedAt"] = acceptance["acceptedAt"]
        result["merged"] = acceptance["merged"]
    return result


def _artifact_facts(
    result: dict[str, Any] | None,
    verifier_results: dict[str, Any] | None,
    evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    if result is None:
        return {}
    if not isinstance(result, dict):
        _invalid("INVALID_RESULT_MANIFEST")
    try:
        validate_result_manifest(result)
    except TaskError:
        _invalid("INVALID_RESULT_MANIFEST")
    facts: dict[str, Any] = {
        "candidateOutputBundleDigest": _sha256(result["candidateOutputBundleDigest"]),
        "verifierResultDigest": _sha256(result["verifierResultDigest"]),
        "evidenceDigest": _sha256(result["evidenceDigest"]),
        "manifestDigest": _sha256(result["manifestDigest"]),
    }
    if result["schemaVersion"] == 2:
        facts.update(
            {
                "lane": _safe_string(result["lane"]),
                "profile": _safe_string(result["profile"]),
                "scopes": list(result["scopes"]),
            }
        )
    if verifier_results is not None:
        if not isinstance(verifier_results, dict):
            _invalid("INVALID_VERIFIER_RESULTS")
        # The delivery artifact validator owns the complete schema.  Facts only
        # retain stable summary fields and the digest is computed from bytes by
        # the trusted caller when available.
        outcome = verifier_results.get("outcome")
        if outcome != "pass" or not isinstance(verifier_results.get("tests"), int):
            _invalid("INVALID_VERIFIER_RESULTS")
        facts["verifierOutcome"] = outcome
        facts["tests"] = verifier_results["tests"]
        if isinstance(verifier_results.get("scopes"), dict):
            facts["scopeTests"] = {
                _safe_string(name): count
                for name, count in sorted(verifier_results["scopes"].items())
                if isinstance(count, int) and not isinstance(count, bool) and count >= 1
            }
            if len(facts["scopeTests"]) != len(verifier_results["scopes"]):
                _invalid("INVALID_VERIFIER_RESULTS")
    if evidence is not None:
        if not isinstance(evidence, dict) or evidence.get("outcome") != "pass":
            _invalid("INVALID_DELIVERY_EVIDENCE")
        for field in ("candidateOutputBundleDigest", "verifierResultDigest", "evidenceDigest"):
            _sha256(evidence.get(field))
        facts["evidenceOutcome"] = evidence["outcome"]
    return facts


def _review_facts(review: dict[str, Any] | None) -> dict[str, Any]:
    if review is None:
        return {}
    try:
        validate_review(review)
    except TaskError:
        _invalid("INVALID_REVIEW")
    return {
        "reviewerRole": review["reviewerRole"],
        "reviewerDigest": _sha256(review["reviewerDigest"]),
        "reviewDigest": _sha256(review["reviewDigest"]),
        "reviewOutcome": review["outcome"],
        "findingCount": len(review["findings"]),
    }


def _ci_facts(ci: dict[str, Any] | None) -> dict[str, Any]:
    if ci is None:
        return {}
    try:
        validate_terminal_result(ci)
    except TaskError:
        _invalid("TERMINAL_RESULT_INVALID")
    return {
        "ciProvider": ci["provider"],
        "ciOutcome": ci["outcome"],
        "ciReason": ci["reason"],
        "ciExpectedHead": _sha1(ci["expectedHead"]) if ci["expectedHead"] is not None else None,
        "ciObservedHead": _sha1(ci["observedHead"]) if ci["observedHead"] is not None else None,
        "ciPullRequest": ci["pullRequest"],
        "ciRequiredChecks": list(ci["requiredChecks"]),
        "ciChecks": [dict(item) for item in ci["checks"]],
        "ciPolicyDigest": _sha256(ci["policyDigest"]) if ci["policyDigest"] is not None else None,
    }


def _planning_facts(
    document: str,
    requirements_digest: str | None,
    plan_digest: str | None,
    implementation_digest: str | None,
) -> dict[str, Any]:
    if document not in {"requirements", "plan", "implementation"}:
        return {}
    facts: dict[str, Any] = {"documentSchemaVersion": 2}
    if requirements_digest is not None:
        facts["requirementsDigest"] = _sha256(requirements_digest)
    if plan_digest is not None:
        facts["planDigest"] = _sha256(plan_digest)
    if implementation_digest is not None:
        facts["implementationDigest"] = _sha256(implementation_digest)
    return facts


def render_machine_facts(
    document: str,
    task: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    verifier_results: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    ci: dict[str, Any] | None = None,
    requirements_digest: str | None = None,
    plan_digest: str | None = None,
    implementation_digest: str | None = None,
) -> dict[str, Any]:
    """Render one canonical, path-free machine-facts object."""

    if document not in DOCUMENT_KINDS:
        _invalid("INVALID_DOCUMENT_KIND")
    value: dict[str, Any] = {
        "schemaVersion": FACTS_SCHEMA_VERSION,
        "kind": FACTS_KIND,
        "document": document,
        "task": _task_facts(task),
    }
    planning = _planning_facts(document, requirements_digest, plan_digest, implementation_digest)
    if planning:
        value["planning"] = planning
    artifacts = _artifact_facts(result, verifier_results, evidence)
    if artifacts:
        value["artifacts"] = artifacts
    review_facts = _review_facts(review)
    if review_facts:
        value["review"] = review_facts
    ci_facts = _ci_facts(ci)
    if ci_facts:
        value["ci"] = ci_facts
    value["factsDigest"] = digest_object(value)
    validate_machine_facts(value)
    return value


def render_delivery_facts(
    task: dict[str, Any],
    result: dict[str, Any],
    verifier_results: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return render_machine_facts(
        "delivery",
        task,
        result=result,
        verifier_results=verifier_results,
        evidence=evidence,
    )


def render_acceptance_facts(
    task: dict[str, Any],
    review: dict[str, Any],
    ci: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    verifier_results: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return render_machine_facts(
        "acceptance",
        task,
        result=result,
        verifier_results=verifier_results,
        evidence=evidence,
        review=review,
        ci=ci,
    )


def render_planning_facts(
    document: str,
    task: dict[str, Any],
    *,
    requirements_digest: str | None = None,
    plan_digest: str | None = None,
    implementation_digest: str | None = None,
) -> dict[str, Any]:
    return render_machine_facts(
        document,
        task,
        requirements_digest=requirements_digest,
        plan_digest=plan_digest,
        implementation_digest=implementation_digest,
    )


def validate_machine_facts(value: dict[str, Any]) -> None:
    """Validate the strict versioned facts schema and self digest."""

    if not isinstance(value, dict) or value.get("schemaVersion") != FACTS_SCHEMA_VERSION:
        _invalid()
    expected = {"schemaVersion", "kind", "document", "task", "factsDigest"}
    allowed_keys = (
        expected,
        expected | {"planning"},
        expected | {"artifacts"},
        expected | {"review"},
        expected | {"ci"},
        expected | {"planning", "artifacts", "review", "ci"},
        expected | {"artifacts", "review", "ci"},
    )
    if not any(set(value) == candidate for candidate in allowed_keys):
        _invalid()
    if value.get("kind") != FACTS_KIND or value.get("document") not in DOCUMENT_KINDS:
        _invalid()
    task = value.get("task")
    if not isinstance(task, dict):
        _invalid()
    required_task = {"taskId", "repository", "taskBranch", "baseSha", "revision", "epoch", "phase"}
    if not required_task.issubset(task) or any(key in task for key in ("candidateRoot", "runtimeRoot", "capabilities", "argv")):
        _invalid()
    for field in ("taskId", "repository", "taskBranch", "phase"):
        _safe_string(task[field])
    _sha1(task["baseSha"])
    if not isinstance(task["revision"], int) or isinstance(task["revision"], bool) or task["revision"] < 0:
        _invalid()
    if not isinstance(task["epoch"], int) or isinstance(task["epoch"], bool) or task["epoch"] < 0:
        _invalid()
    if "claimId" in task:
        _sha256(task["claimId"])
    if "claimBaseHead" in task:
        _sha1(task["claimBaseHead"])
    if "implementationHead" in task:
        _sha1(task["implementationHead"])
    if "candidateHead" in task:
        _sha1(task["candidateHead"])
    for field in ("deliveredAt", "acceptedAt"):
        if field in task and not isinstance(task[field], str):
            _invalid()
    if "merged" in task and not isinstance(task["merged"], bool):
        _invalid()
    if "planning" in value:
        planning = value["planning"]
        if not isinstance(planning, dict) or planning.get("documentSchemaVersion") != 2:
            _invalid("INVALID_DOCUMENT_SCHEMA")
        for field in ("requirementsDigest", "planDigest", "implementationDigest"):
            if field in planning:
                _sha256(planning[field])
    if "artifacts" in value:
        artifacts = value["artifacts"]
        if not isinstance(artifacts, dict):
            _invalid("INVALID_RESULT_MANIFEST")
        for field in ("candidateOutputBundleDigest", "verifierResultDigest", "evidenceDigest", "manifestDigest"):
            if field in artifacts:
                _sha256(artifacts[field])
        if "tests" in artifacts and (not isinstance(artifacts["tests"], int) or artifacts["tests"] < 1):
            _invalid("INVALID_VERIFIER_RESULTS")
        if "scopeTests" in artifacts:
            if not isinstance(artifacts["scopeTests"], dict) or any(
                not isinstance(count, int) or isinstance(count, bool) or count < 1
                for count in artifacts["scopeTests"].values()
            ):
                _invalid("INVALID_VERIFIER_RESULTS")
    if "review" in value:
        review = value["review"]
        if not isinstance(review, dict) or review.get("reviewOutcome") not in {"accepted", "rejected"}:
            _invalid("INVALID_REVIEW")
        _sha256(review["reviewerDigest"])
        _sha256(review["reviewDigest"])
    if "ci" in value:
        ci = value["ci"]
        if not isinstance(ci, dict) or ci.get("ciProvider") != "github":
            _invalid("TERMINAL_RESULT_INVALID")
        if ci.get("ciExpectedHead") is not None:
            _sha1(ci["ciExpectedHead"])
        if ci.get("ciObservedHead") is not None:
            _sha1(ci["ciObservedHead"])
        if ci.get("ciPolicyDigest") is not None:
            _sha256(ci["ciPolicyDigest"])
    unsigned = deepcopy(value)
    actual = unsigned.pop("factsDigest", None)
    if not isinstance(actual, str) or digest_object(unsigned) != actual:
        _invalid("DOCUMENT_FACTS_TAMPERED")


def render_facts_block(facts: dict[str, Any]) -> str:
    validate_machine_facts(facts)
    payload = canonical_bytes(facts).decode("utf-8")
    return f"{FACTS_BEGIN}\n```json\n{payload}```\n{FACTS_END}\n"


def parse_facts_block(raw: bytes | str) -> dict[str, Any] | None:
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    if FACTS_BEGIN not in text and FACTS_END not in text:
        return None
    if text.count(FACTS_BEGIN) != 1 or text.count(FACTS_END) != 1:
        _invalid("INVALID_DOCUMENT_FACTS")
    start = text.index(FACTS_BEGIN)
    end = text.index(FACTS_END)
    if end < start:
        _invalid("INVALID_DOCUMENT_FACTS")
    if text[end + len(FACTS_END) :].strip():
        _invalid("INVALID_DOCUMENT_FACTS")
    block = text[start + len(FACTS_BEGIN) : end]
    if not block.startswith("\n```json\n") or not block.endswith("```\n"):
        _invalid("INVALID_DOCUMENT_FACTS")
    encoded = block[len("\n```json\n") : -len("```\n")]
    try:
        value = json.loads(encoded.encode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _invalid("INVALID_DOCUMENT_FACTS")
    if not isinstance(value, dict) or canonical_bytes(value).decode("utf-8") != encoded:
        _invalid("INVALID_DOCUMENT_FACTS")
    validate_machine_facts(value)
    return value


def strip_facts_block(raw: bytes | str) -> bytes:
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    facts = parse_facts_block(text)
    if facts is None:
        return text.encode("utf-8") if isinstance(raw, bytes) else text.encode("utf-8")
    start = text.index(FACTS_BEGIN)
    prefix = text[:start].rstrip() + "\n"
    return prefix.encode("utf-8")


__all__ = (
    "FACTS_BEGIN",
    "FACTS_END",
    "FACTS_KIND",
    "FACTS_SCHEMA_VERSION",
    "parse_facts_block",
    "render_acceptance_facts",
    "render_delivery_facts",
    "render_facts_block",
    "render_machine_facts",
    "render_planning_facts",
    "strip_facts_block",
    "validate_machine_facts",
)
