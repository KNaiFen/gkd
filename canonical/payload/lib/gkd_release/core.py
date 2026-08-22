"""Release-candidate records remain side-effect free."""

from __future__ import annotations

import re
from typing import Any

from gkd_task.canonical import digest_object, require_keys, require_sha1, require_sha256
from gkd_task.errors import TaskError


DECISIONS = tuple(f"GKD-{number:03d}" for number in range(1, 17))
LAYERS = {"L0", "L1", "L2", "L3", "L4"}
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
