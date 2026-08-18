# GKD-M-1B Delivery

- Status: `ready_for_acceptance`
- Outcome: `core_ready_for_live_gate`
- Base SHA: `9aec60a40572b7c0705049dbce3199d004049c81`
- Synced main SHA: `b9a768d984e2f71e8afd518e0e0f5c5af29ce6c4`
- Implementation and evidence head SHA: `b441562f02c069bbcca7aaff25c6d79eaf1fae63`
- Pull request: `https://github.com/KNaiFen/gkd/pull/2`

## Changed Files

- `src/gkd_watchdog/{constants,jsonrpc,mcp_server,model,runtime,watcher}.py`
- `src/gkd_watchdog/__init__.py` and `src/gkd_watchdog/README.md`
- `scripts/gkd-watchdog-mcp`
- `tests/watchdog/**` and `tests/__init__.py`
- `evidence/m-1-external-watcher-core/contract-results.json`
- `.gitignore`
- `.agents/{context,decisions,open-items}.md`
- `tasks/m-1-external-watcher-core/delivery.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 tests/watchdog/run_contracts.py --output evidence/m-1-external-watcher-core/contract-results.json`: pass, 37 tests; includes unit, fake-clock, actual stdio fake app-server, and MCP subprocess coverage.
- The contract runner was repeated: pass; both generated evidence files had SHA-256 `e73c582d7b08649016e351cb2facb94d36af5903e0dea87481f204e976d0eda8`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -W error::ResourceWarning -m unittest discover -s tests/watchdog -p 'test_*.py' -v`: pass, 37 tests, no resource warning.
- Sensitive scan rules covered Authorization bearer values, credential assignments, private-key markers, and the local username path. `src/`, `scripts/`, and committed M-1B evidence had zero matches; four test files contained only intentional synthetic fixtures. Output reported rule and file names, never matched values.
- `git diff --cached --check`: pass before the implementation/evidence commit.
- `node scripts/check-local-verification.mjs --base 9aec60a40572b7c0705049dbce3199d004049c81`: unavailable, exit 1 `MODULE_NOT_FOUND`; this bootstrap repository still has no fixed runner, so no `local_ready` claim is made.
- Dependency install, build, lint, typecheck, coverage, packaging, real server, paid API, real-hour wait, and live Codex/MCP connection: not run; prohibited, absent, or owned by M-1C.
- PR required checks: `required_checks_not_configured_bootstrap`; this is not a CI success claim.

## Contract Matrix

1. Twelve-hour fake-clock deadline emits one terminal result; hourly health checks emit no MCP progress/result/log frame.
2. Normal terminal returns immediately without steer; stale `active` remains healthy even when `updatedAt` does not change.
3. `systemError`, `notFound`, `errored`, failed, and interrupted states use fixed classifications; active system error orders child interrupt before parent steer.
4. Expected-parent-turn rejection is attempted once, never searches another parent, and never calls `turn/start`.
5. EOF, startup failure, malformed JSON, unknown/duplicate response IDs, response timeout, unknown state, leaked turn bodies, and schema drift terminate fail-closed.
6. Unknown fields, command/path/steer injection, invalid/empty/long IDs, parent-child alias, wrong types, over-limit deadline, invalid health interval, and missing digest are rejected before app-server construction.
7. Cancellation can interrupt only the bound child and never steers or interrupts the parent.
8. Concurrent watches keep identities and request IDs isolated; each JSON-RPC/MCP writer is serialized and active watches are bounded.
9. MCP `initialize`, `tools/list`, `tools/call`, success result, parse/parameter errors, cancellation, and zero-progress behavior pass subprocess/in-memory contracts.
10. Transcript metadata allowlists methods, field presence, IDs, and enum status only; raw body, payload, command, path, error, credential, and arbitrary field/method strings are not persisted or returned.

## Evidence

- Runtime declaration: `codex-cli 0.147.0`, `gpt-5.6-sol`, `xhigh`.
- Relevant app-server schema digest: `ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf`.
- Temporary MCP configuration accepted `tool_timeout_sec = 43200`; evidence class is `declaration_not_live_connection`.
- Production command resolution supplies one trusted executable; fixed argv appends `app-server`, uses `shell=False`, and rejects all command/path/steer fields in tool input.
- The generated evidence declares `liveD2Claimed: false` and stores no transcript or raw protocol payload.

## Residual Risks And Blockers

- No live Codex app-server was attached to an existing parent/child session. Cross-process visibility, real notification timing, and control behavior remain unproved.
- No real MCP call was held for 12 hours. The accepted 43,200-second timeout is a configuration surface, not a long-connection result.
- Normal-final duplication with the native mailbox and parent-context trace are intentionally outside this task.
- The repository has neither the fixed local verification runner nor configured required PR checks. These bootstrap gaps are recorded without converting them into success.
- The repository has no `.trellis` task lifecycle, so `task.py status/doctor/deliver` and a task-state commit were unavailable; no machine state was fabricated.

## Recommended Live Gate

Create a separate `GKD-M-1C` manual fresh-session task against the accepted fixed M-1B head. It should install only in an approved temporary environment and prove actual app-server attachment, MCP blocking/termination, normal-final mailbox de-duplication, abnormal child interrupt plus expected-turn steer, parent context trace, cancellation, and connection failure. Do not enable the auto route or claim `external_watcher_supported` unless that fixed-head live gate passes.
