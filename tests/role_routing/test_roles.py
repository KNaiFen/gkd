from __future__ import annotations

from copy import deepcopy
import json
import unittest

import gkd_toml as tomllib

from gkd_role.roles import (
    context_manifest,
    load_role_source,
    resume_snapshot,
    role_action,
    role_catalog,
    role_files,
    validate_role_source,
)
from gkd_task.errors import TaskError

from tests.role_routing.helpers import BUNDLE_ROOT, bundle_digest


class RoleContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.digest = bundle_digest()
        self.catalog = role_catalog(BUNDLE_ROOT, self.digest)

    def test_fixed_role_matrix_is_exact_and_explicit(self) -> None:
        self.assertEqual({"contractVersion": 1, "name": "codex-host-runtime"}, self.catalog["activationProvider"])
        self.assertEqual("033c387ce08a71dcaa4f455a0e43e5f28f4e4cb09ee87a36c4509f59bdfc4c94", self.catalog["activationProviderDigest"])
        actual = {
            item["name"]: (item["model"], item["modelReasoningEffort"], item["sandboxMode"], item["runtimeSeconds"])
            for item in self.catalog["roles"]
        }
        self.assertEqual(
            {
                "gkd_executor": ("gpt-5.6-sol", "xhigh", "workspace-write", 43200),
                "gkd_acceptor": ("gpt-5.6-sol", "xhigh", "read-only", 43200),
                "gkd_ci_reviewer": ("gpt-5.6-terra", "high", "read-only", 3600),
            },
            actual,
        )

    def test_role_toml_is_deterministic_strict_and_disables_unneeded_gkd_skills(self) -> None:
        first = role_files(BUNDLE_ROOT, self.digest)
        self.assertEqual(first, role_files(BUNDLE_ROOT, self.digest))
        for name, raw in first.items():
            parsed = tomllib.loads(raw.decode("utf-8"))
            self.assertEqual(name.removesuffix(".toml"), parsed["name"])
            self.assertEqual(False, parsed["agents"]["enabled"])
            self.assertEqual(7, len(parsed["skills"]["config"]))
            self.assertEqual({"name", "description", "model", "model_reasoning_effort", "sandbox_mode", "developer_instructions", "agents", "skills"}, set(parsed))

    def test_context_manifests_are_minimal_and_explicit_about_omissions(self) -> None:
        expected = {
            "gkd_executor": {"gkd-execute", "gkd-local-verify", "gkd-ci-monitor", "gkd-optimize-ci", "gkd-review-remediation"},
            "gkd_acceptor": {"gkd-accept", "gkd-local-verify", "gkd-ci-monitor"},
            "gkd_ci_reviewer": {"gkd-ci-monitor", "gkd-optimize-ci", "gkd-review-remediation"},
        }
        for role, skills in expected.items():
            manifest = context_manifest(BUNDLE_ROOT, self.digest, role)
            self.assertEqual(skills, {item["name"] for item in manifest["skills"]})
            self.assertFalse(skills & set(manifest["omittedSkills"]))
            self.assertIn("conversation-transcripts", manifest["omittedContext"])

    def test_role_authority_matrix_denies_every_forbidden_boundary(self) -> None:
        cases = (
            ("gkd_executor", "implementation", True),
            ("gkd_executor", "trusted-accept", False),
            ("gkd_executor", "merge", False),
            ("gkd_executor", "archive", False),
            ("gkd_executor", "cleanup", False),
            ("gkd_acceptor", "fixed-head-review", True),
            ("gkd_acceptor", "implementation", False),
            ("gkd_acceptor", "candidate-write", False),
            ("gkd_ci_reviewer", "diagnose-ci-failure", True),
            ("gkd_ci_reviewer", "file-edit", False),
            ("gkd_ci_reviewer", "ci-rerun", False),
            ("gkd_ci_reviewer", "pr-update", False),
            ("gkd_ci_reviewer", "merge", False),
        )
        for role, action, allowed in cases:
            with self.subTest(role=role, action=action):
                self.assertEqual(allowed, role_action(BUNDLE_ROOT, role, action)["allowed"])

    def test_model_effort_sandbox_or_runtime_mutation_is_rejected(self) -> None:
        source, _ = load_role_source(BUNDLE_ROOT)
        for field, value in (("model", "gpt-5.6-terra"), ("modelReasoningEffort", "medium"), ("sandboxMode", "read-only"), ("runtimeSeconds", 3600)):
            mutated = deepcopy(source)
            executor = next(item for item in mutated["roles"] if item["name"] == "gkd_executor")
            executor[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(TaskError, "INVALID_ROLE_SOURCE"):
                validate_role_source(mutated)

    def test_unknown_role_source_fields_and_conflicting_skill_names_fail_closed(self) -> None:
        source, _ = load_role_source(BUNDLE_ROOT)
        mutated = deepcopy(source)
        mutated["unexpected"] = True
        with self.assertRaisesRegex(TaskError, "INVALID_ROLE_SOURCE"):
            validate_role_source(mutated)
        mutated = deepcopy(source)
        mutated["skills"].append(mutated["skills"][0])
        with self.assertRaisesRegex(TaskError, "INVALID_ROLE_SOURCE"):
            validate_role_source(mutated)

    def test_hard_rule_map_is_complete_and_each_role_context_is_a_declared_subset(self) -> None:
        source, rules = load_role_source(BUNDLE_ROOT)
        identifiers = {rule["id"] for rule in rules["rules"]}
        self.assertEqual(11, len(identifiers))
        for role in source["roles"]:
            self.assertTrue(set(role["hardRules"]).issubset(identifiers))
            manifest = context_manifest(BUNDLE_ROOT, self.digest, role["name"])
            self.assertEqual(set(role["hardRules"]), {rule["id"] for rule in manifest["hardRules"]})

    def test_resume_snapshot_contains_only_short_machine_facts(self) -> None:
        context = context_manifest(BUNDLE_ROOT, self.digest, "gkd_executor")
        compact = {name: context[name] for name in ("roleName", "roleDigest", "configDigest", "contextDigest")}
        task = {"taskId": "TASK-1", "phase": "implementing", "head": "a" * 40, "revision": 4, "requirementsDigest": "b" * 64, "planDigest": "c" * 64, "implementationDigest": "d" * 64}
        result = resume_snapshot(compact, task)
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("documentBodies", result["task"])
        self.assertNotIn("prompt", encoded.lower())
        self.assertLess(len(encoded), 1200)


if __name__ == "__main__":
    unittest.main()
