# GKD-M1-A Requirements v1

## Status

- Task: `GKD-M1-A`
- Requirements: `ready`
- Plan source: approved GKD core implementation plan, milestone 1
- Implementation authorization: `gkd_core_implementation`
- Execution route: manual top-level execution session
- External action mode: `implement_and_merge_on_acceptance`

This task is the bootstrap implementation of the deterministic task core. The
core does not exist yet, so this task is coordinated by reviewed Markdown, Git,
and the existing manual handoff process. It must not create a handwritten
`task.json`, and it must not use candidate code to claim that this same task was
managed by the new core.

## Vision Alignment

- User control: requirements, plan approval, implementation authorization, and
  external actions remain separate facts. A material plan change invalidates
  approval and authorization instead of being inferred from convenience.
- Fixed evidence: every state transition binds the exact repository, branch,
  plan, authorization, state revision, and Git head it was validated against.
- Single fact source and writer: active task state exists only in the candidate
  worktree; the long-lived main checkout remains a trusted control plane.
- Recovery and portability: committed state contains no machine-local path,
  while runtime attachments and journals support safe rediscovery and recovery.
- Minimal process: Agents make open-ended technical judgments, while a narrow
  standard-library CLI owns JSON, digests, transitions, locks, and external
  action gates.

Vision alignment does not grant additional authority. This task remains inside
the approved milestone 1 scope.

## Objective

Deliver the canonical, installable deterministic task core used by later GKD
Skills and roles. The core must make task planning, handoff, claim, delivery,
acceptance, and merge state auditable and fail-closed without embedding a
consumer repository's paths, checks, branch policy, or machine layout.

## Required Behavior

### Requirements, plan, and implementation gates

1. Maintain `requirements_ready`, `plan_approved`, and
   `implementation_authorized` as separate versioned facts.
2. Parse a fixed human-readable planning package and generate all machine state,
   versions, digests, and authorization records through the CLI.
3. Bind approval to a plan version and material-contract digest. Track the full
   document digest separately so internal implementation notes can change
   without silently changing the approved material contract.
4. Treat changes to goal, user decisions, behavior/defaults, scope, non-goals,
   acceptance criteria, compatibility, security/data behavior, migration,
   public interfaces, execution route, external side effects, or action mode as
   material. Such a change invalidates plan approval and implementation/action
   authorization.
5. Allow an explicit user decision to approve only the plan or to approve the
   plan and authorize implementation together. An initial implementation
   request cannot approve a plan that did not yet exist.

### Clean main and candidate trust boundary

1. Bootstrap a formal task only from an explicit full base SHA fetched from the
   canonical remote.
2. Create one task branch and one independent worktree before the first task
   package write. The long-lived main checkout must remain clean and must not
   carry an active task mirror.
3. Require trusted commands to receive or uniquely resolve the candidate root.
   Never select a task by directory name, modification time, or suffix guess.
4. Run acceptance logic from trusted installed/main code. Read candidate files
   from a fixed Git tree as untrusted data; never import or execute candidate
   scripts.

### Portable locator and lifecycle doctor

1. Keep durable task identity free of absolute worktree paths and other
   machine-local values.
2. Store machine-local attachments outside tracked task data and key them by
   canonical repository identity, task ID, and full task branch.
3. Resolve in this order: explicit candidate/worktree, current Git root, unique
   same-common-dir worktree for the full branch, then runtime attachment.
4. Return stable `worktree_missing` or `worktree_ambiguous` errors for zero or
   multiple matches. Revalidate Git root, common dir, repository, branch, task
   identity, and symlink/traversal boundaries after every resolution.
5. Provide static, active/live, and historical/archive doctor modes with
   lifecycle-appropriate checks.
6. Provide an idempotent v1 migration library: active legacy paths migrate to a
   runtime attachment only after validation; archived legacy state remains
   readable when its old worktree no longer exists.

### Execution offer, claim, and transaction safety

1. Planning reaches `awaiting_claim` only through a CLI-generated execution
   offer; at that point writer is null and implementation files are frozen.
2. Bind the offer to task/repository/branch, exact head, route, plan and
   authorization digests, allowed actions, and required role/config digests.
   Role policy remains an opaque input until milestone 2.
3. Generate a one-time claim capability with cryptographic randomness. Commit
   only its digest; keep the secret in machine-local runtime state and out of
   Git, Markdown, logs, errors, evidence, and archive.
4. Make claim first-writer-wins under a task lock and compare-and-swap over the
   exact head, state revision, offer ID, plan digest, and authorization digest.
   Claim success atomically consumes the offer, records verified runtime
   evidence, moves to `implementing`, and produces the claim commit.
5. Make revoke and reclaim permanently invalidate old capabilities and claims.
   Reclaim requires terminal/missing evidence for the old writer and preserves
   that history.
6. Use atomic replacement, directory durability where supported, exact
   preimage/postimage recovery, and a machine-local transaction journal. Any
   state that cannot be proved safe becomes `transaction_in_doubt` and freezes.
7. Stage only the expected coordination files. Never recover with broad reset,
   checkout, clean, or unrelated-file restoration.

### Delivery, acceptance, and merge authorization

1. Delivery requires the current valid claim, a clean candidate, committed
   implementation/evidence, and an exact delivery head. It returns writer
   ownership and freezes the delivered candidate.
2. Persist task-level action authorization bound to task ID, repository, base
   branch/base SHA, task branch, plan version/material digest, mode, and an
   explicit action allowlist.
3. `implement_only` must stop before merge.
   `implement_and_merge_on_acceptance` may allow commit/push/PR update,
   task-related CI repair, ready-for-review, and one conditional merge only.
4. Executor code and executor sessions can never accept or merge. Acceptance
   must run from a trusted synchronized main context against an explicit PR and
   full candidate head.
5. Revalidate candidate identity, delivery, authorization, independent review,
   required checks, PR head/base, and mergeability immediately before the one
   conditional merge call.
6. A runtime authorization refusal returns one `authorization_mismatch`. It
   must not retry, issue a replacement command, broaden the action, or create a
   new offer.
7. An indeterminate merge response may only be reconciled by checking whether
   the exact authorized head was merged. It must never replay the merge write.

### Machine output

1. All coordination JSON is strict, versioned, canonical, and CLI-generated.
   Unknown fields, invalid transitions, noncanonical bytes, stale revisions,
   digest drift, and direct edits must fail closed.
2. Errors are stable, path-free, credential-free machine codes. Normal output
   must not expose capability material, session content, environment secrets,
   machine-local paths, or consumer-specific policy.
3. Clock and nonce sources are injectable only through internal test seams so
   contract evidence is deterministic without weakening production entropy.

## Acceptance Criteria

1. L1 contracts prove every legal and illegal transition, plan invalidation,
   authorization mismatch, one-time capability behavior, journal recovery, and
   direct-state-tamper rejection.
2. L2 temporary bare-origin and real-worktree fixtures prove clean-main
   bootstrap, unique candidate facts, trusted-code/untrusted-data boundaries,
   locator zero/multi-result behavior, v1 migration, and lifecycle doctor.
3. Concurrent subprocess claim tests prove exactly one winner and no lost
   update or state/journal overwrite.
4. Fake GitHub fixtures prove exact-head delivery/acceptance, executor merge
   refusal, required-check and authorization gates, zero retry after refusal,
   merge-time revalidation, and exact-head-only reconciliation after an
   indeterminate response.
5. Mutation tests fail when approval invalidation, lock/CAS, capability
   consumption, candidate-code isolation, action authorization, or merge-head
   checks are removed.
6. The canonical manifest and lock are generated by the foundation CLI; two
   temporary installs have the same version/content digest and expose the new
   task CLI without changing the temporary-only installer boundary.
7. The milestone 0 foundation contracts and all retained M-1 short regressions
   pass. No live watcher probe, dependency installation, large build, or
   production-home write occurs.
8. Machine evidence is generated twice from clean temporary roots and is byte
   identical after controlled clock/nonce fixtures. Tracked source, evidence,
   and installed files contain no machine path, capability, credential, or
   consumer-specific marker.

## Non-Goals

- Defining or installing `gkd_executor`, `gkd_acceptor`, or
  `gkd_ci_reviewer` roles.
- Enabling automatic execution or proving the one-hour/12-hour wait contract.
- Implementing the GitHub CI monitor, repository CI policy, resource presets,
  secret scanner, new review Skills, finalization PR, version release, tag, or
  GitHub Release flow.
- Installing to production user configuration or changing any consumer
  repository.
- Using this task's candidate implementation to claim, deliver, accept, or
  merge this same bootstrap task.
