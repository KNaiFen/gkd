# GKD-M-1B Delivery

- Status: `ready_for_acceptance`
- Outcome: `core_ready_for_live_gate`
- Base SHA: `9aec60a40572b7c0705049dbce3199d004049c81`
- Synced main SHA: `c99e065a4200caf9888e4bfec27c6931d25ec006`
- Main coordination merge SHA: `a282a8426366eeb3319cdd3460d680dbf60d1d9d`
- Implementation and evidence head SHA: `b9fa7978298fea1fe1f14e8b992eb4f2ec2bf7b3`
- Pull request: `https://github.com/KNaiFen/gkd/pull/2`

## Fixed-Head Review Closure

The six required findings reported against prior head
`94053d85ab21943978d3f68e675b5e55e79f20ca` are fixed. The negative tests below
exercise states that the prior implementation accepted or misclassified.

1. Runtime evidence is an exact equality check against the approved schema
   digest in the request parser, direct model construction, service boundary,
   and MCP schema. A different well-formed 64-hex digest is rejected before
   service or app-server construction by
   `test_rejects_well_formed_but_unapproved_runtime_digest`,
   `test_direct_request_construction_cannot_bypass_identity_invariants`, and
   `test_unapproved_runtime_digest_never_constructs_watch_service`.
2. Every child read binds child ID, session ID, and parent thread ID; every
   parent read binds parent ID and the same session, always with
   `includeTurns=false`. Missing, mismatched, or drifting ownership fails before
   interrupt or steer in `test_thread_ownership_mismatch_fails_before_control`,
   `test_thread_ownership_drift_blocks_interrupt_and_steer`, and
   `test_parent_read_remote_failure_is_protocol_not_child_abnormal`.
3. A successful interrupt RPC is not sufficient to steer. The watcher waits a
   bounded interval for an exact child/thread terminal notification and rejects
   missing, wrong-thread, wrong-turn, and nonterminal confirmations in
   `test_interrupt_without_bound_terminal_confirmation_never_steers`.
4. Only `expectedTurnMismatch` maps to `parent_steer_rejected`.
   `notFound`, `systemError`, `invalidParams`, and unclassified remote errors
   remain fixed protocol errors in
   `test_non_expected_steer_errors_remain_protocol_errors`.
5. Cancellation accepts only explicit absent/terminal child classifications;
   other interrupt failures are terminal protocol errors. MCP stdin EOF first
   cancels, then force-closes registered sessions, joins workers within fixed
   bounds, and reaps app-server processes even during initialize or interrupt
   hangs. This is covered by
   `test_cancellation_interrupt_failure_is_terminal_protocol_error`,
   `test_cancellation_explicit_absent_or_terminal_remote_state_can_succeed`, and
   `test_stdin_eof_force_closes_hanging_app_server_and_worker`.
6. Every request string echoed in a result or steer event rejects narrow GitHub,
   GitLab, OpenAI, and Slack credential shapes. Every identity field is mutated
   in `test_rejects_credential_shaped_values_in_every_echoed_id`.

## Changed Files

- `src/gkd_watchdog/{constants,jsonrpc,mcp_server,model,runtime,watcher}.py`
- `src/gkd_watchdog/README.md`
- `tests/watchdog/**`
- `evidence/m-1-external-watcher-core/contract-results.json`
- `.agents/{context,decisions,open-items}.md`
- `tasks/m-1-external-watcher-core/delivery.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 tests/watchdog/run_contracts.py --output evidence/m-1-external-watcher-core/contract-results.json`: pass twice after the final implementation change; 47 unit, fake-clock, actual stdio app-server, and MCP subprocess tests passed on both runs.
- Both final generations produced evidence SHA-256 `f02e484adae0e16ee8ce22ec84e2acb726a62e5a41c2e16adfe7378dcbcae629`; test ID digest is `2e61a1c79e02515de194ac30c9999de0f75f60bca1a1fac207d909f75e19b965`.
- The first generator attempt through the FastCtx login environment resolved an obsolete Python lacking `dataclass(slots=True)` and stopped before discovery. Final verification used the explicit active terminal interpreter shown above; both complete reruns passed.
- Sensitive scans reported rule names and file names only. No credential-shaped value, bytecode/cache artifact, production `.codex` path, or changed production config was found. Secret-label and absolute-home matches were limited to validation code, policy text, and intentional synthetic negative fixtures; generated evidence had no match.
- `git diff --check` and `git diff --cached --check`: pass before the implementation/evidence commit.
- `node scripts/check-local-verification.mjs --base 9aec60a40572b7c0705049dbce3199d004049c81`: unavailable, exit 1 `MODULE_NOT_FOUND`; this bootstrap repository has no fixed runner, so no `local_ready` claim is made.
- Dependency installation, build, lint, typecheck, coverage, packaging, real server, real-hour wait, and live Codex/MCP connection: not run; prohibited, absent, or owned by the later live gate.
- PR required checks: `required_checks_not_configured_bootstrap`; this is not a CI success claim.

## Contract Matrix

1. Twelve-hour fake-clock deadline emits one terminal result; hourly health checks emit no MCP progress/result/log frame.
2. Normal terminal returns immediately without steer; stale `active` remains healthy even when `updatedAt` does not change.
3. `systemError`, `notFound`, `errored`, failed, and interrupted states use fixed classifications; active system error orders child interrupt, terminal confirmation, then parent steer.
4. Child and parent ownership are revalidated immediately before control, after interrupt confirmation, and before steer.
5. Only an exact expected-parent-turn rejection has the dedicated rejection outcome; no fallback parent search or `turn/start` is allowed.
6. EOF, startup failure, malformed JSON, unknown/duplicate response IDs, timeout, ownership drift, unknown state, leaked turn bodies, and schema drift terminate fail-closed.
7. Unknown fields, command/path/steer injection, invalid identity, credential-shaped identity, parent-child alias, wrong types, over-limit deadline, invalid health interval, and unapproved digest are rejected before app-server construction.
8. Cancellation controls only the bound child; stdin EOF deterministically closes workers and owned app-server subprocesses.
9. Concurrent watches keep identities and request IDs isolated; each JSON-RPC/MCP writer is serialized and active watches are bounded.
10. MCP `initialize`, `tools/list`, `tools/call`, success result, parse/parameter errors, cancellation, EOF, and zero-progress behavior pass subprocess/in-memory contracts.
11. Transcript metadata allowlists methods, field presence, IDs, and enum status only; raw body, payload, command, path, remote error, credential, and arbitrary field/method strings are not persisted or returned.

## Evidence

- Runtime declaration: `codex-cli 0.147.0`, `gpt-5.6-sol`, `xhigh`.
- Relevant app-server schema digest: `ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf`.
- Temporary MCP configuration accepted `tool_timeout_sec = 43200`; evidence class is `declaration_not_live_connection`.
- Production command resolution supplies one trusted executable; fixed argv appends `app-server`, uses `shell=False`, and rejects all command/path/steer fields in tool input.
- The generated evidence declares `liveD2Claimed: false` and stores no transcript or raw protocol payload.

## Residual Risks And Blockers

- No live Codex app-server was attached to an existing parent/child session. Cross-process visibility, real notification timing, and control behavior remain unproved.
- No real MCP call was held for 12 hours. The accepted 43,200-second timeout is a configuration surface, not a long-connection result.
- Normal-final duplication with the native mailbox and parent-context trace remain outside this task.
- The repository has neither the fixed local verification runner nor configured required PR checks. These bootstrap gaps are recorded without converting them into success.
- The repository has no `.trellis` task lifecycle, so `task.py status/doctor/deliver` and a task-state commit were unavailable; no machine state was fabricated.

## Recommended Live Gate

After this new fixed head is independently accepted and merged by the main
session, create a separate `GKD-M-1C` manual fresh-session task. This execution
session did not merge PR #2, modify production configuration, or start M-1C.
