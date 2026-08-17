# GKD-M-1A Delivery

- Status: `ready_for_acceptance`
- Outcome: `native_insufficient`
- Base SHA: `b3ad757ca96980e4f7fff4c3096f5e1ca13f56e9`
- Implementation and evidence head SHA: `2dffcdb40cba21793b3683ba45b4027c2b367238`
- Pull request: `https://github.com/KNaiFen/gkd/pull/1`

## Changed Files

- `probes/multiagentv2/native_probe.py`
- `probes/multiagentv2/README.md`
- `probes/multiagentv2/fixtures/normal-final.json`
- `tests/probes/test_native_probe.py`
- `evidence/m-1-native-d2/capability-probe.json`
- `evidence/m-1-native-d2/normal-final.json`
- `evidence/native-capability-matrix.md`
- `.agents/context.md`
- `.agents/decisions.md`
- `.agents/open-items.md`
- `tasks/m-1-native-d2-probe/delivery.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s tests/probes -p 'test_*.py' -v`: pass, 7 tests; no bytecode artifacts.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 probes/multiagentv2/native_probe.py --output evidence/m-1-native-d2/capability-probe.json`: pass; a second capture matched after removing only `capturedAt`.
- One-shot native final fixture: pass; explicit `gpt-5.6-sol`, `xhigh`, `fork_turns="none"`; parent received `GKD_M1_NORMAL_FINAL_OK` through final-status without external steer.
- `git diff --check` and staged `git diff --cached --check`: pass.
- Sensitive-data scan: evidence paths had no credential-pattern or absolute local-user-path matches. The all-scope credential rule matched only the synthetic redaction fixture in `tests/probes/test_native_probe.py`; no matched value was printed or committed as a real credential.
- `node scripts/check-local-verification.mjs --base b3ad757ca96980e4f7fff4c3096f5e1ca13f56e9`: unavailable in this bootstrap repository; exit 1 `MODULE_NOT_FOUND`. No `local_ready` claim is made.
- Dependency install, build, lint, typecheck, packaging, server, paid API, 65-minute wait, and 12-hour wait: not run; prohibited or unnecessary for this standard-library probe.
- PR required checks: `required_checks_not_configured_bootstrap`; PR #1 currently has no status checks to report, which is not a CI success claim.

## Capability Matrix Summary

- `pass`: 1 (`normal_final_wakeup`).
- `fail`: 3 (`single_long_wait`, `hourly_internal_watchdog`, `twelve_hour_deadline`).
- `unknown`: 6 (`healthy_zero_parent_context`, `long_tool_is_healthy`, `abnormal_wakeup`, `wrong_turn_rejected`, `child_interrupt_parent_safe`, `orchestrator_failure_wakeup`).
- Overall: `native_insufficient` for `codex-cli 0.147.0`; `external_watcher_supported` was not evaluated and is not claimed.

## Evidence

- `capability-probe.json` records the CLI version, selected configuration declarations, bundled Sol reasoning levels, 1-hour parser acceptance, 12-hour rejection class, and a digest/allowlist summary of generated app-server protocol fields.
- `normal-final.json` records only the fixed marker and invocation/result metadata; it stores no conversation body or thread identifier.
- `native-capability-matrix.md` distinguishes observed behavior from configuration declarations and protocol-only surfaces for all ten contracts.
- No raw config, full generated schema, user path, token, cookie, Authorization header, private session database, rollout JSONL, or conversation body is stored.

## Residual Risks And Blockers

- Six contracts remain `unknown` because schema names are insufficient runtime evidence and this task allowed only one bounded final-status child fixture. These unknowns do not weaken the two hard deadline failures.
- The production config declares `features.multi_agent_v2.enabled = false`; the active session nevertheless exposed and successfully used the native agents tool. The evidence records the config value as a declaration rather than claiming it is the session override source.
- This bootstrap repository does not yet contain `.trellis/scripts/task.py` or `scripts/check-local-verification.mjs`. The frozen milestone -1 plan explicitly uses a manual top-level session and ordinary Git commits before the future GKD core exists, so no task state was fabricated and no fixed-runner success is claimed.
- The PR has no required checks configured. `required_checks_not_configured_bootstrap` is a bootstrap limitation, not a green CI result.

## Recommended Next Task

After main accepts and merges this fixed-head task, create a separate milestone -1 task for the approved external app-server watcher route. Do not implement it in PR #1; if that later route cannot prove the full D2 contract, retain `manual_only_until_supported`.
