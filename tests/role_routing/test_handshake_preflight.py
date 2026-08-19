from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

from gkd_role.roles import locked_bundle_digest, role_catalog, role_files, role_record
from tests.role_routing.handshake_preflight import (
    LIVE_PROMPT,
    PARSER_SENTINEL,
    PreflightError,
    classify_parser_result,
    live_command,
    prepare_probe_repo,
    static_parser_command,
    trust_override,
)
from tests.role_routing.helpers import BUNDLE_ROOT


class HandshakePreflightContracts(unittest.TestCase):
    def test_prepare_repo_uses_exact_role_skills_and_explicit_registration(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-preflight-test-") as root_name:
            repo = Path(root_name) / "repo"
            facts = prepare_probe_repo(BUNDLE_ROOT, repo)
            digest = locked_bundle_digest(BUNDLE_ROOT)
            catalog = role_catalog(BUNDLE_ROOT, digest)
            role = role_record(catalog, "gkd_executor")
            self.assertEqual(
                role_files(BUNDLE_ROOT, digest)["gkd_executor.toml"],
                (repo / ".codex" / "agents" / "gkd_executor.toml").read_bytes(),
            )
            self.assertEqual(set(role["skills"]), {path.name for path in (repo / ".codex" / "skills").iterdir()})
            project = tomllib.loads((repo / ".codex" / "config.toml").read_text(encoding="utf-8"))
            self.assertIs(project["agents"]["enabled"], True)
            self.assertEqual("agents/gkd_executor.toml", project["agents"]["gkd_executor"]["config_file"])
            self.assertEqual(role["configDigest"], facts["configDigest"])
            self.assertEqual(catalog["bundleDigest"], facts["bundleDigest"])
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            )
            self.assertEqual("", status.stdout)

    def test_trust_override_is_one_inline_table_keyed_by_canonical_repo(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-trust-test-") as root_name:
            repo = Path(root_name).resolve()
            parsed = tomllib.loads(trust_override(repo))
            self.assertEqual({repo.as_posix(): {"trust_level": "trusted"}}, parsed["projects"])
            command = static_parser_command("codex", repo)
            self.assertIn("--strict-config", command)
            self.assertIn("agents.enabled=true", command)

    def test_parser_requires_trust_role_parse_and_no_transport_sentinel(self) -> None:
        classify_parser_result(1, "", f"Error: {PARSER_SENTINEL}\n")
        failures = (
            ("Project-local config, hooks, and exec policies are disabled", "PROJECT_TRUST_NOT_EFFECTIVE"),
            ("Ignoring malformed agent role definition", "CUSTOM_ROLE_PARSE_FAILED"),
            ("unknown configuration field `bad`", "PROJECT_CONFIG_PARSE_FAILED"),
        )
        for message, code in failures:
            with self.subTest(code=code), self.assertRaisesRegex(PreflightError, ".+") as raised:
                classify_parser_result(1, "", message)
            self.assertEqual(code, raised.exception.code)

    def test_live_command_is_fixed_and_never_uses_an_alternate_codex_home(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-command-test-") as root_name:
            repo = Path(root_name).resolve()
            command = live_command("codex", repo)
            self.assertEqual("exec", command[1])
            for value in ("--ephemeral", "--ignore-user-config", "--strict-config", "--json", "gpt-5.6-sol", "workspace-write", 'approval_policy="never"', "agents.enabled=true", LIVE_PROMPT):
                self.assertIn(value, command)
            self.assertNotIn("--ask-for-approval", command)
            self.assertIn('model_reasoning_effort="xhigh"', command)
            self.assertIn(trust_override(repo), command)
            self.assertNotIn("CODEX_HOME", json.dumps(command))


if __name__ == "__main__":
    unittest.main()
