# GKD-M2-D Requirements

## Goal

Close the deterministic lifecycle gap exposed by GKD-M3-A: an executor must stop after delivery, but only the delivered pull-request head can produce the final CI and acceptance result. Add a trusted-main fixed-head rejection/rework transition that preserves all prior facts and safely permits a new automatic offer and claim.

## User Decisions

- The user has explicitly authorized continuous automatic execution through M3, M4, and M5, including this minimal prerequisite repair without further confirmation.
- Use exactly one accepted `gkd_executor` for this task through the existing six-gate automatic route. No worker, alternate role, model downgrade, nested Codex, or fallback.
- Keep the repair generic and deterministic. Do not special-case PR #8, GKD-M3-A, a repository owner, check name, workflow, username, or machine path.
- Use `implement_and_merge_on_acceptance`. Executor may commit, push, maintain one task PR, repair in-scope failures, and ready it; only trusted main may accept and merge.
- Production `~/.codex`, AIO, paid runners, Secrets, repository settings, tags, Releases, and M3 policy/resource/review product functionality remain outside this task.

## Scope

- Add a trusted fixed-head rejection/rework interface for a clean candidate in `delivered` phase, invoked from a clean synchronized main context with an explicit candidate worktree, task path, repository, PR number, full current head, and canonical independent rejected review.
- Validate candidate identity, current delivered state, exact PR/base/head facts, action authorization, claim/activation receipts, review task/head/reviewer independence, non-empty findings, and candidate cleanliness before mutation. Never execute candidate code.
- Atomically preserve the old offer, claim, delivery, route/bundle bindings, review digest, findings digest, rejected head, PR, and timestamp in durable history; revoke the old offer, clear active delivery/claim/offer/writer, increment epoch, and return to authorized planning for a new offer.
- Keep requirements/plan approval and implementation/action authorization only when their bound material contract still matches. Any drift continues to fail closed.
- Add strict versioned state/schema validation, transaction/CAS/journal recovery, CLI/library integration, fixed-tree and fake-GitHub L1/L2 tests, mutation coverage, deterministic evidence, documentation, manifest/lock regeneration, and a repository-versioned local verifier entry.
- Update only the minimum GKD Skills needed to describe rejection/rework ownership and executor stop boundaries.

## Non-Goals

- Editing, reopening, merging, closing, or otherwise changing PR #8 or its candidate files in this task.
- Implementing `.gkd` CI policy, GitHub monitor, Actions workflow, resource/scanner logic, review Skills, finalization state machine, release logic, or consumer adapters.
- Allowing executor self-rejection, executor acceptance, executor merge, force-push history rewrites, hand-edited task state, or reuse of a consumed claim.
- Treating rejection as acceptance, deleting rejected history, automatically changing material requirements/plan, or retrying the same activation/offer.
- Production installation, AIO changes, dependency installation, large builds/caches, historical live probes, or M2-B experiments.

## Acceptance Criteria

1. Only trusted main/acceptor context can reject a clean exact delivered candidate; executor or candidate-facing misuse fails before tracked/runtime writes.
2. Rejection requires an explicit full current candidate head and live PR snapshot whose repository, number, base branch, task branch, and head all match the delivered task. Drift, draft/closed/merged ambiguity, or malformed external facts fail closed.
3. The canonical review must bind task ID and current head, have outcome `rejected`, contain at least one stable non-empty finding, and be independent from the claim session. Accepted, empty, wrong-task/head, duplicate, credential-shaped, or claim-self reviews fail closed.
4. The transition revalidates the fixed candidate, action authorization, claim receipt, activation receipt, execution bundle, route decision, delivery claim and candidate output digest exactly as trusted acceptance does.
5. Success atomically records one rejection/rework history entry, revokes the old offer, retires the old claim/delivery, increments epoch, clears active writer/offer/claim/delivery/acceptance, and returns to `planning` with valid approval and implementation/action authorization.
6. A fresh automatic offer/bridge claim after rework succeeds only with a new offer, envelope, activation, claim, epoch, and current execution bundle; all old capabilities, envelopes, receipts, activations, and claim IDs are unusable but retained as historical evidence where required.
7. Concurrent or replayed rejection has exactly one winner. Pre-commit failure restores exact bytes; committed interruption is recoverable without duplicate history or lost old facts; stale head/revision/review/PR observations write nothing.
8. Rework never changes implementation files, requirements, plan, authorization, unrelated files, Git history, remote PR metadata, or main. It stages only declared coordination files and produces canonical path-free output.
9. Existing acceptance of a successful delivered head remains unchanged. Rejected state cannot be accepted until a new claim and delivery complete.
10. The repository gains one versioned zero-dependency local verification entry accepting an explicit full base SHA, verifying ancestry, and running the new task-core tests plus all retained M1/M2 short contracts without historical live probes or large artifacts.
11. Two clean evidence generations are byte-identical, candidate output bundle digest is separate from the accepted execution bundle, protected production/AIO surfaces do not drift, and the temporary roots finish clean.
12. The complete versioned verifier and dedicated mutation tests pass; canonical source, manifest, lock, README and relevant Skill contracts accurately describe the new boundary without claiming M3 completion.
