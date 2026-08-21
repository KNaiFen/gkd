# GKD-M5-A Plan

## Goal

Implement the final verification and release-candidate machinery, leaving live L3/L4 execution and exact-SHA promotion to trusted main after merge.

## User Decisions

- Use one exact automatic `gkd_executor`; no fallback, worker, retry, role/model substitution or nested agent.
- The first stable candidate is `0.1.0`; executor never creates the final tag or Release.
- Trusted main executes the single post-merge L3/L4 pass on the accepted candidate SHA and promotes only after independent acceptance.

## Behavior And Defaults

- L0-L2 run for GKD changes; L3/L4 are release-candidate-only and bind one exact final SHA.
- L4 effects are confined to `KNaiFen/gkd-sandbox`; failures, head drift, unredacted output or missing provenance fail closed.
- Promotion uses one already-built asset set and one matching receipt; retries reconcile rather than rebuild.

## Scope

- Verification layers, traceability, stable release-candidate bundle/metadata, sandbox canary tooling, release evidence and trusted-main promotion inputs.

## Non-Goals

- Production `~/.codex`, AIO, paid runners, Secrets, settings changes, historical custom-role experiments and executor-issued tag/Release writes.

## Acceptance Criteria

- L0-L2, traceability and mutation contracts pass deterministically; stable candidate bundle installs and verifies.
- L3/L4 interfaces require exact candidate SHA, redacted machine facts and sandbox-only identity.
- Final release record binds version, bundle, evidence, assets and provenance to the same SHA.

## Compatibility

- Preserve M0-M4 canonical bundle, automatic bridge, M3 policy/resource/review behavior and M4 finalization semantics.

## Security And Data

- Treat GitHub/sandbox/event data as untrusted; retain canonical redacted results, paths relative to approved roots, digests and terminal states only.

## Migration

- No production or consumer migration. Stable bundle output remains an artifact pending separate production-install authorization.

## Public Interfaces

- Add narrow verifier, traceability, sandbox-canary and release-candidate interfaces; final tag/Release writer remains trusted-main-only and exact-SHA bound.

## Execution Route

- Trusted main obtains six gates, prepares and claims one exact executor, waits in one-hour intervals, then independently accepts the fixed head.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions and sandbox-only L4 canary tooling; executor does not perform final candidate promotion.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with commit, push, PR update, scoped CI repair, ready-for-review and conditional merge authorization.

## Implementation Notes

- Prefer deterministic standard-library harnesses and fake providers for implementation validation. Commit implementation/evidence, then commit only delivery.md before `gkd-task deliver`; trusted main performs the single live L3/L4 and final promotion after merge.
