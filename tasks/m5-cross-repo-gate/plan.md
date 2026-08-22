# GKD-M5-C Plan

## Goal

Implement the minimal final-gate correction required for an honest GKD 0.1.0 release.

## User Decisions

The stable release remains `0.1.0`; trusted main remains sole owner of live L3/L4, tag and Release effects.

## Behavior And Defaults

L4 accepts a successful sandbox check only after canonical marker content at its fixed sandbox head binds the expected GKD source SHA and bundle digest. L3 eval-only output is redacted and exact-SHA bound.

## Scope

Modify only release verification, release record/provenance interfaces and their deterministic tests.

## Non-Goals

No production/AIO work, Secrets, paid runners, settings changes or executor-issued external promotion.

## Acceptance Criteria

All M5 verification scopes pass; cross-repository head/source substitution is rejected; final trusted main has enough canonical inputs for one real L3/L4 pass.

## Compatibility

Preserve M0-M5-B bundle, bridge and release-candidate contracts except for the corrected final-gate representation.

## Security And Data

Treat GitHub file and check data as untrusted; retain only canonical redacted facts and digests.

## Migration

No consumer or production migration.

## Public Interfaces

Add narrow `gkd_release` eval-only and cross-repository observation interfaces only.

## Execution Route

Trusted main prepares, claims and waits for one exact executor, then independently accepts the fixed head.

## External Side Effects

Executor may create/update only its GKD task PR and CI. Trusted main alone reuses sandbox PR #1 after merge.

## Action Mode

`implement_and_merge_on_acceptance`.

## Implementation Notes

Use deterministic standard-library/fake-GitHub tests. Commit delivery before `gkd-task deliver`; stop on fixed head.
