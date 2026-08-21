# GKD-M4-A Plan

## Goal

Implement repository-neutral finalization and release mechanics needed before the final release-candidate verification task.

## User Decisions

- Use one exact automatic `gkd_executor`; no fallback, worker, retry, role/model substitution or nested agent.
- Trusted main alone accepts, merges and cleans up; M4 does not create a tag or GitHub Release.

## Behavior And Defaults

- Closeout-only is the default and cannot carry product logic or release side effects.
- Release promotion requires exact candidate/main SHA, explicit adapter and authorization; retry must not rebuild evidence or create a second release.

## Scope

- Fixed-head independent acceptance protections, task/finalization PR state machinery, deterministic release metadata/interfaces and generic fixtures.

## Non-Goals

- M3 behavior changes, M5 L3/L4 canary execution, actual publishing, production/AIO work, paid runners, Secrets or GitHub settings.

## Acceptance Criteria

- Fixtures cover normal closeout, unauthorized release refusal, exact SHA promotion, provenance and retry idempotence.
- Candidate code remains unexecuted by acceptance; no records/version/evidence split path exists.

## Compatibility

- Preserve M2 automatic bridge, M3 policy/resource/review contracts, installed bundle validation and staged project-role behavior.

## Security And Data

- Treat adapter/GitHub data as untrusted; canonical outputs retain identifiers, digests and redacted facts only.

## Migration

- No production or consumer migration. M4 adds candidate-bundle mechanisms only.

## Public Interfaces

- Add version, release-intent, finalization, promotion and provenance schemas/CLI interfaces without a public writer that can bypass trusted acceptance.

## Execution Route

- Trusted main obtains six gates, prepares and claims one exact executor, waits in one-hour intervals, then independently accepts the fixed head.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions, read-only GitHub observations and isolated evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with commit, push, PR update, scoped CI repair, ready-for-review and conditional merge authorization.

## Implementation Notes

- Prefer standard-library deterministic state and fake adapters. Commit implementation/evidence, then commit only the canonical delivery document and invoke `gkd-task deliver` with its exact digest.
