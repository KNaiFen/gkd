# GKD-M2-E Plan

## Goal

Make automatic executor task names attempt-aware so a legal delivered rework can create a fresh direct host spawn without colliding with the terminal executor from the rejected attempt.

## User Decisions

- Use only the accepted automatic bridge and one exact `gkd_executor`; no generic worker, role/model substitution, reuse, downgrade, nested execution, or fallback.
- Keep this a prerequisite bridge correction. M3-A candidate code and PR #8 are not modified by this task.
- Preserve the accepted rework transaction and all fixed role/config/bundle/wait bindings.

## Behavior And Defaults

- The bridge derives the task name from canonical durable attempt facts already available after offer creation.
- A name is stable for one prepared offer and different for a later epoch of the same task.
- The exact name returned by `prepare` is the only name accepted by `claim`.
- Any ambiguity or mismatch fails closed before trusted activation or claim writes.

## Scope

- Adjust the trusted runtime bridge task-name derivation and its spawn-result validation context.
- Add focused positive, negative, mutation, recovery, and rework integration tests.
- Update only the minimum bridge/main/executor documentation, evidence declarations, manifest, and lock required by the change.

## Non-Goals

- Host agent deletion or reuse, spawn retries, concurrent executors, fallback names, public automatic activation/claim, M3 product functionality, production installation, AIO changes, or release work.

## Acceptance Criteria

- Every requirements AC has a direct contract, including a real task state sequence that archives a delivered attempt and prepares a new offer.
- Existing automatic bridge and M2-D acceptance/rework tests remain unchanged in outcome.
- The repository-approved verifier runs all retained short contracts with no dependency installation or large artifacts.
- Evidence is deterministic and path-minimized; protected surfaces and task candidates outside this task do not drift.

## Compatibility

- Preserve role names, model/effort/sandbox/runtime values, schemas except additive changes strictly required for name binding, existing task states, receipts, and public CLI failure behavior.
- Existing in-flight offers remain bound to the bridge version that created them; adoption occurs only after accepted bundle installation and a fresh offer.

## Security And Data

- Use only canonical task/offer attempt facts in the task name and enforce a conservative host-safe character/length contract.
- Never include raw agent/thread identity, capabilities, nonces, paths, usernames, credentials, prompts, transcripts, or environment data.

## Migration

- No production or consumer migration. After merge, trusted main installs the accepted bundle in the existing isolated temporary staging flow, revokes any unclaimed old-format offer, and prepares a fresh offer.

## Public Interfaces

- `TrustedMainRuntimeBridge.prepare` continues returning `spawnRequest.taskName`; its value becomes attempt-aware.
- `TrustedMainRuntimeBridge.claim` continues consuming the normalized host spawn result and requires exact equality with the prepared value.

## Execution Route

- Trusted main creates and approves this task through accepted `gkd-task`, obtains all six automatic gates, calls `TrustedMainRuntimeBridge.prepare`, performs one direct exact `gkd_executor` spawn with the returned task name and `fork_turns=none`, normalizes the real result, and completes exact claim.
- Executor works only in this task's registered worktree, verifies, commits, pushes, maintains one PR, repairs in-scope CI, writes delivery, and stops at a full fixed head.
- Trusted main independently reviews and conditionally merges the exact delivered head.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard GitHub Actions caused by committed repository files, read-only GitHub observations, in-scope CI repair, and isolated temporary evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, repository settings, unrelated PRs, sandbox changes, tags, and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review`, and `conditional_merge`; only trusted main may perform the conditional merge.

## Implementation Notes

- Prefer deriving the attempt suffix from validated state/offer fields already held by the bridge rather than adding a new registry or host probe.
- Keep the implementation small and use the existing canonical validation/digest helpers.
- Prove the exact name through `prepare` and `claim` tests instead of relying on an executor statement.
