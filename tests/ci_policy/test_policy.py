from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from gkd_ci.policy import POLICY_PATH, load_validated_policy, parse_github_remote
from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from tests.ci_policy.helpers import (
    SYNTHETIC_REPOSITORY,
    init_checkout,
    policy_value,
    run,
    write_policy,
)


class PolicyContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-m3-policy-")
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_supported_remote_forms_and_multiple_repository_identities(self) -> None:
        forms = (
            "https://github.com/acme/widgets.git",
            "https://github.com/acme/widgets",
            "git@github.com:acme/widgets.git",
            "git@github.com:acme/widgets",
            "ssh://git@github.com/acme/widgets.git",
            "ssh://git@github.com/acme/widgets",
        )
        for remote in forms:
            with self.subTest(remote=remote):
                self.assertEqual(SYNTHETIC_REPOSITORY, parse_github_remote(remote))
        self.assertEqual(
            "github.com/example-org/second.repo",
            parse_github_remote("https://github.com/example-org/second.repo.git"),
        )

    def test_policy_and_checkout_validate_for_each_supported_remote_form(self) -> None:
        forms = (
            "https://github.com/acme/widgets.git",
            "git@github.com:acme/widgets.git",
            "ssh://git@github.com/acme/widgets.git",
        )
        for index, remote in enumerate(forms):
            with self.subTest(remote=remote):
                checkout = init_checkout(self.root / str(index), remote_url=remote)
                policy = load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
                self.assertEqual(SYNTHETIC_REPOSITORY, policy.repository)
                self.assertEqual(("Fixture Verify",), policy.required_checks)

    def test_policy_rejects_absent_nonfile_symlink_ancestor_and_traversal(self) -> None:
        checkout = init_checkout(self.root)
        policy_path = checkout / POLICY_PATH
        policy_path.unlink()
        with self.assertRaisesRegex(TaskError, "POLICY_INVALID"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
        policy_path.mkdir()
        with self.assertRaisesRegex(TaskError, "POLICY_INVALID"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
        policy_path.rmdir()
        external = self.root / "external-policy.json"
        external.write_bytes(canonical_bytes(policy_value()))
        policy_path.symlink_to(external)
        with self.assertRaisesRegex(TaskError, "POLICY_PATH_SYMLINK"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
        policy_path.unlink()
        (checkout / ".gkd").rmdir()
        external_directory = self.root / "external-policy"
        external_directory.mkdir()
        (external_directory / "policy.json").write_bytes(canonical_bytes(policy_value()))
        (checkout / ".gkd").symlink_to(external_directory, target_is_directory=True)
        with self.assertRaisesRegex(TaskError, "POLICY_PATH_SYMLINK"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
        with self.assertRaisesRegex(TaskError, "POLICY_PATH_UNSUPPORTED"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, "../policy.json")

    def test_policy_rejects_unknown_noncanonical_malformed_and_duplicate_values(self) -> None:
        checkout = init_checkout(self.root)
        path = checkout / POLICY_PATH
        mutations = []
        unknown = policy_value()
        unknown["extra"] = True
        mutations.append((unknown, "POLICY_INVALID"))
        unsupported = policy_value()
        unsupported["provider"] = "gitlab"
        mutations.append((unsupported, "POLICY_INVALID"))
        repository = policy_value(repository="github.com/acme/widgets.git")
        mutations.append((repository, "POLICY_INVALID"))
        branch = policy_value(base_branch="bad..branch")
        mutations.append((branch, "POLICY_INVALID"))
        check = policy_value(checks=[" leading"])
        mutations.append((check, "POLICY_INVALID"))
        duplicate = policy_value(checks=["Fixture Verify", "Fixture Verify"])
        mutations.append((duplicate, "POLICY_INVALID"))
        unsorted = policy_value(checks=["Z Check", "A Check"])
        mutations.append((unsorted, "POLICY_INVALID"))
        for value, code in mutations:
            with self.subTest(value=value), self.assertRaisesRegex(TaskError, code):
                path.write_bytes(canonical_bytes(value))
                load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)
        path.write_text(json.dumps(policy_value(), indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "POLICY_INVALID"):
            load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)

    def test_origin_missing_nongithub_mismatch_ambiguity_and_base_drift_fail_closed(self) -> None:
        cases = (
            ("missing", "ORIGIN_MISSING"),
            ("nongithub", "ORIGIN_UNSUPPORTED"),
            ("mismatch", "REPOSITORY_MISMATCH"),
            ("ambiguous", "ORIGIN_AMBIGUOUS"),
            ("base", "BASE_BRANCH_MISMATCH"),
        )
        for index, (case, code) in enumerate(cases):
            with self.subTest(case=case):
                checkout = init_checkout(self.root / str(index))
                if case == "missing":
                    run("git", "remote", "remove", "origin", cwd=checkout)
                elif case == "nongithub":
                    run("git", "remote", "set-url", "origin", "https://example.test/acme/widgets.git", cwd=checkout)
                elif case == "mismatch":
                    run("git", "remote", "set-url", "origin", "https://github.com/acme/other.git", cwd=checkout)
                elif case == "ambiguous":
                    run("git", "config", "--add", "remote.origin.url", "git@github.com:acme/widgets.git", cwd=checkout)
                else:
                    run("git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/release", cwd=checkout)
                with self.assertRaisesRegex(TaskError, code):
                    load_validated_policy(checkout, SYNTHETIC_REPOSITORY, POLICY_PATH)


if __name__ == "__main__":
    unittest.main()
