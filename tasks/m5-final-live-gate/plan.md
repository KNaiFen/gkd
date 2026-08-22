# GKD-M5-B Plan

## Goal

Implement the smallest M5 remediation needed for a real exact-SHA final gate. Deterministic contracts and fake-GitHub tests cover implementation. The executor implements, verifies, commits, pushes and delivers a fixed head only. Trusted main alone runs the live sandbox canary after merge, independently accepts the final record, tags `v0.1.0`, creates the Release, updates records and cleans up.

## User Decisions

The final release remains `0.1.0`; automatic routing remains exact `gkd_executor` only.

## Behavior And Defaults

L3 and L4 default to fail-closed when their supplied source SHA differs from the immutable candidate SHA.

## Scope

Implement exact-SHA L3/L4 final-gate and release-provenance contracts only.

## Non-Goals

No production installation, AIO work, Secrets, paid runners, settings changes, executor-issued tags or Releases.

## Acceptance Criteria

The trusted main can produce and independently validate one exact-SHA L3/L4 record and one matching promotion input.

## Compatibility

Keep M0-M5-A public contracts valid.

## Security And Data

Retain canonical redacted machine facts only; sandbox repository identity is explicit and exact.

## Migration

No consumer or production migration.

## Public Interfaces

Add only narrow exact-SHA final-gate interfaces under `gkd_release`.

## Execution Route

Trusted main prepares, claims and waits for one exact executor; acceptance remains fixed-head.

## External Side Effects

Only the trusted main may perform one post-merge sandbox canary, tag and Release after all gates pass.

## Action Mode

`implement_and_merge_on_acceptance`.

## Implementation Notes

Use deterministic standard-library and fake-GitHub tests; executor writes delivery before `gkd-task deliver`.
The task has no authority to modify production `/Users/knaifen/.codex`, AIO, Secrets, paid runners or GitHub settings.
