# GKD-M2-D Plan

## Goal

Add the missing deterministic rejection/rework transaction between a delivered fixed head and a new authorized execution attempt, so post-delivery CI or independent-review findings can be repaired without rewriting history or bypassing single-writer state.

## User Decisions

- This is an authorized prerequisite to continuous automatic M3/M4/M5 execution, not a manual bootstrap exception.
- Use the existing accepted execution bundle and one exact automatic `gkd_executor` for implementation; trusted main remains the only rejection, acceptance, merge, and cleanup owner.
- Preserve every old delivery/claim/offer fact and use a new epoch/offer/activation/claim for repair.
- Keep the task generic and minimal; do not implement any M3 product surface.

## Behavior And Defaults

- Delivery remains frozen and writerless. A failed CI or review does not itself mutate state; trusted main supplies one canonical rejected review and exact live PR snapshot to the narrow rework interface.
- Rework is explicit, fixed-head, fail-closed, and atomic. It returns to planning only after all existing trusted acceptance identity/receipt/authorization gates and new rejection gates pass.
- Approval and implementation/action authorization survive only because the material plan is unchanged; rejection cannot silently authorize a changed plan.
- The old attempt remains immutable historical fact. No capability, activation, claim, delivery, finding, or review is overwritten or reused.

## Scope

- Versioned task lifecycle/state additions for rejection and retired delivery history.
- Trusted-main fixed-tree rejection/rework library and CLI surface using the existing review and subprocess GitHub adapter boundaries.
- Exact CAS/transaction/journal behavior, replay/concurrency/recovery and new-offer/new-claim tests.
- Repository verifier, deterministic evidence, docs/Skills, source inventory and generated manifest/lock.

## Non-Goals

- M3-A code or PR repair, CI policy/monitor/workflow, resource/scanner/review Skills, M4 finalization, M5 release, or consumer integration.
- Generic workflow engine, arbitrary rollback, force-reset, claim resurrection, executor rejection authority, or same-user security isolation.
- GitHub writes other than the separately authorized task PR and final conditional merge after acceptance.

## Acceptance Criteria

- Every requirement AC has positive/negative coverage and material mutation tests.
- A real temporary bare origin/worktree plus fake GitHub proves delivered rejection, exact history preservation, new epoch/offer/automatic claim/redelivery, and eventual normal acceptance.
- Rejection failure and replay leave tracked/runtime bytes unchanged; interrupted committed transitions recover deterministically.
- Existing task-core, role-routing, runtime-bridge, foundation, watcher-core and live-negative behavior remains green.
- The versioned verifier runs the approved short suite from an explicit base without dependencies or large artifacts.
- Evidence is deterministic and protected surfaces remain unchanged.

## Compatibility

- Preserve existing schema-v1 tasks and every accepted M1/M2 record. Additive fields/versioning must keep old delivered and accepted tasks readable.
- Existing successful acceptance and merge behavior, public candidate claim fail-closed behavior, route/activation receipts, manual default, and execution/output bundle separation remain unchanged.
- Rework is unavailable for planning, awaiting-claim, implementing, accepted, completed, blocked, dirty, drifted, or legacy records that cannot satisfy the new exact gates.

## Security And Data

- Treat review and GitHub snapshot as untrusted structured input. Require canonical strict fields and stable path-free errors; never emit raw API bodies, credentials, capabilities, agent/thread identities, prompts, or transcripts.
- Reuse the existing same-OS-user workflow authority model; do not add keys, signatures, daemon, IPC, auth/session inspection, or general security functionality.
- Keep real runtime identities machine-local and exclude them from deterministic evidence.

## Migration

- No production migration. Existing tasks are read compatibly; only a new trusted rework call writes the additive rejection history.
- No automatic conversion of delivered tasks. PR #8 will be reworked only after this bundle is independently accepted, installed to a new isolated temporary root, project-verified, and explicitly invoked by trusted main.
- Project staging may be refreshed later from the accepted digest; this task does not modify current machine-local staging.

## Public Interfaces

- Add one trusted `gkd-task` rejection/rework command or equivalent supported library path with explicit trusted root, candidate root, task path, repository, PR, full candidate head, canonical review, trusted GitHub adapter, runtime root, and actor role.
- Extend strict task state/schema with additive rejected-attempt history and one deterministic machine result.
- Add `scripts/gkd-verify --base-sha <full-sha>` as the repository-approved local verification entry; do not add an Actions workflow in this task.

## Execution Route

- Trusted main bootstraps, approves, routes, prepares and claims through the accepted automatic bridge, then waits through the approved one-hour loop.
- Executor implements only this prerequisite, runs the versioned verifier, commits/pushes one task PR, writes delivery, and stops at a fixed head.
- Trusted main independently reviews the fixed head and merges only if all applicable local evidence and live PR facts pass; there are no configured policy-backed checks before M3-A is accepted.

## External Side Effects

- Allowed: this task worktree/branch/PR, read-only GitHub facts, in-scope commits/pushes/PR updates, temporary Git/fake-GitHub/evidence roots, and one conditional merge after independent acceptance.
- Forbidden: PR #8 writes, production `~/.codex`, AIO, sandbox, paid runner, Secrets, repository settings, branch protection, workflow dispatch/rerun/cancel, tags, and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review`, and `conditional_merge`.
- Executor owns all except conditional merge; trusted main owns review, rejection/rework calls on later tasks, merge, archival and cleanup.

## Implementation Notes

- Reuse `validate_review`, fixed candidate receipt validation, `SubprocessGitHubAdapter`, task transactions, state finalization and retired-claim patterns rather than creating a second authority.
- Model rejection as a durable immutable attempt record and clear only active pointers. Keep old activation/claim receipts available for historical validation.
- Add the verifier without copying M3-A policy or workflow code; M3-A will extend the verifier after this task merges.
