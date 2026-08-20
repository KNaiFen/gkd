# GKD-M2-I-R Plan

## Goal

Re-deliver the existing generic M2-I trusted-host recovery bridge on the current M2-J main base with the corrected delivery sequence.

## User Decisions

- Use one exact accepted `gkd_executor` with no substitution, retry, reuse, downgrade, or fallback.
- Limit the task to M2-I lifecycle repair and legal redelivery; do not edit M3 candidates or implement M3 features.
- Preserve existing state, authorization, receipt, rework, fixed-bundle and one-hour wait contracts.

## Behavior And Defaults

- Preserve the M2-I deterministic host task-name and trusted terminal-reclaim behavior unchanged.
- Keep ambiguity, drift, replay, active status and malformed input fail-closed before writes.
- Public candidate surfaces remain unable to activate, claim, terminate or reclaim automatic execution.

## Scope

- Port commit `27cf3293d6cc37c4f19a0b96d934d4b6c079db01` and its focused tests onto current main.
- Resolve only mechanical M2-J manifest/documentation conflicts.
- Commit the delivery document before the final state transition and bind its exact path and digest.

## Non-Goals

- Host agent management, retries, fallback, concurrent execution, new services, M3 product work, production/AIO changes, release work, or historical probes.

## Acceptance Criteria

- M2-I implementation and focused evidence pass on current main.
- Existing short contracts and M2-J delivery sequencing pass through the repository verifier.
- Evidence is deterministic, path-minimized and protected-surface neutral.

## Compatibility

- Preserve role/model/effort/sandbox/runtime values, task and receipt schemas, and current CLI failure behavior.
- Do not include old M2-I task-state or delivery commits.

## Security And Data

- Validate host results at the bridge boundary and retain only canonical binding facts.
- Never persist raw final messages, prompts, transcripts, credentials, environment, capability, or raw thread identity.

## Migration

- No production or consumer migration. This task exists only to legally redeliver the M2-I implementation after the generic M2-J contract fix.

## Public Interfaces

- Preserve the M2-I trusted-main bridge interfaces and candidate/public fail-closed boundaries.
- Do not add a public automatic CLI writer.

## Execution Route

- Trusted main registers/approves the task, obtains all six gates, calls `prepare`, spawns once with exact returned task name and `fork_turns=none`, normalizes the real spawn, claims, and waits through one-hour `wait_agent` calls.
- Executor uses only its registered worktree, implements/verifies/pushes/maintains one PR, writes delivery in the required order and stops at a fixed head.
- Trusted main independently accepts and conditionally merges.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions from committed files, read-only GitHub observations, in-scope CI repair and isolated evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, unrelated PRs, sandbox changes, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review` and `conditional_merge`; only trusted main merges.

## Implementation Notes

- Use the prior M2-I implementation commit as the source of truth; preserve M2-J changes when resolving conflicts.
- Commit only `tasks/m2-host-recovery-bridge-redelivery/delivery.md` for the delivery-document commit, then invoke `gkd-task deliver` with its exact digest and stop.
