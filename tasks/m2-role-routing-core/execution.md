# GKD-M2-A: Role And Routing Core

## Sole Entry For The Execution Session

Open a new top-level Codex session in this task worktree and send only the
launch prompt produced by main. Read this file and the adjacent requirements,
plan, and implementation documents completely before any implementation.

The session must use GPT-5.6 Sol with `xhigh` reasoning. It is a manually opened
top-level execution session, not main and not the future `gkd_executor`. It must
stop after fixed-head delivery. It must not accept, merge, start GKD-M2-B,
enable automatic routing, or start milestone 3.

## Task Identity

- Status: `delivered_ready`
- Task: `GKD-M2-A`
- Repository: `KNaiFen/gkd`
- Base branch: `main`
- Task branch: `task/m2-role-routing-core`
- Fixed base SHA: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- PR: `https://github.com/KNaiFen/gkd/pull/6`
- Rework findings: `tasks/m2-role-routing-core/findings.md` (F-001 through F-005
  resolved and awaiting independent acceptance); this handoff does not authorize
  acceptance, merge, M2-B, production installation, or AIO changes.
- Requirements: `tasks/m2-role-routing-core/requirements.md`, version 5
- Plan: `tasks/m2-role-routing-core/plan.md`, version 5
- Implementation notes: `tasks/m2-role-routing-core/implementation.md`, version 5
- Route: manual top-level execution session
- Action mode: `implement_and_merge_on_acceptance`

The worktree absolute path is launch-time machine state supplied by the main
handoff Prompt. Do not write it into tracked source, task records, evidence, or
archive.

## Required Reading

Before any command that changes files, read completely:

1. root `AGENTS.md` and `VISION.md`;
2. `.agents/context.md`, `.agents/decisions.md`, and `.agents/open-items.md`;
3. this task's `requirements.md`, `plan.md`, `implementation.md`, and
   `execution.md`;
4. the approved GKD core implementation plan and plan index from the read-only
   AIO planning source supplied in the launch Prompt;
5. `tasks/m1-deterministic-task-core/acceptance.md` and the exact milestone 1
   task/runtime/acceptance modules that will be extended;
6. current official OpenAI documentation for Codex custom agents, subagents,
   Skills, AGENTS discovery, and config fields;
7. the five existing production GKD Skills, legacy `ci-reviewer.toml`, and six
   duplicate Skill groups as read-only migration evidence.

Do not read private session databases, conversation transcripts, credentials,
or unrelated production configuration. The user-authorized F-004 test-session
parent/child rollout may be read only for exact offline normalization; do not
copy raw records, prompts, paths, or plain thread identities into the repository.

## Bootstrap Exception

Milestone 1 intentionally leaves installed claim routing fail-closed until a
trusted runtime evidence provider exists. M2-A creates that provider, so it
cannot use the existing CLI or candidate role code to prove that this same task
was claimed by `gkd_executor`.

Do not create or hand-edit a task `task.json`, offer, claim, activation,
authorization, journal, or receipt for M2-A. Do not use candidate code to claim,
deliver, accept, or merge its own PR. The reviewed Markdown, Git branch/worktree,
manual top-level session, and fixed-head independent acceptance remain the
bootstrap authority for this task. This exception ends after M2-A for behavior
that its accepted bundle can actually prove.

## Authorization And Hard Boundaries

The existing `gkd_core_implementation` authorization permits this session to:

1. modify only this task worktree within the approved M2-A file scope;
2. use Python standard library, Git, system temporary directories, temporary
   Codex homes/configs, fake clocks/nonces, fake host adapters, and temporary
   Git repositories for L1/L2 contracts;
3. inspect production GKD Skills/legacy role and AIO planning inputs read-only;
4. commit and push the task branch, create/update its Draft PR, and perform
   task-related repair;
5. after hermetic gates pass, run no-model static parsing and bounded short live
   handshake diagnosis against the normally configured local Codex host and a
   temporary project-scoped custom-agent configuration. Only the final complete
   delivery head is frozen for independent acceptance.

It must not:

1. modify or install into production `~/.codex` or AIO;
2. delete duplicate `.agents` Skills, edit global AGENTS, or replace the live
   `ci_reviewer` role;
3. change GitHub settings, Secrets, runners, billing, tags, Releases, or the
   sandbox repository;
4. install dependencies, run Rust/Tauri/frontend builds, generate large caches,
   invoke API-key billed APIs outside the normal authorized Codex login path, or
   run the historical live watcher probe;
5. perform the M2-B real one-hour wait or claim automatic routing is ready;
6. delegate investigation, design, implementation, review judgment, or
   repository writes to a subagent;
7. accept or merge its own PR, start another task, or modify main directly.

If a material requirement, role authority, model/effort, route default, wait
contract, migration boundary, public interface, or external action must change,
stop as `blocked` and return the proposed plan delta. Do not edit `plan.md` to
manufacture approval.

## Startup Gates

1. Confirm current Git root is the registered M2-A worktree, branch is exactly
   `task/m2-role-routing-core`, origin is `KNaiFen/gkd`, fixed base is an
   ancestor, and the worktree is clean.
2. Confirm GPT-5.6 Sol and `xhigh`; stop rather than downgrade.
3. Fetch `origin/main`. It may differ from the fixed base only by main-session
   task registration/coordination records. Inspect every intervening commit and
   path. Merge only that allowed main update; unknown product drift is a
   blocker. Record the synchronized main SHA in delivery.
4. Confirm the PR head/branch/base match this task after main has supplied
   the final PR number.
5. Run baseline task-core 104, foundation 53, watcher core 47, and watcher
   live-negative 15 tests. Do not run the four-scenario live probe.
6. Snapshot the protected production configuration paths and the read-only AIO
   planning source with a path-free digest method before implementation. All
   repository/configuration writes must remain in the task worktree or explicit
   system temporary roots. Host-owned operational metadata created by the
   authorized live handshake is not configuration or evidence; do not inspect
   its contents, delete pre-existing state, or claim the entire Codex home is
   byte-unchanged.

## Production-Environment Handshake Preparation

The earlier isolation-mode attempt and its HTTP 400 remain historical negative
evidence. This execution session owns static preparation, bounded short live
diagnosis, evidence normalization, and final delivery without intermediate
fixed-head authorization stops.

1. Resolve the CLI only through `command -v codex`. Record a path-free executable
   digest and version. Use `codex login status` only as a boolean before live
   diagnosis. Do not inspect auth files, tokens, cookies,
   private sessions, or print user configuration.
2. Create a clean explicit system-temporary Git repository. Render the exact
   candidate `gkd_executor` and required Skills into project `.codex/agents` and
   `.codex/skills`; commit them and bind bundle/role/config/project/Skill digests.
3. Strictly parse the generated project config and `gkd_executor.toml` with
   Python `tomllib`, and compare every field to the canonical role source. With
   normal `CODEX_HOME` and user configuration, then run only
   `codex app-server --listen off` from the fresh Git root.
   Static v5 diagnosis proved that a nested fresh repository does not inherit
   the outer worktree trust identity. The user explicitly established trust for
   the exact path through the normal Codex UI; the execution session must not
   write or inspect that configuration. This
   non-strict host startup must reach the no-transport boundary without a project
   config, trust, role, or other fatal startup failure. Do not set an alternate
   home or use `--ignore-user-config`. A normal user unknown-field warning is not
   a project-config failure when the expected boundary is reached.
4. Parse the frozen live command with `--help`, consuming no model turn. The
   command is `codex exec --json <fixed-prompt>` with
   `cwd=<probe-repo>`. It
   contains no `--strict-config`, `--ignore-user-config`, parent model/effort,
   sandbox, approval, agents-enabled, fallback, or alternate-role
   override. The child TOML remains Sol/xhigh/workspace-write.
5. Static evidence owns requested role configuration, all GKD digests, strict
   generated-TOML parsing, trust, accepted project-role definition, CLI
   resolution, command parsing, clean repo, and production configuration
   non-drift. The expected no-transport boundary is not activation evidence. If
   any fact is missing, record one redacted
   machine-readable preflight failure, keep model/attempt counts at zero, and
   stop without requesting a live launch.
6. After static gates pass, run a bounded live diagnosis. The fixed Prompt must
   require the exposed `spawn_agent` exactly once with `agent_type=gkd_executor`, then
   call the actual wait tool only after spawn succeeds. A wait-before-spawn,
   tool-name miss, or invalid argument is `probe_orchestration_miss`; inspect the
   complete temporary JSONL/parent response, correct the Prompt or actual tool
   name, and retry within a small explicit attempt cap. Never downgrade, replace
   the role, or use a built-in fallback.
7. Host evidence owns only parent turn entry, exactly one named `gkd_executor`
   spawn, no other role/downgrade/fallback, child terminal, parent terminal,
   exit code, and redacted host error. It need not echo GKD digests. Delete raw
   JSONL and the temporary repo after final normalization.
8. Compare approved production configuration surfaces before/after static and
   live invocation. Existing provider/routing/login configuration may be read by
   normal Codex startup but must not be printed, copied, or modified.

## Implementation Contract

Implement every approved requirement and material plan field. In particular:

1. Add deterministic canonical role definitions and generated installable TOML
   for `gkd_executor`, `gkd_acceptor`, and `gkd_ci_reviewer` with fixed model,
   effort, sandbox, instructions, context manifest, and digests.
2. Implement trustworthy one-time activation/runtime evidence and integrate it
   with M1 offer/claim without weakening existing CAS, lock, capability,
   journal, receipt, recovery, revoke/reclaim, delivery, or acceptance behavior.
3. Implement manual-default/explicit-automatic routing with exact readiness
   gates, stable refusal, no generic-worker fallback, and a forced manual-only
   result until M2-B evidence exists.
4. Implement deterministic one-hour/12-hour wait state transitions and the GKD
   main Skill orchestration contract. M2-A tests use fake time and fake host
   results; they do not wait one real hour.
5. Canonicalize the five GKD workflow Skills and remove AIO-specific mechanism.
   Keep CI monitoring fail-closed where milestone 3 policy facts are absent.
6. Implement minimal role context generation, exact six-group Skill discovery
   disablement, AGENTS hard-rule mapping, and same-transaction legacy
   `ci_reviewer` replacement in temporary installation fixtures.
7. Extend canonical source, schemas, manifest/lock, documentation, dedicated M2
   tests, deterministic evidence, and protected-surface checks.

## Required Contracts

- Strict canonical schema/unknown-field/path/symlink/digest tests for role,
  activation, route, wait, context, and migration records.
- Positive/negative/mutation tests for every role authority boundary.
- Missing/stale/replayed/cross-task/cross-role/candidate-written activation
  rejection before claim commit; concurrent activation/claim has one winner.
- A full temporary-task positive contract proves trusted-main activation receipt
  to exact offer/envelope claim and delivery. Candidate-facing CLI and ordinary
  library claim/recovery without a trusted-main provider fail before activation,
  runtime, claim, or tracked writes. Test-only fixture seams must not be present
  in the canonical payload or installed inventory. Same-user monkeypatch,
  private-API calls, and direct runtime-file edits are explicit non-goals.
- Manual default, explicit automatic request, incomplete gate refusal, bundle or
  role drift, zero fallback, and M2-B gate absence tests.
- Fake-clock intervals 1 through 12, early child final/error, user interruption,
  agent/task/head drift, immediate silent re-wait decision, and exactly one
  deadline interrupt/timeout result.
- Two temporary installs proving exact role/Skill inventory and modes, legacy
  role absence, six duplicates disabled but preserved, unrelated Skills
  untouched, AGENTS mapping lossless, idempotence, and failure recovery.
- Per-role context snapshots proving only required Skills/instructions are
  loaded and no production/AIO paths leak into installed output or evidence.
- Retained task-core/foundation/watcher short regressions and two byte-identical
  M2 evidence generations from disjoint clean temporary roots.
- Tests prove the live command is exactly `codex exec --json <fixed-prompt>`,
  has no `--ignore-user-config`, parent model/effort, `--strict-config`, sandbox,
  approval, agents-enabled, alternate `CODEX_HOME`, or built-in role, and
  that its argument vector parses without a model invocation.

## Packaging And Evidence

1. Add every payload file to `canonical/source.toml`; regenerate manifest and
   lock only through the canonical bundle generator.
2. Install into two independent explicit system-temporary targets, verify equal
   bundle version/content digest/inventory/modes, and exercise installed role,
   route, activation, wait, context, and migration commands.
3. Generate M2 evidence twice with controlled clock/nonce and disjoint fixture
   roots. Commit only the canonical output after byte comparison.
4. Scan source, installed payload, task records, and evidence for production
   paths, plaintext capabilities, real agent/session identifiers, credentials,
   AIO-specific policy, undeclared files, and context outside each role's
   allowlist.
5. Remove all temporary homes and fixtures, including any raw live-handshake
   JSONL, before the final production/AIO protection snapshot. Do not call
   configured-check absence a CI pass.

## Delivery

The only successful outcome is `role_routing_core_ready`; otherwise use
`blocked`. Success does not establish the M2-B live wait gate, automatic-route
readiness, milestone 3 readiness, production installation, AIO adoption, or
release readiness.

Before handoff to main:

1. Complete required deterministic tests, retained regressions, temporary
   installs, protection checks, static preparation, bounded live handshake, and
   two byte-identical final evidence generations.
2. Write `delivery.md` with fixed base, synchronized main, implementation and
   evidence commit, PR, exact validation, test matrix, bundle/role/Skill/context
   digests, migration facts, deviations, and residual risks.
3. Commit and push, update the PR body, mark it Ready for a successful outcome
   or keep it Draft when blocked, and verify the live remote head equals the
   final local 40-character head.
4. Report outcome, fixed head, implementation/evidence commit, bundle/evidence
   digests, test totals, PR/check reality, protected-surface result, and every
   unmet condition.
5. Stop only after complete fixed-head delivery for independent acceptance. Do
   not accept, merge, clean the worktree/branch, start M2-B, enable automatic
   routing, or launch another task.
