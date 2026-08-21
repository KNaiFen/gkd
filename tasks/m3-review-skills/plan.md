# GKD-M3-C Plan

## Goal

Implement the repository-neutral review core and the two new workflow Skills required to close milestone 3.

## User Decisions

- Use one exact automatic `gkd_executor`; no fallback, worker, retry, role/model substitution or nested agent.
- Trusted main alone accepts, merges and cleans up.

## Behavior And Defaults

- Ambiguous review intent remains in recommendation/clarification state; it must not silently approve or merge.
- Partial approval and recovery preserve canonical machine facts and require explicit continuation.

## Scope

- Shared review state, targeted/guided/recon entry points, partial approval, resume/recovery and deterministic machine facts.
- `gkd-optimize-ci`, `gkd-review-remediation`, seven-Skill bundle declarations, multi-repository adapter schemas and redacted fixtures.

## Non-Goals

- M3-A monitor/policy, M3-B resource/scanner behavior, M4 release logic, M5 release-candidate verification, production/AIO or GitHub settings.

## Acceptance Criteria

- Fuzzy review recommendation, targeted/guided/recon, partial approval and recovery fixtures pass with mutation coverage.
- The two Skills are discoverable from the accepted bundle, Skill names are unique, and manifest/lock/inventory/digests remain aligned.
- Adapter schema supports multiple repositories and fixtures are redacted without credential-shaped output.

## Compatibility

- Preserve M3-A policy/monitor, M3-B resource/scanner, M2 runtime bridge, task acceptance and project staging contracts.

## Security And Data

- Retain only canonical redacted facts and digests; never print raw credentials, authorization headers or machine paths.

## Migration

- No production or consumer migration. New capabilities are installed only in the candidate bundle and project staging after acceptance.

## Public Interfaces

- Add generic review, optimization, remediation and multi-repository adapter schemas; no merge, rerun, dispatch or settings writer.

## Execution Route

- Trusted main obtains six gates, prepares and claims one exact executor, waits in one-hour intervals, then independently accepts the fixed head.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions, read-only GitHub observations and isolated evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with commit, push, PR update, scoped CI repair, ready-for-review and conditional merge authorization.

## Implementation Notes

- Prefer standard-library deterministic parsers and fixtures; preserve M3-A/M3-B no-dependency verifier and path-free output boundaries.
- Commit implementation/evidence, then commit only the canonical delivery document and invoke `gkd-task deliver` with its exact digest.
