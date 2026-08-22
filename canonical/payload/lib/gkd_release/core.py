"""Release-candidate records remain side-effect free."""

from __future__ import annotations

import re
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256
from gkd_task.errors import TaskError


DECISIONS = tuple(f"GKD-{number:03d}" for number in range(1, 17))
LAYERS = {"L0", "L1", "L2", "L3", "L4"}
ASSET_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TRACEABILITY_EVIDENCE = {
    "GKD-001": (
        "tests.role_routing.test_routing_waiting.RoutingContracts.test_explicit_automatic_selects_only_gkd_executor_when_every_gate_is_true",
        "tests.role_routing.test_routing_waiting.RoutingContracts.test_each_missing_automatic_gate_returns_one_stable_manual_only_refusal",
        "tests.role_routing.test_mutations.MutationContracts.test_mutation_route_fallback_is_killed",
    ),
    "GKD-002": (
        "tests.task_core.test_planning.PlanningContracts.test_combined_explicit_decision_can_approve_and_authorize",
        "tests.task_core.test_planning.PlanningContracts.test_plan_only_approval_leaves_implementation_unauthorized",
        "tests.task_core.test_mutations.MutationContracts.test_mutation_revision_cas_is_killed",
    ),
    "GKD-003": (
        "tests.role_routing.test_routing_waiting.WaitingContracts.test_healthy_intervals_one_through_eleven_only_allow_immediate_silent_rewait",
        "tests.role_routing.test_routing_waiting.WaitingContracts.test_short_wait_and_early_timeout_are_rejected_not_rounded_up",
        "tests.role_routing.test_mutations.MutationContracts.test_mutation_short_wait_is_killed",
    ),
    "GKD-004": (
        "tests.task_core.test_acceptance.AcceptanceContracts.test_exact_head_acceptance_performs_two_reads_and_one_merge",
        "tests.task_core.test_acceptance.AcceptanceContracts.test_executor_can_never_accept_or_merge",
        "tests.task_core.test_mutations.MutationContracts.test_mutation_merge_head_check_is_killed",
    ),
    "GKD-005": (
        "tests.ci_policy.test_policy.PolicyContracts.test_policy_and_checkout_validate_for_each_supported_remote_form",
        "tests.ci_policy.test_policy.PolicyContracts.test_policy_rejects_unknown_noncanonical_malformed_and_duplicate_values",
        "tests.ci_policy.test_mutations.CiPolicyMutationContracts.test_mutation_repository_binding_is_killed",
    ),
    "GKD-006": (
        "tests.role_routing.test_roles.RoleContracts.test_fixed_role_matrix_is_exact_and_explicit",
        "tests.role_routing.test_roles.RoleContracts.test_model_effort_sandbox_or_runtime_mutation_is_rejected",
        "tests.role_routing.test_mutations.MutationContracts.test_mutation_role_authority_is_killed",
    ),
    "GKD-007": (
        "tests.resource_scanner.test_resources.ResourceContracts.test_zero_and_bounded_artifacts_are_deterministic",
        "tests.resource_scanner.test_resources.ResourceContracts.test_unknown_visibility_and_malformed_policy_fail_closed",
        "tests.resource_scanner.test_mutations.ResourceMutationContracts.test_mutation_scanner_terminal_gate_is_killed",
    ),
    "GKD-008": (
        "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_requires_current_claim_and_clean_candidate",
        "tests.task_core.test_bootstrap_and_packaging.BootstrapNegativeContracts.test_duplicate_branch_or_second_writable_fact_source_is_rejected",
        "tests.task_core.test_mutations.MutationContracts.test_mutation_merge_head_check_is_killed",
    ),
    "GKD-009": (
        "tests.task_core.test_runtime_and_migration.LocatorAndMigrationContracts.test_locator_uses_current_git_root",
        "tests.task_core.test_runtime_and_migration.LocatorAndMigrationContracts.test_locator_multi_result_is_stable_worktree_ambiguous",
        "tests.task_core.test_mutations.MutationContracts.test_mutation_revision_cas_is_killed",
    ),
    "GKD-010": (
        "tests.release_candidate.test_layers.LayeredVerificationContracts.test_l1_property_matrix_emits_distinct_positive_negative_and_mutation_evidence",
        "tests.release_candidate.test_traceability.ReleaseCandidateContracts.test_missing_decision_is_rejected",
        "tests.release_candidate.test_layers.LayeredVerificationContracts.test_critical_l3_and_l4_mutations_are_killed",
    ),
    "GKD-011": (
        "tests.task_core.test_lifecycle.LifecycleContracts.test_claim_consumes_offer_and_capability_once",
        "tests.task_core.test_lifecycle.LifecycleContracts.test_wrong_capability_is_rejected_without_claim_commit",
        "tests.task_core.test_mutations.MutationContracts.test_mutation_revision_cas_is_killed",
    ),
    "GKD-012": (
        "tests.finalization.test_finalization.FinalizationContracts.test_closeout_record_is_canonical_and_uses_at_most_two_prs",
        "tests.finalization.test_finalization.FinalizationContracts.test_closeout_rejects_product_logic_release_side_effects_and_release_bindings",
        "tests.finalization.test_mutations.FinalizationMutationContracts.test_mutation_same_sha_promotion_is_killed",
    ),
    "GKD-013": (
        "tests.resource_scanner.test_scanner.ScannerContracts.test_credential_is_redacted_and_terminal",
        "tests.resource_scanner.test_scanner.ScannerContracts.test_scanner_rejects_unknown_surface_and_oversized_input",
        "tests.resource_scanner.test_mutations.ResourceMutationContracts.test_mutation_scanner_terminal_gate_is_killed",
    ),
    "GKD-014": (
        "tests.role_routing.test_roles.RoleContracts.test_context_manifests_are_minimal_and_explicit_about_omissions",
        "tests.role_routing.test_roles.RoleContracts.test_unknown_role_source_fields_and_conflicting_skill_names_fail_closed",
        "tests.role_routing.test_mutations.MutationContracts.test_mutation_legacy_role_replacement_is_killed",
    ),
    "GKD-015": (
        "tests.review_core.test_core.ReviewCoreContracts.test_partial_approval_resume_and_recovery_preserve_machine_facts",
        "tests.review_core.test_core.ReviewCoreContracts.test_remediation_requires_explicit_partial_approval_and_resume",
        "tests.review_core.test_mutations.ReviewMutationContracts.test_state_unknown_approval_fails_closed",
    ),
    "GKD-016": (
        "tests.foundation.test_governance.GovernanceContracts.test_vision_has_exactly_seven_required_sections",
        "tests.foundation.test_governance.GovernanceContracts.test_decision_index_and_machine_principle_id_are_rejected",
        "tests.foundation.test_governance.GovernanceContracts.test_mutation_missing_vision_section_is_rejected",
    ),
}


def _trace_entry(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TRACEABILITY")
    require_keys(value, {"decisionId", "positive", "negative", "mutation"}, "INVALID_TRACEABILITY")
    if value["decisionId"] not in DECISIONS or not all(isinstance(value[key], list) and len(value[key]) == 1 and isinstance(value[key][0], str) for key in ("positive", "negative")):
        raise TaskError("INVALID_TRACEABILITY")
    if not isinstance(value["mutation"], str):
        raise TaskError("INVALID_TRACEABILITY")
    if (value["positive"][0], value["negative"][0], value["mutation"]) != TRACEABILITY_EVIDENCE[value["decisionId"]]:
        raise TaskError("TRACEABILITY_EVIDENCE_MISMATCH")


def validate_traceability(value: Any) -> None:
    if not isinstance(value, dict):
        raise TaskError("INVALID_TRACEABILITY")
    require_keys(value, {"schemaVersion", "decisions"}, "INVALID_TRACEABILITY")
    if value["schemaVersion"] != 2 or not isinstance(value["decisions"], list):
        raise TaskError("INVALID_TRACEABILITY")
    for entry in value["decisions"]:
        _trace_entry(entry)
    if tuple(entry["decisionId"] for entry in value["decisions"]) != DECISIONS:
        raise TaskError("TRACEABILITY_INCOMPLETE")


def build_release_candidate(value: dict[str, Any]) -> dict[str, Any]:
    require_keys(value, {"version", "sourceSha", "bundleDigest", "evidenceDigest", "traceability", "layers", "sandboxRepository"}, "INVALID_RELEASE_CANDIDATE")
    if value["version"] != "0.1.0" or not isinstance(value["sandboxRepository"], str) or not re.fullmatch(r"github\.com/[A-Za-z0-9_.-]+/gkd-sandbox", value["sandboxRepository"]):
        raise TaskError("INVALID_RELEASE_CANDIDATE")
    require_sha1(value["sourceSha"], "INVALID_RELEASE_CANDIDATE")
    for key in ("bundleDigest", "evidenceDigest"):
        require_sha256(value[key], "INVALID_RELEASE_CANDIDATE")
    validate_traceability(value["traceability"])
    if not isinstance(value["layers"], list) or set(value["layers"]) != LAYERS:
        raise TaskError("RELEASE_LAYERS_INVALID")
    result = dict(value)
    result["provenance"] = {"sourceSha": value["sourceSha"], "bundleDigest": value["bundleDigest"], "evidenceDigest": value["evidenceDigest"], "traceabilityDigest": digest_object(value["traceability"])}
    result["recordDigest"] = digest_object(result)
    return result


def promotion_request(record: dict[str, Any]) -> dict[str, Any]:
    expected = dict(record)
    actual = expected.pop("recordDigest", None)
    if actual != digest_object(expected):
        raise TaskError("RELEASE_RECORD_TAMPERED")
    rebuilt = build_release_candidate({key: record[key] for key in ("version", "sourceSha", "bundleDigest", "evidenceDigest", "traceability", "layers", "sandboxRepository")})
    if rebuilt != record:
        raise TaskError("RELEASE_RECORD_TAMPERED")
    return {"tagName": "v0.1.0", "targetSha": record["sourceSha"], "bundleDigest": record["bundleDigest"], "provenanceDigest": digest_object(record["provenance"])}


def _assets(value: Any, source_sha: str, bundle_digest: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise TaskError("POST_MERGE_ASSETS_INVALID")
    names: list[str] = []
    for asset in value:
        if not isinstance(asset, dict):
            raise TaskError("POST_MERGE_ASSETS_INVALID")
        require_keys(asset, {"name", "sourceSha", "bundleDigest", "sha256"}, "POST_MERGE_ASSETS_INVALID")
        if (
            not isinstance(asset["name"], str)
            or not ASSET_NAME_RE.fullmatch(asset["name"])
            or asset["sourceSha"] != source_sha
            or asset["bundleDigest"] != bundle_digest
        ):
            raise TaskError("POST_MERGE_ASSET_PROVENANCE_MISMATCH")
        require_sha256(asset["sha256"], "POST_MERGE_ASSETS_INVALID")
        names.append(asset["name"])
    if names != sorted(set(names)):
        raise TaskError("POST_MERGE_ASSETS_INVALID")
    return value


def _post_merge_provenance(
    release_record: dict[str, Any],
    l3_record: dict[str, Any],
    l4_request: dict[str, Any],
    l4_observed_check: dict[str, Any],
    assets: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {
        "sourceSha": release_record["sourceSha"],
        "bundleDigest": release_record["bundleDigest"],
        "evidenceDigest": release_record["evidenceDigest"],
        "releaseRecordDigest": release_record["recordDigest"],
        "l3RecordDigest": l3_record["recordDigest"],
        "l4RequestDigest": l4_request["requestDigest"],
        "l4ObservedCheckDigest": l4_observed_check["recordDigest"],
        "assetsDigest": digest_object(assets),
    }
    result["provenanceDigest"] = digest_object(result)
    return result


def build_post_merge_release_record(value: dict[str, Any]) -> dict[str, Any]:
    """Bind trusted-main L3/L4 observations and promotion assets to one merge SHA."""

    require_keys(
        value,
        {
            "releaseCandidate",
            "sourceSha",
            "sandboxRepository",
            "l3ForwardEval",
            "l4CanaryRequest",
            "l4ObservedCheck",
            "assets",
        },
        "POST_MERGE_RELEASE_RECORD_INVALID",
    )
    source_sha = value["sourceSha"]
    require_sha1(source_sha, "POST_MERGE_RELEASE_RECORD_INVALID")
    release_record = value["releaseCandidate"]
    if not isinstance(release_record, dict):
        raise TaskError("POST_MERGE_RELEASE_RECORD_INVALID")
    promotion_request(release_record)
    if release_record["sourceSha"] != source_sha:
        raise TaskError("POST_MERGE_SOURCE_SHA_MISMATCH")
    sandbox_repository = value["sandboxRepository"]
    if not isinstance(sandbox_repository, str) or release_record["sandboxRepository"] != sandbox_repository:
        raise TaskError("POST_MERGE_SANDBOX_MISMATCH")

    from .verification import (
        validate_l3_forward_eval_record,
        validate_post_merge_l4_canary_request,
        validate_post_merge_l4_observed_check,
    )

    l3_record = validate_l3_forward_eval_record(value["l3ForwardEval"], source_sha)
    l4_request = validate_post_merge_l4_canary_request(
        value["l4CanaryRequest"], source_sha, sandbox_repository
    )
    l4_observed_check = validate_post_merge_l4_observed_check(l4_request, value["l4ObservedCheck"])
    assets = _assets(value["assets"], source_sha, release_record["bundleDigest"])
    provenance = _post_merge_provenance(
        release_record, l3_record, l4_request, l4_observed_check, assets
    )
    result = {
        "schemaVersion": 1,
        "releaseCandidate": release_record,
        "finalGate": {
            "sourceSha": source_sha,
            "sandboxRepository": sandbox_repository,
            "l3ForwardEval": l3_record,
            "l4CanaryRequest": l4_request,
            "l4ObservedCheck": l4_observed_check,
        },
        "assets": assets,
        "provenance": provenance,
    }
    result["recordDigest"] = digest_object(result)
    return result


def validate_post_merge_release_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaskError("POST_MERGE_RELEASE_RECORD_INVALID")
    require_keys(
        value,
        {"schemaVersion", "releaseCandidate", "finalGate", "assets", "provenance", "recordDigest"},
        "POST_MERGE_RELEASE_RECORD_INVALID",
    )
    if value["schemaVersion"] != 1 or not isinstance(value["finalGate"], dict):
        raise TaskError("POST_MERGE_RELEASE_RECORD_INVALID")
    require_keys(
        value["finalGate"],
        {"sourceSha", "sandboxRepository", "l3ForwardEval", "l4CanaryRequest", "l4ObservedCheck"},
        "POST_MERGE_RELEASE_RECORD_INVALID",
    )
    unsigned = dict(value)
    actual = unsigned.pop("recordDigest")
    if not isinstance(actual, str) or actual != digest_object(unsigned):
        raise TaskError("POST_MERGE_RELEASE_RECORD_TAMPERED")
    rebuilt = build_post_merge_release_record(
        {
            "releaseCandidate": value["releaseCandidate"],
            "sourceSha": value["finalGate"]["sourceSha"],
            "sandboxRepository": value["finalGate"]["sandboxRepository"],
            "l3ForwardEval": value["finalGate"]["l3ForwardEval"],
            "l4CanaryRequest": value["finalGate"]["l4CanaryRequest"],
            "l4ObservedCheck": value["finalGate"]["l4ObservedCheck"],
            "assets": value["assets"],
        }
    )
    if rebuilt != value:
        raise TaskError("POST_MERGE_PROVENANCE_MISMATCH")
    return value


def post_merge_promotion_request(record: dict[str, Any]) -> dict[str, Any]:
    """Return tag, Release, and prebuilt-asset inputs without issuing a write."""

    validated = validate_post_merge_release_record(record)
    source_sha = validated["finalGate"]["sourceSha"]
    return {
        "tagName": f"v{validated['releaseCandidate']['version']}",
        "targetSha": source_sha,
        "releaseSha": source_sha,
        "assets": validated["assets"],
        "assetsDigest": digest_object(validated["assets"]),
        "provenanceDigest": validated["provenance"]["provenanceDigest"],
    }
