# GKD-M2-A Requirements v1

## Goal

Deliver the canonical role and routing core required before GKD may attempt an
automatic task route. The bundle must define fixed executor, acceptor, and CI
reviewer roles; bind live role activation to the milestone 1 offer/claim core;
keep manual execution as the default; generate the deterministic one-hour and
12-hour wait decisions; minimize role context; and provide temporary-install
migration contracts for duplicate Skills and the legacy CI reviewer role.

This task establishes `role_routing_core_ready`. It does not run the real
one-hour fresh-runtime gate and cannot enable the automatic route by itself.

## User Decisions

- Milestone 2 remains a manually opened top-level execution session using
  GPT-5.6 Sol with `xhigh` reasoning. No implementation subagent owns this task.
- Milestone 2 is split into `GKD-M2-A` for the deterministic role/routing core
  and `GKD-M2-B` for the independent fresh-runtime one-hour wait gate.
- Canonical custom role names are `gkd_executor`, `gkd_acceptor`, and
  `gkd_ci_reviewer`. The old generic `ci_reviewer` is replaced in the same
  temporary migration and is not retained as an alias.
- `gkd_executor` and `gkd_acceptor` use GPT-5.6 Sol with `xhigh` reasoning.
  `gkd_ci_reviewer` uses GPT-5.6 Terra with `high` reasoning and a read-only
  sandbox. Exact role configuration must be emitted by deterministic source,
  not inferred from the parent session.
- Manual routing is the default. Automatic routing is accepted only when it is
  explicitly requested and every role, offer/claim, bundle-digest, and wait
  gate is already proven. This task must continue returning manual-only until
  M2-B records a successful fresh-runtime gate.
- The wait contract uses one native `wait_agent(timeout_ms=3600000)` call per
  healthy interval and may cover at most 12 such intervals after claim. A
  healthy timeout causes an immediate re-wait with no voluntary output or
  side-channel inspection. The 12-hour terminal path interrupts the bound
  executor once and returns one timeout result.
- The five existing GKD workflow Skills are brought into the canonical bundle
  as one authoritative copy. Six known `.agents/skills` duplicates are disabled
  from discovery through generated `skills.config` entries but are not deleted.
- Production `~/.codex`, AIO, paid runners, Secrets, repository settings, tags,
  Releases, and milestone 3 behavior remain outside this task.

## Scope

- Add canonical, installable definitions for the three GKD custom roles with
  fixed names, model/effort, sandbox, role digest, config digest, minimal Skill
  allowlist, and narrow developer instructions.
- Add a trusted role activation/evidence boundary that binds task, repository,
  task branch, offer, envelope, route, agent/thread identity, role/config
  digests, bundle content digest, activation time, and one-time claim use.
  Agent prose or a candidate-created file is not sufficient evidence.
- Integrate the provider with milestone 1 claim without weakening capability,
  CAS, lock, receipt, journal, revoke, reclaim, delivery, or acceptance rules.
- Add a deterministic router with `manual` default, explicit `automatic`
  request, precondition matrix, stable refusal codes, and no fallback from a
  failed automatic attempt to a generic worker or implicit manual claim.
- Add deterministic wait state and commands that decide `wait_again`,
  `executor_terminal`, `executor_error`, `deadline_timeout`, or fail-closed
  drift from canonical input facts. The Agent performs the actual host tool
  call; scripts own counters, deadlines, identity binding, and machine output.
- Add canonical versions of `gkd-main`, `gkd-execute`, `gkd-accept`,
  `gkd-local-verify`, and `gkd-ci-monitor`, removing AIO-specific paths and
  `.trellis` assumptions from generic mechanism. The CI monitor remains
  disabled/fail-closed where milestone 3 repository policy is unavailable.
- Add temporary-home installer/migration fixtures that atomically install the
  three roles and five Skills, remove the legacy `ci_reviewer` role in the same
  transaction, disable only the six approved duplicate Skill paths, preserve
  their files, and retain every mapped global AGENTS hard rule.
- Add role-context manifest generation so each role receives only its required
  Skills and instructions. Omitted context must be explicit and testable.
- Add L1/L2 contracts, deterministic evidence, manifest/lock regeneration, and
  retained regression coverage proportional to the new bundle surface.
- Permit one short, bounded role-handshake verification in an isolated
  temporary home only after deterministic tests pass. It must not implement
  repository code or serve as the M2-B one-hour gate.

## Non-Goals

- Running or claiming success for a real one-hour wait, 12-hour wall-clock run,
  or automatic implementation task. Those belong to GKD-M2-B and later tasks.
- Implementing GitHub repository policy, required-check discovery, billing,
  resource presets, secret scanning, CI optimization, review remediation,
  finalization PRs, version release, tag, or GitHub Release behavior.
- Installing into or editing production `~/.codex`, deleting `.agents` Skill
  sources, changing the user's global AGENTS file, or replacing the live legacy
  CI reviewer role.
- Modifying AIO, adding consumer-specific repository identity/check names, or
  treating AIO's `.trellis` workflow as canonical GKD mechanism.
- Using candidate code, candidate role files, Agent self-report, conversation
  text, private session databases, or rollout logs as trusted proof that this
  bootstrap task was correctly claimed or executed.
- Falling back to built-in `worker`, a shorter wait loop, an external watcher,
  repeated polling, or a second executor when a gate fails.

## Acceptance Criteria

1. Strict schemas and deterministic generators produce byte-identical role
   files, role-context manifests, activation records, route decisions, wait
   state, migration plans, bundle manifest/lock, and evidence in two clean
   temporary roots.
2. Installed role fixtures contain exactly one `gkd_executor`, one
   `gkd_acceptor`, and one `gkd_ci_reviewer`; `ci_reviewer` is absent. Role
   names, model/effort, sandbox, instructions, and config/role digests match the
   canonical source and reject unknown or conflicting fields.
3. Executor cannot accept, merge, archive, or clean up; acceptor cannot own
   implementation or mutate candidate files; CI reviewer cannot edit files,
   rerun/dispatch/cancel CI, change PR metadata, or merge.
4. Claim succeeds only with trusted activation evidence bound to the exact
   offer/envelope/task/agent/role/config/bundle facts. Missing, stale, replayed,
   candidate-written, self-reported, cross-task, cross-role, or digest-drifted
   evidence fails before a claim commit.
5. Router contracts prove manual default, explicit automatic selection, exact
   gate evaluation, stable manual-only refusal, and zero generic-worker or
   alternate-command fallback. M2-A output cannot mark automatic routing ready.
6. Fake-clock wait contracts prove 1 through 11 healthy timeouts each produce
   only `wait_again`; child final/error returns immediately; head/task/agent
   drift fails closed; the 12th elapsed hour produces one timeout and one bound
   interrupt decision; no branch reads, CI reads, analysis, or progress output
   is permitted between healthy waits.
7. Temporary migration tests prove the six approved duplicate Skill paths are
   disabled through exact `skills.config` entries without deleting bytes;
   unrelated Skills remain enabled; repeated migration is idempotent; partial
   failure restores exact preimages or freezes safely.
8. The five canonical GKD Skills use generic task-core commands and portable
   locators. No production absolute path, AIO identity, `.trellis` command, or
   consumer check policy appears in installed files or evidence.
9. Role context tests prove each role loads only the declared minimum Skills and
   hard instructions. The generated global-AGENTS migration map preserves every
   approved hard rule without adding profiles, plugin/MCP pruning, or context
   budget changes.
10. Two temporary installs have identical version, content digest, inventory,
    modes, role digests, Skill digests, and migration output. Production
    `~/.codex`, AIO, and unrelated repository state remain byte-unchanged.
11. All milestone 1 task-core contracts, foundation contracts, retained watcher
    core contracts, and watcher live-negative tests pass. No historical live
    watcher probe, dependency installation, large build, or paid API runs.
12. A bounded isolated role handshake, if the host exposes sufficient trusted
    facts, binds the expected custom role and returns a path-free terminal
    result. If reliable evidence cannot be established, the task stops as
    `blocked`; fixture self-report cannot upgrade the outcome.
