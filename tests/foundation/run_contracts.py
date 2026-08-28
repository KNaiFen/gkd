#!/usr/bin/env python3
"""Run canonical foundation contracts and write deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

from gkd_task.results import CanonicalResultError, canonical_bytes, load_canonical_results


CONTRACT_SUFFIXES = {
    "manifest_lock_and_digest": (
        "ManifestContracts.test_schema_manifest_lock_and_canonical_sort_are_valid",
        "ManifestContracts.test_repeated_generation_is_byte_identical",
        "ManifestContracts.test_mutation_content_tamper_without_digest_update_is_rejected",
        "ManifestContracts.test_metadata_mode_mutations_are_rejected_before_generation",
    ),
    "source_inventory_and_paths": (
        "ManifestContracts.test_unknown_payload_file_is_rejected",
        "ManifestContracts.test_missing_payload_file_is_rejected",
        "ManifestContracts.test_source_path_traversal_is_rejected",
        "ManifestContracts.test_machine_specific_source_content_is_rejected",
        "ManifestContracts.test_bare_usernames_and_unrelated_aio_substrings_are_portable",
        "ManifestContracts.test_project_specific_install_target_is_deferred_to_repository_scan",
    ),
    "temporary_installation_and_drift": (
        "InstallationContracts.test_two_clean_installs_match_and_repeat_is_idempotent",
        "InstallationContracts.test_cli_has_no_default_target_or_temporary_root",
        "InstallationContracts.test_verify_detects_content_drift",
        "InstallationContracts.test_verify_detects_missing_file",
        "InstallationContracts.test_verify_detects_extra_file",
        "InstallationContracts.test_verify_detects_mode_drift",
        "InstallationContracts.test_verify_detects_symlink_drift",
    ),
    "vision_and_documentation": (
        "GovernanceContracts.test_vision_has_exactly_seven_required_sections",
        "GovernanceContracts.test_mutation_missing_vision_section_is_rejected",
        "GovernanceContracts.test_readme_and_agents_must_link_without_copying_vision",
        "GovernanceContracts.test_document_layering_and_templates_are_complete",
        "GovernanceContracts.test_alignment_template_is_generated_and_cannot_expand_authorization",
    ),
    "deterministic_evidence": (
        "EvidenceContracts.test_two_clean_evidence_generations_are_byte_identical",
        "EvidenceContracts.test_evidence_digest_is_canonical_and_self_excluding",
        "EvidenceContracts.test_evidence_contains_no_temporary_or_machine_path",
        "EvidenceContracts.test_output_inside_protected_root_fails_without_writing",
        "EvidenceContracts.test_cleanup_failure_cannot_publish_ready_evidence",
        "EvidenceContracts.test_final_snapshot_occurs_only_after_install_cleanup",
        "EvidenceContracts.test_project_specific_path_fails_at_evidence_boundary",
    ),
}


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.success_ids: set[str] = set()

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self.success_ids.add(test.id())


def _matching(success_ids: set[str], suffix: str) -> str:
    matches = sorted(test_id for test_id in success_ids if test_id.endswith(suffix))
    if len(matches) != 1:
        raise RuntimeError(f"contract mapping mismatch: {suffix}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-results", type=Path)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(
        "tests/foundation", pattern="test_*.py", top_level_dir="."
    )
    runner = unittest.TextTestRunner(
        verbosity=2, resultclass=RecordingResult, warnings="error"
    )
    tests = list(_flatten(suite))
    discovered_ids = [test.id() for test in tests]
    if args.canonical_results is None:
        result = runner.run(suite)
        if not result.wasSuccessful():
            return 1
        success_ids = result.success_ids
    else:
        try:
            load_canonical_results(args.canonical_results, "foundation", repository, discovered_ids)
        except CanonicalResultError as error:
            sys.stderr.buffer.write(canonical_bytes({"error": error.code, "status": "error"}))
            return 2
        success_ids = set(discovered_ids)
    test_ids = sorted(success_ids)
    evidence = {
        "schemaVersion": 1,
        "task": "GKD-M0-A",
        "outcome": "pass",
        "tests": {
            "count": len(test_ids),
            "idDigestSha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
        },
        "contracts": {
            contract: {
                "status": "pass",
                "tests": [_matching(success_ids, suffix) for suffix in suffixes],
            }
            for contract, suffixes in sorted(CONTRACT_SUFFIXES.items())
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": "pass", "tests": len(test_ids)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
