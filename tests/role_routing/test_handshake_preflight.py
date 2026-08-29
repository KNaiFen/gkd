from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import gkd_toml as tomllib

from gkd_role.roles import locked_bundle_digest, role_catalog, role_files, role_record
from tests.role_routing.handshake_preflight import (
    LIVE_PROMPT,
    PARSER_SENTINEL,
    PROBE_INSTRUCTIONS,
    PreflightError,
    blocked_preflight_handshake,
    classify_parser_result,
    completed_handshake,
    discover_codex,
    live_argument_parser_command,
    live_command,
    normalize_host_events,
    normalize_rollout_facts,
    pending_handshake,
    prepare_probe_repo,
    static_parser_command,
    validate_generated_toml,
)
from tests.role_routing.helpers import BUNDLE_ROOT
from tests.role_routing.run_contracts import _validate_handshake


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
            self.assertIs(facts["generatedProjectConfigParsed"], True)
            self.assertIs(facts["generatedRoleConfigParsed"], True)
            self.assertEqual(PROBE_INSTRUCTIONS, (repo / "AGENTS.md").read_bytes())
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

    def test_static_parser_uses_only_normal_trusted_environment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gkd-handshake-trust-test-") as root_name:
            repo = Path(root_name).resolve()
            command = static_parser_command("codex", repo)
            self.assertEqual(["codex", "app-server", "--listen", "off"], command)
            self.assertNotIn("agents.enabled", " ".join(command))

    def test_generated_toml_parser_rejects_malformed_project_and_role(self) -> None:
        definition = {
            "name": "gkd_executor",
            "description": "Executor",
            "model": "gpt-5.6-sol",
            "modelReasoningEffort": "xhigh",
            "sandboxMode": "workspace-write",
            "developerInstructions": "Return the marker.",
            "skills": ["gkd-execute"],
        }
        project = b'[agents]\nenabled = true\n[agents.gkd_executor]\ndescription = "Executor"\nconfig_file = "agents/gkd_executor.toml"\n'
        role = b'name = "gkd_executor"\ndescription = "Executor"\nmodel = "gpt-5.6-sol"\nmodel_reasoning_effort = "xhigh"\nsandbox_mode = "workspace-write"\ndeveloper_instructions = "Return the marker."\n[agents]\nenabled = false\n[[skills.config]]\npath = "../skills/gkd-execute/SKILL.md"\nenabled = true\n'
        self.assertEqual(
            {"generatedProjectConfigParsed": True, "generatedRoleConfigParsed": True},
            validate_generated_toml(project, role, definition, ["gkd-execute"]),
        )
        for malformed, valid, code in (
            (b"[agents\n", role, "GENERATED_PROJECT_CONFIG_PARSE_FAILED"),
            (project, b'name = "unterminated\n', "GENERATED_ROLE_CONFIG_PARSE_FAILED"),
        ):
            with self.subTest(code=code), self.assertRaises(PreflightError) as raised:
                validate_generated_toml(malformed, valid, definition, ["gkd-execute"])
            self.assertEqual(code, raised.exception.code)

    def test_parser_requires_trust_role_parse_and_no_transport_sentinel(self) -> None:
        classify_parser_result(1, "", f"Error: {PARSER_SENTINEL}\n")
        classify_parser_result(1, "", f"unknown configuration field `legacy`\nError: {PARSER_SENTINEL}\n")
        failures = (
            ("Project-local config, hooks, and exec policies are disabled", "PROJECT_TRUST_NOT_EFFECTIVE"),
            ("Ignoring malformed agent role definition", "CUSTOM_ROLE_PARSE_FAILED"),
            ("Error parsing project config", "PROJECT_CONFIG_PARSE_FAILED"),
            ("fatal startup error", "STATIC_PARSER_UNEXPECTED_RESULT"),
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
            self.assertEqual(["codex", "exec", "--json", LIVE_PROMPT], command)
            for forbidden in ("--ephemeral", "--strict-config", "--ignore-user-config", "--model", "gpt-5.6-sol", "--sandbox", "workspace-write", "--ask-for-approval", "approval_policy", "agents.enabled", "trust_level", "-c"):
                self.assertNotIn(forbidden, command)
            self.assertIn("tool named `spawn_agent`", LIVE_PROMPT)
            self.assertIn('agent_type="gkd_executor"', LIVE_PROMPT)
            self.assertLess(LIVE_PROMPT.index("tool named `spawn_agent`"), LIVE_PROMPT.index("wait tool"))
            self.assertIn("cannot be completed by the parent", LIVE_PROMPT)
            self.assertNotIn("CODEX_HOME", " ".join(command))
            parser_command = live_argument_parser_command("codex", repo)
            self.assertEqual(["codex", "exec", "--json", "--help"], parser_command)

    def test_pending_handshake_keeps_static_and_historical_evidence_separate(self) -> None:
        preflight = {
            "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
            "bundleDigest": "1" * 64,
            "roleDigest": "2" * 64,
            "configDigest": "3" * 64,
            "projectConfigDigest": "4" * 64,
            "probeInstructionsDigest": "a" * 64,
            "skillDigests": {"gkd-execute": "5" * 64},
            "codexExecutableDigest": "6" * 64,
            "generatedProjectConfigParsed": True,
            "generatedRoleConfigParsed": True,
            "normalEnvironmentReachedNoTransport": True,
            "trustedProjectLayerLoaded": True,
            "agentsEnabled": True,
            "projectRoleDefinitionAccepted": True,
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
            "preflightFailure": {"code": "USER_CONFIG_PARSE_FAILED", "message": "strict compatibility rejection"},
            "preflightDigest": "9" * 64,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
        }
        first = pending_handshake(preflight, historical)
        second = pending_handshake(preflight, historical)
        self.assertEqual(first, second)
        self.assertEqual("ready_for_live_diagnosis", first["outcome"])
        self.assertEqual("LIVE_DIAGNOSIS_PENDING", first["error"])
        self.assertEqual(0, first["liveAttemptsConsumed"])
        self.assertEqual("normal-user-config", first["parentConfigurationSource"])
        self.assertIs(first["parentModelOverride"], False)
        self.assertIs(first["parentStrictConfig"], False)
        self.assertEqual("HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT", first["historicalNegativeEvidence"]["hostFailure"])
        self.assertEqual("USER_CONFIG_PARSE_FAILED", first["historicalCompatibilityEvidence"]["failure"])
        self.assertIs(first["setupFacts"]["customRoleActivationProven"], False)

    def test_blocked_preflight_records_no_model_or_live_attempt(self) -> None:
        setup = {
            "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
            "bundleDigest": "1" * 64,
            "roleDigest": "2" * 64,
            "configDigest": "3" * 64,
            "projectConfigDigest": "4" * 64,
            "probeInstructionsDigest": "a" * 64,
            "skillDigests": {"gkd-execute": "5" * 64},
            "generatedProjectConfigParsed": True,
            "generatedRoleConfigParsed": True,
            "probeRepo": {"clean": True},
        }
        historical = {
            "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
            "evidenceClass": "host-runtime-model-rejection",
            "codexExitCode": 1,
            "hostError": {"code": "invalid_request_error", "httpStatus": 400, "message": "historical isolation-mode rejection"},
            "handshakeDigest": "8" * 64,
            "preflightFailure": {"code": "USER_CONFIG_PARSE_FAILED", "message": "strict compatibility rejection"},
            "preflightDigest": "9" * 64,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
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
        self.assertIs(value["setupFacts"]["projectRoleDefinitionAccepted"], False)
        self.assertIs(value["setupFacts"]["customRoleActivationProven"], False)
        self.assertIs(value["setupFacts"]["liveCommandParsed"], True)

    def test_completed_handshake_uses_only_minimal_host_facts(self) -> None:
        preflight = pending_handshake(
            {
                "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
                "bundleDigest": "1" * 64,
                "roleDigest": "2" * 64,
                "configDigest": "3" * 64,
                "projectConfigDigest": "4" * 64,
                "probeInstructionsDigest": "a" * 64,
                "skillDigests": {"gkd-execute": "5" * 64},
                "codexExecutableDigest": "6" * 64,
                "generatedProjectConfigParsed": True,
                "generatedRoleConfigParsed": True,
                "normalEnvironmentReachedNoTransport": True,
                "trustedProjectLayerLoaded": True,
                "agentsEnabled": True,
                "projectRoleDefinitionAccepted": True,
                "liveCommandParsed": True,
                "probeRepo": {"clean": True},
                "probeRepoUnchanged": True,
                "productionConfigUnchanged": True,
                "preflightDigest": "7" * 64,
            },
            {
                "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
                "evidenceClass": "host-runtime-model-rejection",
                "codexExitCode": 1,
                "hostError": {"code": "invalid_request_error", "httpStatus": 400, "message": "historical isolation-mode rejection"},
                "handshakeDigest": "8" * 64,
                "preflightFailure": {"code": "USER_CONFIG_PARSE_FAILED", "message": "strict compatibility rejection"},
                "preflightDigest": "9" * 64,
                "modelInvocations": 0,
                "liveAttemptsConsumed": 0,
            },
        )
        facts = {
            "parentTurnEntered": True,
            "spawnCount": 0,
            "spawnFacts": [],
            "activatedRoles": [],
            "unexpectedRoles": [],
            "downgradeObserved": False,
            "fallbackObserved": False,
            "childBindingValid": False,
            "childThreadIdentityHash": None,
            "childTerminalObserved": False,
            "parentTerminalObserved": True,
            "codexExitCode": 0,
            "eventTypes": ["thread.started", "turn.started", "item.started:collab_tool_call:wait", "turn.completed"],
            "threadIdentityHashes": ["a" * 64],
            "hostError": None,
        }
        value = completed_handshake(preflight, facts)
        self.assertEqual("blocked", value["outcome"])
        self.assertEqual("PROBE_ORCHESTRATION_MISS_WAIT_BEFORE_SPAWN", value["error"])
        self.assertEqual(1, value["modelInvocations"])
        self.assertEqual(1, value["liveAttemptsConsumed"])
        self.assertIs(value["setupFacts"]["customRoleActivationProven"], False)
        with self.assertRaises(PreflightError) as raised:
            completed_handshake(preflight, {**facts, "agentMessage": "GKD_EXECUTOR_CHILD_TERMINAL"})
        self.assertEqual("INVALID_HOST_FACTS", raised.exception.code)

    def test_normalize_host_events_requires_structured_role_and_terminals(self) -> None:
        child = "child-thread"
        events = [
            {"type": "thread.started", "thread_id": "parent-thread"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {
                    "type": "collab_tool_call",
                    "tool": "spawn_agent",
                    "agent_type": "gkd_executor",
                    "task_name": "gkd_executor_handshake",
                    "fork_turns": "none",
                    "receiver_thread_ids": [child],
                    "status": "completed",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "collab_tool_call",
                    "tool": "wait",
                    "agents_states": {child: {"status": "completed"}},
                    "status": "completed",
                },
            },
            {"type": "turn.completed"},
        ]
        facts = normalize_host_events(events, 0, "", Path("/temporary/probe"))
        self.assertEqual(1, facts["spawnCount"])
        self.assertEqual([{"agentType": "gkd_executor", "taskName": "gkd_executor_handshake", "forkTurns": "none"}], facts["spawnFacts"])
        self.assertEqual(["gkd_executor"], facts["activatedRoles"])
        self.assertEqual([], facts["unexpectedRoles"])
        self.assertIs(facts["childTerminalObserved"], True)
        self.assertIs(facts["childBindingValid"], True)
        self.assertIs(facts["parentTerminalObserved"], True)
        self.assertIsNone(facts["hostError"])
        self.assertEqual(2, len(facts["threadIdentityHashes"]))

        without_role = [{**events[2], "item": {key: value for key, value in events[2]["item"].items() if key != "agent_type"}}, *events[3:]]
        missing = normalize_host_events([events[0], events[1], *without_role], 0, "", Path("/temporary/probe"))
        self.assertEqual(1, missing["spawnCount"])
        self.assertEqual([], missing["activatedRoles"])

    @staticmethod
    def _rollout_fixture(
        *,
        agent_type: str = "gkd_executor",
        task_name: str = "gkd_executor_handshake",
        fork_turns: str = "none",
        activity_thread: str = "child-thread",
        child_thread: str = "child-thread",
        spawn_count: int = 1,
    ) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]]]:
        parent = [
            {"payload": {"type": "task_started"}},
            *[
                {"payload": {"type": "function_call", "namespace": "agents", "name": "spawn_agent", "arguments": json.dumps({"agent_type": agent_type, "task_name": task_name, "fork_turns": fork_turns, "message": "redacted"})}}
                for _ in range(spawn_count)
            ],
            {"payload": {"type": "sub_agent_activity", "kind": "started", "agent_path": f"/root/{task_name}", "agent_thread_id": activity_thread}},
            {"payload": {"type": "function_call", "namespace": "agents", "name": "wait_agent", "arguments": "{\"timeout_ms\": 180000}"}},
            {"payload": {"type": "task_complete", "last_agent_message": "GKD_PARENT_TERMINAL"}},
        ]
        child = [
            {
                "type": "session_meta",
                "payload": {
                    "id": child_thread,
                    "session_id": "parent-thread",
                    "thread_source": "subagent",
                    "source": {"subagent": {"thread_spawn": {"parent_thread_id": "parent-thread", "agent_path": f"/root/{task_name}", "agent_role": agent_type}}},
                },
            },
            {"payload": {"type": "task_complete", "last_agent_message": "GKD_EXECUTOR_CHILD_TERMINAL"}},
        ]
        return parent, {child_thread: child}

    def test_normalize_rollout_facts_proves_spawn_and_exact_child_terminals(self) -> None:
        parent, children = self._rollout_fixture()
        facts = normalize_rollout_facts(parent, children, "parent-thread", 0)
        self.assertEqual(1, facts["spawnCount"])
        self.assertEqual([{"agentType": "gkd_executor", "taskName": "gkd_executor_handshake", "forkTurns": "none"}], facts["spawnFacts"])
        self.assertEqual(["gkd_executor"], facts["activatedRoles"])
        self.assertIs(facts["childBindingValid"], True)
        self.assertEqual("e706190eeef92244d0cf590f8ba3125baa8e5062ee7034b086e21cba78dceb71", facts["childThreadIdentityHash"])
        self.assertIs(facts["childTerminalObserved"], True)
        self.assertIs(facts["parentTerminalObserved"], True)
        self.assertEqual(2, len(facts["threadIdentityHashes"]))

    def test_rollout_rejects_wrong_task_name_and_fork_turns(self) -> None:
        for field, value in (("task_name", "other_task"), ("fork_turns", "all")):
            parent, children = self._rollout_fixture(**{field: value})
            facts = normalize_rollout_facts(parent, children, "parent-thread", 0)
            handshake = completed_handshake(self._handshake_preflight(), facts)
            self.assertEqual("blocked", handshake["outcome"], field)
            _validate_handshake(handshake)

    def test_rollout_rejects_unrelated_child_terminal_and_wrong_child_identity(self) -> None:
        parent, children = self._rollout_fixture(activity_thread="expected-child", child_thread="other-child")
        facts = normalize_rollout_facts(parent, children, "parent-thread", 0)
        self.assertIs(facts["childBindingValid"], False)
        self.assertIs(facts["childTerminalObserved"], False)
        handshake = completed_handshake(self._handshake_preflight(), facts)
        self.assertEqual("blocked", handshake["outcome"])
        _validate_handshake(handshake)

    def test_rollout_rejects_multiple_spawn_and_computes_fallback(self) -> None:
        parent, children = self._rollout_fixture(spawn_count=2)
        facts = normalize_rollout_facts(parent, children, "parent-thread", 0)
        self.assertEqual(2, facts["spawnCount"])
        handshake = completed_handshake(self._handshake_preflight(), facts)
        self.assertEqual("blocked", handshake["outcome"])
        _validate_handshake(handshake)
        parent, children = self._rollout_fixture(agent_type="worker")
        facts = normalize_rollout_facts(parent, children, "parent-thread", 0)
        self.assertIs(facts["downgradeObserved"], True)
        self.assertIs(facts["fallbackObserved"], True)

    def _handshake_preflight(self) -> dict[str, object]:
        historical = {
            "hostFailure": "HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT",
            "evidenceClass": "host-runtime-model-rejection",
            "codexExitCode": 1,
            "hostError": {"code": "invalid_request_error", "httpStatus": 400, "message": "historical"},
            "handshakeDigest": "8" * 64,
            "preflightFailure": {"code": "USER_CONFIG_PARSE_FAILED", "message": "strict compatibility rejection"},
            "preflightDigest": "9" * 64,
            "modelInvocations": 0,
            "liveAttemptsConsumed": 0,
        }
        return pending_handshake(
            {
                "requestedRole": {"name": "gkd_executor", "model": "gpt-5.6-sol", "reasoningEffort": "xhigh", "sandbox": "workspace-write"},
                "bundleDigest": "1" * 64,
                "roleDigest": "2" * 64,
                "configDigest": "3" * 64,
                "projectConfigDigest": "4" * 64,
                "probeInstructionsDigest": "a" * 64,
                "skillDigests": {"gkd-execute": "5" * 64},
                "codexExecutableDigest": "6" * 64,
                "generatedProjectConfigParsed": True,
                "generatedRoleConfigParsed": True,
                "normalEnvironmentReachedNoTransport": True,
                "trustedProjectLayerLoaded": True,
                "agentsEnabled": True,
                "projectRoleDefinitionAccepted": True,
                "liveCommandParsed": True,
                "probeRepo": {"clean": True},
                "probeRepoUnchanged": True,
                "productionConfigUnchanged": True,
                "preflightDigest": "7" * 64,
            },
            historical,
        )


if __name__ == "__main__":
    unittest.main()
