"""Deterministic contract-to-test indexes shared by evidence runners."""

from __future__ import annotations

import re


TEST_ID_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*$")
CONTRACT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def build_contract_catalog(declarations: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Validate declarations and return a stable contract-to-full-test-ID index."""

    catalog = {}
    for contract_id, test_ids in declarations.items():
        if not CONTRACT_ID_RE.fullmatch(contract_id) or not test_ids:
            raise ValueError("CONTRACT_CATALOG_INVALID")
        ordered = tuple(sorted(test_ids))
        if len(ordered) != len(set(ordered)) or any(not TEST_ID_RE.fullmatch(test_id) for test_id in ordered):
            raise ValueError("CONTRACT_CATALOG_INVALID")
        catalog[contract_id] = ordered
    return {contract_id: catalog[contract_id] for contract_id in sorted(catalog)}


def test_to_contract_ids(catalog: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Derive the stable reverse index without duplicating execution records."""

    reverse: dict[str, list[str]] = {}
    for contract_id, test_ids in build_contract_catalog(catalog).items():
        for test_id in test_ids:
            reverse.setdefault(test_id, []).append(contract_id)
    return {test_id: tuple(sorted(contract_ids)) for test_id, contract_ids in sorted(reverse.items())}


def validate_contract_coverage(catalog: dict[str, tuple[str, ...]], available_test_ids: set[str]) -> None:
    """Reject evidence generation when a declared contract test is absent."""

    declared = set(test_to_contract_ids(catalog))
    if not declared.issubset(available_test_ids):
        raise ValueError("CONTRACT_CATALOG_TEST_IDS_MISMATCH")


DELIVERY_CONTRACT_TEST_IDS = build_contract_catalog(
    {
        "delivery_document_binding": (
            "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_requires_precommitted_canonical_document_binding",
            "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_document_commit_with_extra_tracked_path",
            "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_path_traversal_before_any_write",
            "tests.task_core.test_lifecycle.LifecycleContracts.test_delivery_rejects_duplicate_document_on_fresh_attempt",
            "tests.task_core.test_acceptance.AcceptanceContracts.test_exact_head_acceptance_performs_two_reads_and_one_merge",
            "tests.task_core.test_acceptance.AcceptanceContracts.test_legacy_delivery_without_document_binding_is_readable_but_not_acceptable",
            "tests.task_core.test_acceptance.AcceptanceContracts.test_post_delivery_document_commit_is_not_a_fixed_candidate",
            "tests.task_core.test_mutations.MutationContracts.test_mutation_delivery_document_digest_check_is_killed",
            "tests.task_core.test_mutations.MutationContracts.test_mutation_delivery_document_commit_paths_check_is_killed",
        ),
    }
)


WATCHDOG_CONTRACT_TEST_IDS = build_contract_catalog(
    {
        "runtime_evidence_binding": (
            "tests.watchdog.test_model.WatchRequestTests.test_rejects_well_formed_but_unapproved_runtime_digest",
            "tests.watchdog.test_mcp.McpAdapterTests.test_unapproved_runtime_digest_never_constructs_watch_service",
            "tests.watchdog.test_model.WatchRequestTests.test_direct_request_construction_cannot_bypass_identity_invariants",
        ),
        "thread_ownership_binding": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_thread_ownership_mismatch_fails_before_control",
            "tests.watchdog.test_watcher.WatchServiceTests.test_thread_ownership_drift_blocks_interrupt_and_steer",
            "tests.watchdog.test_watcher.WatchServiceTests.test_parent_read_remote_failure_is_protocol_not_child_abnormal",
        ),
        "interrupt_confirmation": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_system_error_interrupts_child_then_steers_bound_parent",
            "tests.watchdog.test_watcher.WatchServiceTests.test_interrupt_without_bound_terminal_confirmation_never_steers",
        ),
        "steer_error_classification": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_wrong_expected_turn_is_rejected_once_without_fallback",
            "tests.watchdog.test_watcher.WatchServiceTests.test_non_expected_steer_errors_remain_protocol_errors",
        ),
        "cancellation_and_eof_shutdown": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_cancellation_interrupt_failure_is_terminal_protocol_error",
            "tests.watchdog.test_watcher.WatchServiceTests.test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed",
            "tests.watchdog.test_mcp.McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
        ),
        "credential_identity_rejection": (
            "tests.watchdog.test_model.WatchRequestTests.test_rejects_credential_shaped_values_in_every_echoed_id",
        ),
        "deadline_single_terminal": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_twelve_hour_deadline_is_single_and_hourly_ticks_are_silent",
        ),
        "normal_terminal_no_steer": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_normal_terminal_returns_immediately_without_steer",
        ),
        "active_stale_is_healthy": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_stale_active_child_remains_healthy_across_ticks",
        ),
        "abnormal_classification_and_order": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_system_error_interrupts_child_then_steers_bound_parent",
            "tests.watchdog.test_watcher.WatchServiceTests.test_failed_terminal_steers_without_interrupting_terminal_child",
            "tests.watchdog.test_watcher.WatchServiceTests.test_explicit_remote_errored_is_abnormal",
            "tests.watchdog.test_watcher.WatchServiceTests.test_not_found_is_abnormal_and_does_not_interrupt_parent",
        ),
        "expected_turn_cas": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_wrong_expected_turn_is_rejected_once_without_fallback",
            "tests.watchdog.test_app_server.AppServerClientTests.test_actual_expected_turn_rejection_is_single_and_redacted",
        ),
        "bounded_protocol_failures": (
            "tests.watchdog.test_app_server.AppServerClientTests.test_eof_malformed_unknown_and_duplicate_responses_terminate",
            "tests.watchdog.test_app_server.AppServerClientTests.test_response_timeout_is_bounded",
            "tests.watchdog.test_app_server.AppServerClientTests.test_start_failure_maps_to_terminal_orchestrator_error",
            "tests.watchdog.test_mcp.McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
        ),
        "pre_side_effect_validation": (
            "tests.watchdog.test_model.WatchRequestTests.test_rejects_unknown_fields_before_side_effects",
            "tests.watchdog.test_model.WatchRequestTests.test_rejects_wrong_types_limits_and_digest",
            "tests.watchdog.test_mcp.McpAdapterTests.test_unapproved_runtime_digest_never_constructs_watch_service",
            "tests.watchdog.test_app_server.AppServerClientTests.test_schema_drift_stops_before_app_server_spawn",
        ),
        "cancellation_scope": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_cancellation_interrupts_only_bound_child_and_never_parent",
            "tests.watchdog.test_watcher.WatchServiceTests.test_cancellation_interrupt_failure_is_terminal_protocol_error",
            "tests.watchdog.test_watcher.WatchServiceTests.test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed",
            "tests.watchdog.test_mcp.McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
        ),
        "concurrency_and_single_writer": (
            "tests.watchdog.test_watcher.WatchServiceTests.test_two_concurrent_instances_keep_identity_and_calls_separate",
            "tests.watchdog.test_app_server.AppServerClientTests.test_two_subprocess_clients_keep_rpc_ids_and_identity_isolated",
            "tests.watchdog.test_app_server.AppServerClientTests.test_single_client_serializes_concurrent_writers_and_ids",
            "tests.watchdog.test_mcp.McpAdapterTests.test_active_watch_capacity_is_bounded_before_service_construction",
        ),
        "mcp_framing_and_silence": (
            "tests.watchdog.test_mcp.McpAdapterTests.test_initialize_negotiates_each_registered_protocol_version",
            "tests.watchdog.test_mcp.McpAdapterTests.test_initialize_unknown_protocol_returns_stable_unsupported_error",
            "tests.watchdog.test_mcp.McpAdapterTests.test_subprocess_initialize_list_call_and_success_framing",
            "tests.watchdog.test_mcp.McpAdapterTests.test_subprocess_invalid_request_uses_jsonrpc_error_without_side_effect",
            "tests.watchdog.test_mcp.McpAdapterTests.test_health_ticks_emit_no_progress_result_or_log_before_cancel",
            "tests.watchdog.test_mcp.McpAdapterTests.test_malformed_mcp_json_uses_parse_error_frame",
            "tests.watchdog.test_mcp.McpAdapterTests.test_stdin_eof_force_closes_hanging_app_server_and_worker",
        ),
        "sensitive_data_containment": (
            "tests.watchdog.test_app_server.AppServerClientTests.test_actual_subprocess_normal_terminal_drops_body_from_transcript",
            "tests.watchdog.test_app_server.AppServerClientTests.test_untrusted_notification_method_and_keys_are_redacted_in_transcript",
            "tests.watchdog.test_model.WatchRequestTests.test_rejects_credential_shaped_values_in_every_echoed_id",
        ),
    }
)


APP_SERVER_INITIALIZE_CONTRACT_TEST_IDS = build_contract_catalog(
    {
        "initialize_response_shape": (
            "tests.watchdog.test_runtime_compat.RuntimeCompatibilityTests.test_initialize_response_requires_current_schema_metadata",
            "tests.watchdog.test_app_server.AppServerClientTests.test_factory_retains_only_normalized_initialize_facts",
        ),
        "initialize_capability_boundary": (
            "tests.watchdog.test_runtime_compat.RuntimeCompatibilityTests.test_initialize_capability_type_drift_is_unsupported",
            "tests.watchdog.test_runtime_compat.RuntimeCompatibilityTests.test_legacy_capability_fixture_remains_compatibility_only",
        ),
    }
)


FOUNDATION_CONTRACT_TEST_IDS = build_contract_catalog(
    {
        "manifest_lock_and_digest": (
            "tests.foundation.test_manifest.ManifestContracts.test_schema_manifest_lock_and_canonical_sort_are_valid",
            "tests.foundation.test_manifest.ManifestContracts.test_repeated_generation_is_byte_identical",
            "tests.foundation.test_manifest.ManifestContracts.test_mutation_content_tamper_without_digest_update_is_rejected",
            "tests.foundation.test_manifest.ManifestContracts.test_metadata_mode_mutations_are_rejected_before_generation",
        ),
        "source_inventory_and_paths": (
            "tests.foundation.test_manifest.ManifestContracts.test_unknown_payload_file_is_rejected",
            "tests.foundation.test_manifest.ManifestContracts.test_missing_payload_file_is_rejected",
            "tests.foundation.test_manifest.ManifestContracts.test_source_path_traversal_is_rejected",
            "tests.foundation.test_manifest.ManifestContracts.test_machine_specific_source_content_is_rejected",
            "tests.foundation.test_manifest.ManifestContracts.test_bare_usernames_and_unrelated_aio_substrings_are_portable",
            "tests.foundation.test_manifest.ManifestContracts.test_project_specific_install_target_is_deferred_to_repository_scan",
        ),
        "temporary_installation_and_drift": (
            "tests.foundation.test_install.InstallationContracts.test_two_clean_installs_match_and_repeat_is_idempotent",
            "tests.foundation.test_install.InstallationContracts.test_cli_has_no_default_target_or_temporary_root",
            "tests.foundation.test_install.InstallationContracts.test_verify_detects_content_drift",
            "tests.foundation.test_install.InstallationContracts.test_verify_detects_missing_file",
            "tests.foundation.test_install.InstallationContracts.test_verify_detects_extra_file",
            "tests.foundation.test_install.InstallationContracts.test_verify_detects_mode_drift",
            "tests.foundation.test_install.InstallationContracts.test_verify_detects_symlink_drift",
        ),
        "vision_and_documentation": (
            "tests.foundation.test_governance.GovernanceContracts.test_vision_has_exactly_seven_required_sections",
            "tests.foundation.test_governance.GovernanceContracts.test_mutation_missing_vision_section_is_rejected",
            "tests.foundation.test_governance.GovernanceContracts.test_readme_and_agents_must_link_without_copying_vision",
            "tests.foundation.test_governance.GovernanceContracts.test_document_layering_and_templates_are_complete",
            "tests.foundation.test_governance.GovernanceContracts.test_alignment_template_is_generated_and_cannot_expand_authorization",
        ),
        "deterministic_evidence": (
            "tests.foundation.test_evidence.EvidenceContracts.test_two_clean_evidence_generations_are_byte_identical",
            "tests.foundation.test_evidence.EvidenceContracts.test_evidence_digest_is_canonical_and_self_excluding",
            "tests.foundation.test_evidence.EvidenceContracts.test_evidence_contains_no_temporary_or_machine_path",
            "tests.foundation.test_evidence.EvidenceContracts.test_output_inside_protected_root_fails_without_writing",
            "tests.foundation.test_evidence.EvidenceContracts.test_cleanup_failure_cannot_publish_ready_evidence",
            "tests.foundation.test_evidence.EvidenceContracts.test_final_snapshot_occurs_only_after_install_cleanup",
            "tests.foundation.test_evidence.EvidenceContracts.test_project_specific_path_fails_at_evidence_boundary",
        ),
    }
)
