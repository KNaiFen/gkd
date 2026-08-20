# GKD-M2-H Plan

## Goal

Make automatic attempts host-name unique and give trusted main a narrow exact-terminal reclaim bridge so real child failures remain recoverable without weakening candidate boundaries.

## User Decisions

- Use one exact accepted `gkd_executor` with no substitution, retry, reuse, downgrade, or fallback.
- Limit the task to trusted runtime lifecycle repair; do not edit M3 candidates or implement M3 features.
- Preserve existing state, authorization, receipt, rework, fixed-bundle and one-hour wait contracts.

## Behavior And Defaults

- Attempt names derive only from validated canonical task/offer context and are stable for that offer.
- Trusted terminal reclaim accepts one minimal normalized host result after child final/error and validates every active binding.
- Ambiguity, drift, replay, active status or malformed input fails closed before writes.
- Public candidate surfaces remain unable to activate, claim, terminate or reclaim automatic execution.

## Scope

- Private task-name derivation and exact spawn-result expectation in `TrustedMainRuntimeBridge`.
- Trusted-main-only terminal normalization/reclaim method and one-shot evidence provider.
- Focused tests, mutations, Skills/docs, evidence, manifest/lock and verifier integration.

## Non-Goals

- Host agent management, retries, fallback, concurrent execution, new services, M3 product work, production/AIO changes, release work, or historical probes.

## Acceptance Criteria

- Every requirements AC has positive and negative contracts, including real rework/new epoch and terminal reclaim/new epoch sequences.
- Old implementation fails the new name and terminal-boundary tests.
- Existing short contracts pass through the repository verifier without dependency installation or large artifacts.
- Evidence is deterministic, path-minimized and protected-surface neutral.

## Compatibility

- Preserve role/model/effort/sandbox/runtime values, task and receipt schemas unless an additive declared schema change is strictly required, and current CLI failure behavior.
- Existing active claims remain readable; the new bundle is used for trusted terminal reclaim only after acceptance and isolated installation.

## Security And Data

- Validate host results as external input at the bridge boundary and retain only canonical binding facts.
- Never persist raw final messages, prompts, transcripts, credentials, environment, capability, or raw thread identity.

## Migration

- No production or consumer migration. Trusted main installs the accepted bundle in an isolated temp target, refreshes project staging, reclaims the blocked superseded attempt using its real terminal fact, and creates only fresh offers thereafter.

## Public Interfaces

- `TrustedMainRuntimeBridge.prepare` keeps returning `spawnRequest.taskName`, now attempt-aware.
- Add one trusted-main library method for exact normalized terminal reclaim; no public automatic CLI writer is added.

## Execution Route

- Trusted main registers/approves the task, obtains all six gates, calls `prepare`, spawns once with exact returned task name and `fork_turns=none`, normalizes the real spawn, claims, and waits through one-hour `wait_agent` calls.
- Executor uses only its registered worktree, implements/verifies/pushes/maintains one PR, writes delivery and stops at a fixed head.
- Trusted main independently accepts and conditionally merges.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions from committed files, read-only GitHub observations, in-scope CI repair and isolated evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, unrelated PRs, sandbox changes, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review` and `conditional_merge`; only trusted main merges.

## Implementation Notes

- Prefer an offer-ID digest suffix and bounded sanitized task prefix over a mutable registry.
- Implement terminal evidence as a bridge-owned one-shot object compatible with existing reclaim validation; do not expose it from candidate CLI.
- Use existing canonical validators, digests and transaction machinery.
