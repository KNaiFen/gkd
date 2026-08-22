# GKD-P1 Plan

## Goal

Add the minimum production migration capability missing from the released `0.1.0` bundle without weakening its temporary-only safeguards.

## User Decisions

The user authorized this bounded production-support implementation, its patch release, the later trusted-main production installation and the subsequent AIO adoption task. P1 also resolves legacy role replacement, but the user-specific global AGENTS compression is a separately accepted P2 policy task: it must not be guessed or embedded in the portable bundle. The executor remains limited to the GKD task worktree, task PR and scope-local CI repair.

## Behavior And Defaults

Production operations use a separate explicit interface and an explicit home root. They validate all managed inputs and recovery state before any write, stage desired bytes first, and provide deterministic plan, apply, doctor and recovery/rollback outcomes. The legacy temporary migration API remains production-forbidden.

## Scope

Implement the production transaction, schema/CLI surface, narrow managed-surface inventory, durable recovery record, doctor and rollback/recovery semantics. Treat both legacy role filenames as explicit managed removals and verify that neither survives a successful migration. Add focused standard-library tests and update source version, manifest/lock, release fixtures and user-facing documentation only as needed for `0.1.1`.

## Non-Goals

Do not install into the actual production home, modify AIO, create a tag or Release, change GitHub settings, or introduce repository-specific consumer policy. Do not encode, rewrite or claim to compress arbitrary user global AGENTS content; P2 owns that policy-specific, reversible operation.

## Acceptance Criteria

All existing verifier scopes and new production-migration tests pass from a clean worktree. The implementation proves precise managed-surface mutation, failure recovery, legacy role removal and path/content containment; temporary migration behavior remains unchanged. P1 documentation makes clear that its doctor does not certify the separate global-AGENTS P2 gate.

## Compatibility

Existing `migration-plan`, `migration-apply` and `migration-verify` continue to reject production homes. Existing role, project staging, routing, bridge, monitor, resource and review interfaces retain their current contracts.

## Security And Data

Treat the home configuration and runtime state as private. Do not serialize their contents, credentials, tokens, absolute home path or session data into Git, task documents, PR data, test fixtures or machine output. Reject symlinks and ambiguous recovery state rather than following or guessing.

## Migration

The new path is opt-in and only usable by trusted main after the user-approved release. It must make recovery explicit and deterministic; it must not silently alter an existing temporary migration or generic bundle installation path. The subsequent P2 task will bind the actual global AGENTS preimage, reviewed compression mapping and rollback evidence without making that user policy part of the portable bundle.

## Public Interfaces

Add a production-specific `gkd-role` command family or equivalently explicit production API. Its input/output schema must distinguish plan, apply, verify/doctor and rollback/recovery states without exposing private home details.

## Execution Route

Trusted main prepares, claims and waits for one exact `gkd_executor` from the accepted execution bundle. The executor implements, verifies, commits, pushes, maintains one task PR, writes delivery and stops at its complete fixed head. Trusted main independently accepts, merges, releases and later performs the real production migration.

## External Side Effects

The executor may create or update only the GKD task branch, PR and scope-local standard GitHub Actions. Trusted main alone may merge after acceptance and later create the `0.1.1` release and execute the production migration. No AIO effect is permitted in this task.

## Action Mode

`implement_and_merge_on_acceptance`.

## Implementation Notes

Use focused deterministic tests with injectable failure points and temporary fixture homes. Do not use production paths in tests. Add focused contracts for legacy role deletion and legacy-role absence after doctor. Rebuild canonical metadata only through the repository-approved generator, run the registered verifier from the fixed base SHA, commit delivery before `gkd-task deliver`, and stop on the final fixed head.
