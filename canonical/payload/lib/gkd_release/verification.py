"""Deterministic release-verification contracts with no GitHub write surface."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any

from gkd_ci.github import GitHubClient
from gkd_task.canonical import (
    canonical_bytes,
    digest_object,
    require_keys,
    require_sha1,
    require_sha256,
)
from gkd_task.errors import TaskError

from .core import DECISIONS, validate_traceability


CANARY_CHECK = "GKD Canary"
CANARY_MARKER_PATH = "canary.json"
SANDBOX_REPOSITORY_RE = re.compile(r"github\.com/[A-Za-z0-9_.-]+/gkd-sandbox")
L3_EVALUATION_KIND = "trusted-main-post-merge-release-gate"
L3_EFFECT_BOUNDARY = {
    "pullRequestWrite": False,
    "sourceMutation": False,
    "taskLifecycleWrite": False,
}


def _is_sha256(value: Any) -> bool:
    try:
        require_sha256(value, "INVALID_RELEASE_VERIFICATION")
    except TaskError:
        return False
    return True


def _release_fixture(traceability: dict[str, Any], version: str) -> dict[str, Any]:
    return {
        "version": version,
        "sourceSha": "a" * 40,
        "bundleDigest": "b" * 64,
        "evidenceDigest": "c" * 64,
        "traceability": traceability,
        "layers": ["L0", "L1", "L2", "L3", "L4"],
        "sandboxRepository": "github.com/example/gkd-sandbox",
    }


def _expect_traceability_failure(value: dict[str, Any]) -> None:
    try:
        validate_traceability(value)
    except TaskError:
        return
    raise TaskError("L1_PROPERTY_NOT_KILLED")


def run_l1_properties(traceability: dict[str, Any]) -> dict[str, Any]:
    """Execute property counterexamples for every approved decision entry."""

    validate_traceability(traceability)
    from .core import build_release_candidate, promotion_request

    for version in ("0.1.1", "0.1.2", "0.1.3", "0.1.4"):
        promotion = promotion_request(build_release_candidate(_release_fixture(traceability, version)))
        if promotion["targetSha"] != "a" * 40 or promotion["tagName"] != f"v{version}":
            raise TaskError("L1_PROPERTY_FAILED")

    results = []
    for index, decision in enumerate(DECISIONS):
        entry = traceability["decisions"][index]
        if entry["decisionId"] != decision:
            raise TaskError("L1_PROPERTY_FAILED")
        negative = deepcopy(traceability)
        negative["decisions"][index]["negative"] = ["unbound-negative"]
        _expect_traceability_failure(negative)
        mutation = deepcopy(traceability)
        mutation["decisions"][index]["mutation"] = "unbound-mutation"
        _expect_traceability_failure(mutation)
        results.append(
            {
                "decisionId": decision,
                "positive": "pass",
                "negative": "pass",
                "mutation": "pass",
            }
        )
    evidence = {"layer": "L1", "properties": results, "schemaVersion": 1}
    return {**evidence, "evidenceDigest": digest_object(evidence)}


def validate_l2_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L2_REQUEST_INVALID")
    require_keys(
        value,
        {"baseBranch", "expectedHead", "pullRequest", "repository", "requiredCheck", "schemaVersion"},
        "L2_REQUEST_INVALID",
    )
    if (
        value["schemaVersion"] != 1
        or not isinstance(value["repository"], str)
        or not SANDBOX_REPOSITORY_RE.fullmatch(value["repository"])
        or value["baseBranch"] != "main"
        or value["requiredCheck"] != CANARY_CHECK
        or isinstance(value["pullRequest"], bool)
        or not isinstance(value["pullRequest"], int)
        or value["pullRequest"] < 1
    ):
        raise TaskError("L2_REQUEST_INVALID")
    require_sha1(value["expectedHead"], "L2_REQUEST_INVALID")
    return value


def run_l2_probe(value: Any, github: GitHubClient | None = None) -> dict[str, Any]:
    request = validate_l2_request(value)
    observation = (github or GitHubClient()).observe(
        request["repository"],
        request["pullRequest"],
        request["expectedHead"],
        (request["requiredCheck"],),
    )
    if (
        observation.repository != request["repository"]
        or observation.base_branch != request["baseBranch"]
        or observation.head_sha != request["expectedHead"]
        or observation.state != "open"
        or observation.checks != ((CANARY_CHECK, "success"),)
    ):
        raise TaskError("L2_CANARY_OBSERVATION_INVALID")
    evidence = {
        "expectedHead": request["expectedHead"],
        "layer": "L2",
        "outcome": "pass",
        "pullRequest": request["pullRequest"],
        "repository": request["repository"],
        "schemaVersion": 1,
    }
    return {**evidence, "evidenceDigest": digest_object(evidence)}


def _l3_evaluation(release_record: dict[str, Any]) -> dict[str, Any]:
    from .core import promotion_request

    promotion_request(release_record)
    return {
        "effectBoundary": L3_EFFECT_BOUNDARY,
        "evaluationKind": L3_EVALUATION_KIND,
        "releaseCandidateDigest": release_record["recordDigest"],
        "releaseSourceSha": release_record["sourceSha"],
        "schemaVersion": 3,
        "traceabilityDigest": release_record["provenance"]["traceabilityDigest"],
    }


def validate_l3_trusted_main_evaluation(
    value: Any, release_record: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L3_TRUSTED_MAIN_EVALUATION_INVALID")
    require_keys(
        value,
        {
            "effectBoundary",
            "evaluationKind",
            "releaseCandidateDigest",
            "releaseSourceSha",
            "schemaVersion",
            "traceabilityDigest",
        },
        "L3_TRUSTED_MAIN_EVALUATION_INVALID",
    )
    if (
        value["schemaVersion"] != 3
        or value["evaluationKind"] != L3_EVALUATION_KIND
        or value["effectBoundary"] != L3_EFFECT_BOUNDARY
    ):
        raise TaskError("L3_TRUSTED_MAIN_EVALUATION_INVALID")
    require_sha1(value["releaseSourceSha"], "L3_TRUSTED_MAIN_EVALUATION_INVALID")
    for key in ("releaseCandidateDigest", "traceabilityDigest"):
        require_sha256(value[key], "L3_TRUSTED_MAIN_EVALUATION_INVALID")
    if release_record is not None:
        expected = _l3_evaluation(release_record)
        if value["releaseSourceSha"] != expected["releaseSourceSha"]:
            raise TaskError("L3_SOURCE_SHA_MISMATCH")
        if value["releaseCandidateDigest"] != expected["releaseCandidateDigest"]:
            raise TaskError("L3_CANDIDATE_MISMATCH")
        if value["traceabilityDigest"] != expected["traceabilityDigest"]:
            raise TaskError("L3_TRACEABILITY_MISMATCH")
        if value != expected:
            raise TaskError("L3_TRUSTED_MAIN_EVALUATION_INVALID")
    return value


def build_l3_trusted_main_record(release_record: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize trusted-main's observable, read-only post-merge inputs."""

    evaluation = _l3_evaluation(release_record)
    record = {
        "schemaVersion": 3,
        "releaseSourceSha": evaluation["releaseSourceSha"],
        "evaluation": evaluation,
        "evaluationDigest": digest_object(evaluation),
    }
    record["recordDigest"] = digest_object(record)
    return record


def validate_l3_trusted_main_record(
    value: Any, release_record: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L3_TRUSTED_MAIN_RECORD_INVALID")
    require_keys(
        value,
        {
            "schemaVersion",
            "releaseSourceSha",
            "evaluation",
            "evaluationDigest",
            "recordDigest",
        },
        "L3_TRUSTED_MAIN_RECORD_INVALID",
    )
    if value["schemaVersion"] != 3:
        raise TaskError("L3_TRUSTED_MAIN_RECORD_INVALID")
    require_sha1(value["releaseSourceSha"], "L3_TRUSTED_MAIN_RECORD_INVALID")
    evaluation = validate_l3_trusted_main_evaluation(value["evaluation"], release_record)
    if value["releaseSourceSha"] != evaluation["releaseSourceSha"]:
        raise TaskError("L3_SOURCE_SHA_MISMATCH")
    if value["evaluationDigest"] != digest_object(evaluation):
        raise TaskError("L3_TRUSTED_MAIN_RECORD_TAMPERED")
    unsigned = dict(value)
    actual = unsigned.pop("recordDigest")
    if actual != digest_object(unsigned):
        raise TaskError("L3_TRUSTED_MAIN_RECORD_TAMPERED")
    return value


def build_l4_canary_request(
    record: dict[str, Any], sandbox_head_sha: str
) -> dict[str, Any]:
    from .core import promotion_request

    if not isinstance(record, dict):
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    promotion = promotion_request(record)
    if not SANDBOX_REPOSITORY_RE.fullmatch(record["sandboxRepository"]):
        raise TaskError("L4_SANDBOX_INVALID")
    require_sha1(sandbox_head_sha, "L4_CANARY_REQUEST_INVALID")
    request = {
        "branch": f"gkd-canary/{record['sourceSha'][:12]}",
        "bundleDigest": record["bundleDigest"],
        "markerPath": CANARY_MARKER_PATH,
        "operation": "sandbox-canary",
        "repository": record["sandboxRepository"],
        "releaseSourceSha": promotion["targetSha"],
        "requiredCheck": CANARY_CHECK,
        "sandboxHeadSha": sandbox_head_sha,
        "schemaVersion": 2,
    }
    return {**request, "requestDigest": digest_object(request)}


def validate_l4_canary_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    require_keys(
        value,
        {
            "branch",
            "bundleDigest",
            "markerPath",
            "operation",
            "repository",
            "releaseSourceSha",
            "requestDigest",
            "requiredCheck",
            "sandboxHeadSha",
            "schemaVersion",
        },
        "L4_CANARY_REQUEST_INVALID",
    )
    request = dict(value)
    actual = request.pop("requestDigest")
    if actual != digest_object(request):
        raise TaskError("L4_CANARY_REQUEST_TAMPERED")
    if (
        request["schemaVersion"] != 2
        or request["operation"] != "sandbox-canary"
        or not isinstance(request["repository"], str)
        or not SANDBOX_REPOSITORY_RE.fullmatch(request["repository"])
        or request["markerPath"] != CANARY_MARKER_PATH
        or request["requiredCheck"] != CANARY_CHECK
    ):
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    require_sha1(request["releaseSourceSha"], "L4_CANARY_REQUEST_INVALID")
    require_sha1(request["sandboxHeadSha"], "L4_CANARY_REQUEST_INVALID")
    require_sha256(request["bundleDigest"], "L4_CANARY_REQUEST_INVALID")
    if request["branch"] != f"gkd-canary/{request['releaseSourceSha'][:12]}":
        raise TaskError("L4_CANARY_REQUEST_INVALID")
    return value


def build_post_merge_l4_canary_request(
    record: dict[str, Any],
    expected_source_sha: str,
    sandbox_repository: str,
    expected_sandbox_head_sha: str,
) -> dict[str, Any]:
    """Derive the one sandbox-only L4 request from the immutable merge SHA."""

    request = build_l4_canary_request(record, expected_sandbox_head_sha)
    return validate_post_merge_l4_canary_request(
        request, expected_source_sha, sandbox_repository, expected_sandbox_head_sha
    )


def validate_post_merge_l4_canary_request(
    value: Any,
    expected_source_sha: str,
    sandbox_repository: str,
    expected_sandbox_head_sha: str,
) -> dict[str, Any]:
    request = validate_l4_canary_request(value)
    require_sha1(expected_source_sha, "L4_CANARY_REQUEST_INVALID")
    require_sha1(expected_sandbox_head_sha, "L4_CANARY_REQUEST_INVALID")
    if request["releaseSourceSha"] != expected_source_sha:
        raise TaskError("L4_SOURCE_SHA_MISMATCH")
    if request["repository"] != sandbox_repository:
        raise TaskError("L4_SANDBOX_MISMATCH")
    if request["sandboxHeadSha"] != expected_sandbox_head_sha:
        raise TaskError("L4_SANDBOX_HEAD_SHA_MISMATCH")
    return request


def validate_canary_marker(
    value: Any, expected_release_source_sha: str, expected_bundle_digest: str
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_MARKER_INVALID")
    require_keys(
        value,
        {"bundleDigest", "releaseSourceSha", "schemaVersion"},
        "L4_CANARY_MARKER_INVALID",
    )
    if value["schemaVersion"] != 1:
        raise TaskError("L4_CANARY_MARKER_INVALID")
    require_sha1(value["releaseSourceSha"], "L4_CANARY_MARKER_INVALID")
    require_sha256(value["bundleDigest"], "L4_CANARY_MARKER_INVALID")
    if value["releaseSourceSha"] != expected_release_source_sha:
        raise TaskError("L4_MARKER_SOURCE_SHA_MISMATCH")
    if value["bundleDigest"] != expected_bundle_digest:
        raise TaskError("L4_MARKER_BUNDLE_DIGEST_MISMATCH")
    return value


def _canonical_canary_marker(
    raw: bytes, expected_release_source_sha: str, expected_bundle_digest: str
) -> dict[str, Any]:
    try:
        marker = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("L4_CANARY_MARKER_INVALID") from None
    if not isinstance(marker, dict) or raw != canonical_bytes(marker):
        raise TaskError("L4_CANARY_MARKER_INVALID")
    return validate_canary_marker(
        marker, expected_release_source_sha, expected_bundle_digest
    )


def observe_post_merge_l4_canary(
    request: dict[str, Any],
    pull_request: int,
    github: GitHubClient | None = None,
) -> dict[str, Any]:
    """Read a fixed sandbox head, marker, and check without GitHub writes."""

    validated_request = validate_l4_canary_request(request)
    if isinstance(pull_request, bool) or not isinstance(pull_request, int) or pull_request < 1:
        raise TaskError("L4_CANARY_OBSERVATION_INVALID")
    client = github or GitHubClient()
    observation = client.observe(
        validated_request["repository"],
        pull_request,
        validated_request["sandboxHeadSha"],
        (CANARY_CHECK,),
    )
    if (
        observation.repository != validated_request["repository"]
        or observation.head_sha != validated_request["sandboxHeadSha"]
        or observation.head_branch != validated_request["branch"]
        or observation.state != "open"
        or observation.checks != ((CANARY_CHECK, "success"),)
    ):
        raise TaskError("L4_CANARY_OBSERVATION_INVALID")
    marker = _canonical_canary_marker(
        client.read_file(
            validated_request["repository"],
            validated_request["markerPath"],
            validated_request["sandboxHeadSha"],
        ),
        validated_request["releaseSourceSha"],
        validated_request["bundleDigest"],
    )
    result = {
        "branch": observation.head_branch,
        "canaryMarker": marker,
        "markerDigest": digest_object(marker),
        "markerPath": validated_request["markerPath"],
        "outcome": "success",
        "pullRequest": observation.pull_request,
        "releaseSourceSha": validated_request["releaseSourceSha"],
        "repository": observation.repository,
        "requiredCheck": CANARY_CHECK,
        "requestDigest": validated_request["requestDigest"],
        "sandboxHeadSha": validated_request["sandboxHeadSha"],
        "schemaVersion": 2,
    }
    result["recordDigest"] = digest_object(result)
    return result


def validate_post_merge_l4_observed_check(
    request: dict[str, Any], value: Any
) -> dict[str, Any]:
    request = validate_l4_canary_request(request)
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_OBSERVATION_INVALID")
    require_keys(
        value,
        {
            "branch",
            "canaryMarker",
            "markerDigest",
            "markerPath",
            "outcome",
            "pullRequest",
            "releaseSourceSha",
            "repository",
            "requiredCheck",
            "requestDigest",
            "sandboxHeadSha",
            "schemaVersion",
            "recordDigest",
        },
        "L4_CANARY_OBSERVATION_INVALID",
    )
    if (
        value["schemaVersion"] != 2
        or value["releaseSourceSha"] != request["releaseSourceSha"]
        or value["repository"] != request["repository"]
        or value["branch"] != request["branch"]
        or value["markerPath"] != request["markerPath"]
        or value["sandboxHeadSha"] != request["sandboxHeadSha"]
        or value["requiredCheck"] != CANARY_CHECK
        or value["outcome"] != "success"
        or value["requestDigest"] != request["requestDigest"]
        or isinstance(value["pullRequest"], bool)
        or not isinstance(value["pullRequest"], int)
        or value["pullRequest"] < 1
    ):
        raise TaskError("L4_CANARY_OBSERVATION_INVALID")
    require_sha1(value["sandboxHeadSha"], "L4_CANARY_OBSERVATION_INVALID")
    marker = validate_canary_marker(
        value["canaryMarker"], request["releaseSourceSha"], request["bundleDigest"]
    )
    if value["markerDigest"] != digest_object(marker):
        raise TaskError("L4_CANARY_OBSERVATION_TAMPERED")
    unsigned = dict(value)
    actual = unsigned.pop("recordDigest")
    if actual != digest_object(unsigned):
        raise TaskError("L4_CANARY_OBSERVATION_TAMPERED")
    return value


class TrustedMainFinalGate:
    """Trusted-main boundary for one post-merge gate; it never writes GitHub state."""

    def __init__(
        self, source_sha: str, sandbox_repository: str, sandbox_head_sha: str
    ) -> None:
        require_sha1(source_sha, "POST_MERGE_GATE_INVALID")
        require_sha1(sandbox_head_sha, "POST_MERGE_GATE_INVALID")
        if not isinstance(sandbox_repository, str) or not SANDBOX_REPOSITORY_RE.fullmatch(sandbox_repository):
            raise TaskError("POST_MERGE_GATE_INVALID")
        self.source_sha = source_sha
        self.sandbox_repository = sandbox_repository
        self.sandbox_head_sha = sandbox_head_sha

    def l3_trusted_main_evaluation(self, release_record: dict[str, Any]) -> dict[str, Any]:
        record = build_l3_trusted_main_record(release_record)
        if record["releaseSourceSha"] != self.source_sha:
            raise TaskError("L3_SOURCE_SHA_MISMATCH")
        return validate_l3_trusted_main_record(record, release_record)

    def l4_canary_request(self, release_record: dict[str, Any]) -> dict[str, Any]:
        return build_post_merge_l4_canary_request(
            release_record,
            self.source_sha,
            self.sandbox_repository,
            self.sandbox_head_sha,
        )

    def observe_l4_canary(
        self,
        request: dict[str, Any],
        pull_request: int,
        github: GitHubClient | None = None,
    ) -> dict[str, Any]:
        request = validate_post_merge_l4_canary_request(
            request,
            self.source_sha,
            self.sandbox_repository,
            self.sandbox_head_sha,
        )
        observed = observe_post_merge_l4_canary(request, pull_request, github)
        return validate_post_merge_l4_observed_check(request, observed)

    def release_record(
        self,
        release_candidate: dict[str, Any],
        l3_trusted_main_evaluation: dict[str, Any],
        l4_canary_request: dict[str, Any],
        l4_observed_check: dict[str, Any],
        assets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        from .core import build_post_merge_release_record

        return build_post_merge_release_record(
            {
                "releaseCandidate": release_candidate,
                "releaseSourceSha": self.source_sha,
                "sandboxHeadSha": self.sandbox_head_sha,
                "sandboxRepository": self.sandbox_repository,
                "l3TrustedMainEvaluation": l3_trusted_main_evaluation,
                "l4CanaryRequest": l4_canary_request,
                "l4ObservedCheck": l4_observed_check,
                "assets": assets,
            }
        )


def validate_l4_canary_result(request: dict[str, Any], value: Any) -> dict[str, Any]:
    validate_l4_canary_request(request)
    if not isinstance(value, dict):
        raise TaskError("L4_CANARY_RESULT_INVALID")
    require_keys(
        value,
        {
            "branch",
            "eventDigest",
            "outcome",
            "pullRequest",
            "releaseSourceSha",
            "repository",
            "requestDigest",
            "schemaVersion",
        },
        "L4_CANARY_RESULT_INVALID",
    )
    if (
        value["schemaVersion"] != 1
        or value["repository"] != request["repository"]
        or value["branch"] != request["branch"]
        or value["releaseSourceSha"] != request["releaseSourceSha"]
        or value["requestDigest"] != request["requestDigest"]
        or value["outcome"] not in {"failure", "success"}
        or isinstance(value["pullRequest"], bool)
        or not isinstance(value["pullRequest"], int)
        or value["pullRequest"] < 1
        or not _is_sha256(value["eventDigest"])
    ):
        raise TaskError("L4_CANARY_RESULT_INVALID")
    return value
