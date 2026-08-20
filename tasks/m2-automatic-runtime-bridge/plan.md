# GKD-M2-C Plan

## Goal

Close the narrow gap between the accepted automatic-route policy and an actually launchable, claimable custom executor. The result must let a fresh trusted main stage the fixed execution bundle, spawn one exact `gkd_executor`, convert the direct host spawn result into trusted activation, and claim the exact task envelope without a production installation.

## User Decisions

- Use one final manual top-level GPT-5.6 Sol/xhigh execution session for this bootstrap repair. Stop before independent acceptance and merge.
- Preserve the accepted M2-A role/config/activation design and M2-B native one-hour wait decision. Do not repeat their historical probes.
- Do not use generic worker fallback, nested CLI agents, model downgrade, session transcript evidence, or a production installation.
- Keep the bridge small and workflow-focused; same-user malicious tampering is outside scope.
- M3 is already split into M3-A fixed-head CI/policy, M3-B resource/data-protection core, and M3-C review/new Skills. Implement none of those here.

## Behavior And Defaults

- Manual remains the default route. Automatic is explicit and requires all six existing route gates plus a persisted decision digest.
- The execution bundle is the already accepted runtime used to stage role/config/Skills and claim the task. The candidate output bundle is implementation output and may change without changing the running executor identity.
- Project staging is deterministic and explicit. It never discovers or edits production paths implicitly and never copies provider/auth/session state.
- Trusted main owns host spawn verification, activation, claim, waiting, acceptance routing, and cleanup. Executor owns implementation and delivery only.
- Any unavailable role, project conflict, digest drift, offer expiry, spawn mismatch, activation failure, or claim CAS failure ends automatic startup without retrying another role or falling back.

## Scope

- Canonical project-role stager and verification command/library for a supplied source bundle and explicit non-production Git project root.
- Minimum project registration, exact `gkd_executor` TOML, parent main Skill and executor Skill set, inventory, modes, digests, idempotence and recovery.
- Generic direct host-spawn fact model and main-only activation/claim bridge using `TrustedMainActivationAuthority` and `TaskService`.
- Route decision digest binding in automatic offer/handoff/claim validation.
- Execution-bundle versus candidate-output-bundle schema and lifecycle semantics.
- Dedicated contracts, evidence, documentation correction, canonical manifest/lock and retained regressions.

## Non-Goals

- M3 CI/resource/scanner/review implementation, production installation, AIO adoption, GitHub settings, paid services, tags, Releases, or public sandbox initialization.
- OS-level privilege separation, signatures, keys, daemon, IPC, transcript/session parsing, authentication inspection, or alternate Codex home.
- Executor acceptance/merge/cleanup authority, multiple executors, another custom role, or a built-in worker.
- New package dependencies, Rust/frontend builds, large local caches, or a real one-hour wait.

## Acceptance Criteria

- Every requirement AC has positive, negative, and where material mutation coverage.
- The bridge can be exercised end to end in temporary Git/worktree/project fixtures using fixed clocks/nonces and fake direct host spawn results; the real custom role is not used to self-certify this task.
- Staged project output is canonical, minimal, byte-identical across roots, and leaves candidate Git clean.
- Successful automatic claim is impossible without the persisted exact route decision and trusted-main bridge; public candidate surfaces remain fail-closed.
- Existing M1/M2 contracts remain green and evidence/protected-surface results are reproducible.

## Compatibility

- Preserve existing task, offer, runtime, activation, claim receipt, journal, delivery and acceptance records through an additive versioned extension where needed.
- Preserve the existing role names, model/effort/sandbox/runtime, M2 bundle digest history and manual route behavior.
- Existing M2-A evidence remains historical; new generic spawn facts must not reinterpret or rewrite the handshake evidence.
- Project staging must use current Codex project custom-agent and Skill formats without writing machine-specific paths into tracked canonical output.

## Security And Data

- Treat the bridge as trusted-main workflow authority, not same-user security isolation. Role context and supported interfaces enforce normal use; private API abuse and direct runtime modification remain explicit non-goals.
- Do not read or store auth files, cookies, tokens, session databases, rollout JSONL, prompt text, transcript text, environment secrets, or production configuration contents.
- Commit only deterministic synthetic fixture identities and path-minimized evidence. Real runtime identifiers/capabilities remain machine-local.
- Reject credential-shaped inputs and redact errors without broadening into a Cyber platform.

## Migration

- No production migration. The stager targets an explicit disposable or project-development root and supports verify, idempotent refresh, exact preimage restore, and clean removal of owned files.
- Existing conflicting unowned `.codex` files fail closed. Do not overwrite user/project configuration that is not recorded in the stager inventory.
- Future execution-bundle upgrades require a separately accepted digest and explicit restaging; candidate output does not trigger an implicit runtime upgrade.

## Public Interfaces

- Add one canonical main-only staging/verify interface and one main-only automatic activation/claim interface. Exact command names may be selected during implementation but must be stable and machine-readable.
- Extend automatic offer/route records with a versioned route-decision binding and execution bundle identity.
- Keep `gkd-task claim` and `gkd-role activation-record` candidate-facing behavior fail-closed unless invoked through the supported main-only context.
- Produce a short fresh-main launch instruction from deterministic output rather than a hand-written machine path.

## Execution Route

- This repair uses a manually opened independent top-level session because the current parent cannot discover a role that was not staged at session start and the missing bridge prevents trusted automatic claim.
- The execution session may not delegate implementation or use a generic worker. It implements, tests, commits, pushes, opens/updates the task PR, and stops at fixed-head delivery.
- After acceptance, main stages the accepted execution project and starts a fresh main; only then may M3 use automatic routing.

## External Side Effects

- Allowed: this task worktree/branch/PR, temporary Git repositories/worktrees/project roots, fake host facts, standard GitHub task PR operations, and read-only official documentation checks.
- Forbidden: production `~/.codex`, AIO writes, credentials/sessions, GitHub settings/Secrets/runners/billing changes, tags/Releases, sandbox repository changes, dependency installation and large builds.

## Action Mode

- Use `implement_and_merge_on_acceptance` under the existing `gkd_core_implementation` authorization.
- Execution may commit, push, update/ready the task PR, and repair in-scope failures. It must not accept or merge its own head.
- Main independently reviews the exact delivered head and conditionally merges only with no blocking finding.

## Implementation Notes

- Reuse `roles.py`, M2 staging fixture shapes, `TrustedMainActivationAuthority`, `TaskService`, route/wait state and transaction primitives; promote behavior into canonical payload rather than importing from tests.
- Prefer a small main Skill script/library with strict JSON input over a new service. Keep the main-only semantic boundary explicit in role context and tests.
- Make route-decision and execution-bundle fields additive/versioned and cover old records in compatibility tests.
- Do not solve M3 or production installation while touching adjacent role and Skill packaging.
