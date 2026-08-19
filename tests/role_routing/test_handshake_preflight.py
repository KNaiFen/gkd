from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from gkd_role.roles import locked_bundle_digest, role_catalog, role_files, role_record
from tests.role_routing.handshake_preflight import (
    LIVE_PROMPT,
    PARSER_SENTINEL,
    PreflightError,
    blocked_preflight_handshake,
    classify_parser_result,
    discover_codex,
    live_argument_parser_command,
    live_command,
    pending_handshake,
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
            self.assertEqual(
                {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
                facts["requestedRole"],
            )
            self.assertIs(facts["probeRepo"]["clean"], True)
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

    def test_command_v_resolution_is_the_only_codex_discovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-codex-test-") as root_name:
            executable = Path(root_name) / "codex"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            with patch("tests.role_routing.handshake_preflight.shutil.which", return_value=executable.as_posix()) as which:
                self.assertEqual(executable.resolve(), discover_codex())
            which.assert_called_once_with("codex")

    def test_live_command_uses_normal_user_routing_and_fixed_child_role(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-command-test-") as root_name:
            repo = Path(root_name).resolve()
            command = live_command("codex", repo)
            self.assertEqual("exec", command[1])
            for value in ("--ephemeral", "--strict-config", "--json", "workspace-write", 'approval_policy="never"', "agents.enabled=true", LIVE_PROMPT):
                self.assertIn(value, command)
            for forbidden in ("--ignore-user-config", "--model", "gpt-5.6-sol", "--ask-for-approval", 'model_reasoning_effort="xhigh"'):
                self.assertNotIn(forbidden, command)
            self.assertIn(trust_override(repo), command)
            self.assertNotIn("CODEX_HOME", json.dumps(command))
            parser_command = live_argument_parser_command("codex", repo)
            self.assertEqual("--help", parser_command[-1])
            self.assertNotIn(LIVE_PROMPT, parser_command)

    def test_pending_handshake_keeps_static_and_historical_evidence_separate(self) -> None:
        preflight = {
            "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
            "bundleDigest": "1" * 64,
            "roleDigest": "2" * 64,
            "configDigest": "3" * 64,
            "projectConfigDigest": "4" * 64,
            "skillDigests": {"gkd-execute": "5" * 64},
            "codexExecutableDigest": "6" * 64,
            "userConfigurationParsed": True,
            "trustedProjectLayerLoaded": True,
            "agentsEnabled": True,
            "customRoleDiscovered": True,
            "liveCommandParsed": True,
            "probeRepo": {"clean": True},
            "probeRepoUnchanged": True,
            "productionConfigUnchanged": True,
            "preflightDigest": "7" * 64,
        }
        historical = {
            "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
            "evidenceClass": "host-runtime-model-rejection",
            "codexExitCode": 1,
            "hostError": {"code": "invalid_request_error", "httpStatus": 400, "message": "historical isolation-mode rejection"},
            "handshakeDigest": "8" * 64,
        }
        first = pending_handshake(preflight, historical)
        second = pending_handshake(preflight, historical)
        self.assertEqual(first, second)
        self.assertEqual("awaiting_authorized_live_probe", first["outcome"])
        self.assertEqual(0, first["liveAttemptsConsumed"])
        self.assertEqual("normal-user-config", first["parentConfigurationSource"])
        self.assertIs(first["parentModelOverride"], False)
        self.assertEqual("HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT", first["historicalNegativeEvidence"]["hostFailure"])

    def test_blocked_preflight_records_no_model_or_live_attempt(self) -> None:
        setup = {
            "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
            "bundleDigest": "1" * 64,
            "roleDigest": "2" * 64,
            "configDigest": "3" * 64,
            "projectConfigDigest": "4" * 64,
            "skillDigests": {"gkd-execute": "5" * 64},
            "probeRepo": {"clean": True},
        }
        historical = {
            "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
            "evidenceClass": "host-runtime-model-rejection",
            "codexExitCode": 1,
            "hostError": {"code": "invalid_request_error", "httpStatus": 400, "message": "historical isolation-mode rejection"},
            "handshakeDigest": "8" * 64,
        }
        value = blocked_preflight_handshake(
            setup,
            "6" * 64,
            PreflightError("PROJECT_CONFIG_PARSE_FAILED", "unknown configuration field"),
            historical,
            True,
        )
        self.assertEqual("blocked", value["outcome"])
        self.assertEqual("PROJECT_CONFIG_PARSE_FAILED", value["preflightFailure"]["code"])
        self.assertEqual(0, value["modelInvocations"])
        self.assertEqual(0, value["liveAttemptsConsumed"])
        self.assertIs(value["setupFacts"]["customRoleDiscovered"], False)
        self.assertIs(value["setupFacts"]["liveCommandParsed"], True)


if __name__ == "__main__":
    unittest.main()
