# GKD-M1-A: Deterministic Task Core

## Sole Entry For The Execution Session

In a new top-level Codex session opened in this task worktree, send only the
launch prompt produced by main. That prompt must require this file,
`requirements.md`, and `plan.md` to be read in full before any implementation.

The execution session must use GPT-5.6 Sol with `xhigh` reasoning. It is a
manually opened top-level execution session, not main and not a writable
subagent. It must stop after the Draft PR is ready for independent fixed-head
acceptance. It must not accept, merge, start milestone 2, or start another
session.

## Task Identity

- Status: `awaiting_manual_execution`
- Task: `GKD-M1-A`
- Repository: `KNaiFen/gkd`
- Base branch: `main`
- Task branch: `task/m1-deterministic-task-core`
- Fixed base SHA: `1335ac6a9a4dbb5c63570f5a02ba9e713705eebd`
- Draft PR: pending creation by main
- Plan: `tasks/m1-deterministic-task-core/plan.md`, version 1
- Requirements: `tasks/m1-deterministic-task-core/requirements.md`, version 1
- Route: manual top-level execution session
- Action mode: `implement_and_merge_on_acceptance`

The worktree's absolute path is launch-time machine state. It is supplied by the
main handoff prompt and must not be written into tracked task state, source,
evidence, or archive.

## Required Reading

Before any command that changes files, read completely:

1. root `AGENTS.md` and `VISION.md`;
2. `.agents/context.md`, `.agents/decisions.md`, and `.agents/open-items.md`;
3. this task's `requirements.md`, `plan.md`, and `execution.md`;
4. the approved GKD core implementation plan and its plan index from the
   read-only planning source supplied in the launch prompt;
5. the exact canonical foundation files that will be changed.

Legacy consumer code may be inspected read-only for behavioral evidence, but it
is not an implementation source of truth and must not be modified.

## Bootstrap Exception

This task creates the deterministic CLI and therefore cannot dogfood it. Do not
handwrite a coordination `task.json`, offer, claim, authorization JSON, journal,
or evidence result for this task. Do not run the candidate `gkd-task` to claim,
deliver, accept, or merge this same PR. The existing Git/manual process remains
the only authority for M1-A.

All future behavior of the new core must nevertheless be implemented and tested
through generated fixture state. Candidate self-test success is not acceptance;
main will later review and reproduce it from a fixed head.

## Authorization And Hard Boundaries

The user has granted `gkd_core_implementation`. This execution session may:

1. modify only this task worktree within the approved M1-A file scope;
2. use Python standard library, Git, temporary directories, local subprocesses,
   and fake GitHub executables/services for L1/L2 contracts;
3. commit and push the task branch, update its existing Draft PR, perform
   task-related CI repair within the frozen plan, and mark the PR ready;
4. read current repository/PR facts needed to deliver a fixed head.

It must not:

1. modify or install to production user configuration;
2. modify a consumer repository, the GKD sandbox repository, GitHub settings,
   Secrets, runners, billing, branch protection, tags, or Releases;
3. install dependencies, run large builds, run Rust/Tauri/frontend builds,
   invoke paid APIs, or create large local caches/artifacts;
4. run the historical live watcher probe or claim that old watcher outcomes
   changed;
5. define milestone 2 roles/routing/wait logic or milestone 3+ CI, resource,
   review, finalization, or release behavior;
6. use a writable subagent for investigation, design, implementation, testing,
   review judgment, or delivery;
7. accept or merge its own PR, even though the approved action mode permits a
   later independent trusted main/acceptor to merge after all gates pass.

If a material requirement, plan field, public interface, security/data boundary,
execution route, or external action must change, stop with `blocked` and describe
the proposed plan delta. Do not edit `plan.md` to manufacture approval.

## Startup Gates

1. Confirm current Git root is the registered task worktree, current branch is
   exactly `task/m1-deterministic-task-core`, origin is the canonical repository,
   and the fixed base is an ancestor.
2. Confirm the worktree is clean and the Draft PR head/branch/base match this
   task. Confirm GPT-5.6 Sol and `xhigh`; stop rather than downgrade.
3. Fetch `origin/main`. It may differ from the fixed base only by main-session
   task-registration records under `.agents/`. Inspect every commit and path.
   Unknown or product-code drift is a blocker. If only the allowed coordination
   record exists, merge it and record the actual synchronized main SHA in
   `delivery.md`.
4. Run the existing foundation 53-test runner, watcher-core 47-test runner, and
   watcher-live 15 negative tests before changing product code. Do not run the
   four-scenario live probe.
5. Verify production user surfaces are unchanged before implementation using a
   path-free digest/snapshot method. Temporary tests may only write inside
   explicit system temporary roots and fixture repositories.

## Implementation Contract

Implement every requirement and technical choice in the adjacent planning
files. In particular:

1. Add the separately installed `gkd-task` executable, standard-library task
   package, and strict task/runtime/offer/authorization schemas. Keep
   `gkd-bundle` public behavior compatible.
2. Implement versioned requirements/plan/implementation gates and material
   approval invalidation. All machine state and digests are CLI-generated.
3. Implement explicit-base clean-main bootstrap, candidate-only active truth,
   trusted-code/fixed-tree-candidate-data boundaries, portable locator,
   machine-local attachment, lifecycle doctor, and idempotent v1 migration.
4. Implement execution offer, one-time capability, atomic claim, revoke,
   evidence-backed reclaim, block/resume, delivery, task-level action
   authorization, and trusted fixed-head acceptance/conditional merge.
5. Implement task lock, state/head/revision CAS, prepared transaction journal,
   exact recovery, and `transaction_in_doubt` freeze. Never use broad Git
   destructive recovery.
6. Keep repository policy as explicit input. Do not embed a consumer name/path,
   `main` as a universal base, required check names, merge method, runtime path,
   or machine/user identity in canonical code.
7. Keep plaintext capabilities and machine paths outside Git and all evidence.
   Error and status JSON must be canonical, strict, stable, path-free, and
   credential-free.

## Required L1 Contracts

Cover at least these contract groups with positive, negative, and mutation
tests, mapped by stable IDs in the evidence runner:

1. strict schemas, canonical bytes, unknown fields, direct tamper, digest drift,
   and deterministic fixture clock/nonce behavior;
2. all legal/illegal requirements, plan, authorization, lifecycle, block/resume,
   offer, claim, revoke/reclaim, delivery, acceptance, and completion
   transitions;
3. plan document versus material digest behavior and invalidation for every
   material section;
4. authorization binding across task, repository, base branch/SHA, task branch,
   plan version/digest, mode, and action allowlist;
5. capability hash-only persistence, replay/expiry/revocation/epoch behavior,
   wrong role/config/route/action/head rejection, and zero secret output;
6. lock/CAS behavior, injected failures before/after state write and Git commit,
   exact recovery, unrelated-file preservation, and uncertain freeze;
7. one `authorization_mismatch` with zero external call, retry, alternate
   command, or replacement offer;
8. doctor static/live/historical composition and v1 migration idempotence.

Mutation tests must demonstrate failure when material invalidation, first-writer
claim, capability consumption, exact expected head, trusted-code isolation,
action scope, or no-retry behavior is removed.

## Required L2 Contracts

Use real temporary bare remotes/clones/worktrees and concurrent subprocesses:

1. Bootstrap from an explicit fetched full SHA; create exactly one branch and
   worktree; write task facts only in the candidate; keep main clean and not
   ahead of origin.
2. Reject bootstrap from main, dirty main/candidate, stale/nonexistent base,
   duplicate branch/worktree, or a second writable task fact source.
3. Exercise each locator layer. Reject zero/multiple matches, symlink/traversal,
   wrong repo/common-dir/branch/task, stale/tampered attachment, and any guessed
   directory selection.
4. Prove handoff can render a local absolute path without changing any tracked
   byte. Scan tracked task documents/JSON for the fixture path.
5. Prove active and archived v1 migrations, repeat idempotence, deleted archive
   worktree behavior, attachment/session cleanup, and active missing-worktree
   failure.
6. Launch concurrent claim subprocesses and prove exactly one winner, one claim
   commit, no lost update, and permanent rejection of the losing/stale launch
   envelope.
7. Tamper with candidate CLI/modules and prove trusted acceptance still runs
   trusted code and reads only explicit fixed-tree candidate data.
8. With fake GitHub behavior, reject wrong repo/base/PR/head, missing/failed
   required checks, missing independent acceptance, executor merge, authorization
   mismatch, dirty/drifted candidate, and merge-time head change.
9. Prove one conditional exact-head merge call. For timeout/transport ambiguity,
   reconcile only exact-head merged success and never replay the merge request.
10. Prove policy inputs vary across at least two generic repository identities;
    no fixture-specific identity/check/branch leaks into the canonical core.

## Packaging, Regression, And Evidence

1. Add every payload file to `canonical/source.toml`; generate manifest/lock only
   through `gkd-bundle generate`.
2. Install into two independent temporary targets, verify the same development
   version/content digest/owned file inventory, and exercise installed
   `gkd-task`. Preserve the installer's temporary-only boundary.
3. Run all task-core L1/L2 contracts, foundation 53, watcher core 47, watcher
   live-negative 15, and `git diff --check`. Do not run live canary/probe.
4. Generate task-core evidence twice in separate clean temporary roots with
   controlled fixture clock/nonces. The committed evidence must match both runs
   byte for byte and list the exact stable test IDs and contract groups.
5. Scan source, installed payload, tracked task records, and evidence for
   machine paths, plaintext capabilities, credential-shaped values, secrets,
   consumer-specific identity/policy, and undeclared files.
6. Confirm the production protection snapshot is unchanged and all temporary
   fixture roots are removed before evidence publication.
7. If GitHub has no configured required checks, record
   `required_checks_not_configured_bootstrap`; do not call that CI success.

## Expected Files

- `canonical/payload/bin/gkd-task`
- `canonical/payload/lib/gkd_task/**`
- `canonical/payload/schema/task/**`
- generated `canonical/manifest.json` and `canonical/manifest.lock.json`
- `canonical/source.toml` and minimal canonical documentation updates
- `tests/task_core/**`
- `evidence/m1-deterministic-task-core/**`
- `tasks/m1-deterministic-task-core/delivery.md`
- task-state updates under `.agents/**`

Do not rewrite historical watcher or milestone 0 evidence. Do not put task-core
tests into the foundation discovery directory.

## Delivery

The only successful outcome is `deterministic_task_core_ready`; otherwise use
`blocked`. Success does not imply auto-route, role, wait-loop, CI monitor,
production, release, or consumer readiness.

Before handoff back to main:

1. Complete all required validation and deterministic evidence generation.
2. Write `delivery.md` with outcome, fixed base, synchronized main SHA,
   implementation/evidence commit, PR, exact commands, test counts, contract
   matrix, development bundle version/content digest, evidence digest, protected
   surface proof, changed files, deviations, and residual risks.
3. Commit with short specific Chinese messages, push the task branch, update the
   Draft PR body, and mark the PR ready for review.
4. Verify the worktree is clean and the remote PR head equals the full local
   40-character head. Report that head, implementation/evidence commit, outcome,
   test totals, bundle/evidence digests, PR state, configured-check reality, and
   every unmet condition.
5. Stop. Do not accept, merge, modify main, clean the worktree/branch, start
   milestone 2, or launch another session.
