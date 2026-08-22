# GKD-R3 Consumer Policy Binding Plan

## Goal

Establish a deterministic consumer-policy chain before AIO receives its first `.gkd` policy or automatic executor route.

## User Decisions

Use only host-observable facts. Preserve the accepted v0.1.2 role and host-acknowledgement contracts, retain the existing six route gates, and fail closed instead of substituting a worker, fallback role, fabricated receipt, or AIO-local implementation.

## Behavior And Defaults

The existing strict policy parser remains authoritative. Bootstrap creates a task only from a policy package whose repository identity matches the checkout origin and requested repository. Project staging records the policy facts in its inventory. Route and bridge preparation consume verified policy facts and reject every mismatch before a task can become eligible for automatic execution.

## Scope

1. Extend the task bootstrap package/state contract to bind a validated consumer policy.
2. Extend project staging and project verification with an exact policy record and digest.
3. Version the route decision and automatic offer validation as needed to carry the same binding while retaining all six gates.
4. Make the trusted bridge independently compare current task state, checked-out policy, staged inventory, and route decision.
5. Add focused unit, integration, and static contract coverage, then update the relevant GKD guidance and acceptance evidence.

## Non-Goals

- No AIO policy write, migration, scanner, resource tuning, CI redesign, review package, production migration, or task-history rewrite.
- No host-role contract change beyond consuming the existing host acknowledgement; no role/model/sandbox/runtime inference.
- No new route gate, GitHub setting, Secret, paid runner, tag, or Release as part of this task.

## Acceptance Criteria

1. Bootstrap, staging, route, and bridge each reject absent or malformed policy input.
2. Repository, origin, base branch, required checks, and policy digest must agree at every boundary.
3. Altering any policy input after staging or after route generation fails before automatic preparation/claim.
4. The six route gate names and their fail-closed semantics remain unchanged.
5. Existing release, task, role, and CI contracts remain green with no consumer-specific contamination.

## Compatibility

Existing pre-policy tasks remain readable as legacy/manual records. They are not upgraded into automatic eligibility; a new policy-bound task is required for automatic routing.

## Security And Data

Policy data is repository configuration only. The implementation must not scan home directories, print credentials, or add general Cyber review behavior. Diagnostics may report stable error codes and non-sensitive digests only.

## Migration

The first consumer receives a policy through the new deterministic bootstrap path after this bundle is released. Existing staged projects are restaged deliberately; no inventory is hand-edited and no old task state is rewritten merely to add a policy digest.

## Public Interfaces

The affected public machine interfaces are `gkd-task bootstrap`, `gkd-role project-stage`, `gkd-role project-verify`, `gkd-role route`, and the trusted-main bridge library interface. Any schema version changes must be explicit and covered by compatibility tests.

## Execution Route

This task uses a manual bootstrap exception because it implements the first-consumer binding that future automatic routing must require. It must not claim or test automatic executor activation until the new policy chain is implemented and independently verified.

## External Side Effects

Allowed task effects are branch commits, push, one GKD task PR, CI repair inside this scope, fixed-head independent acceptance, and synchronous squash merge after all gates pass. No AIO write, production install, tag, Release, Secret, runner purchase, or GitHub setting change is authorized by this task.

## Action Mode

`implement_and_merge_on_acceptance`: `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review`, and `conditional_merge` are authorized only for this task's exact branch, fixed head, and acceptance path.

## Implementation Notes

Prefer structured policy APIs over string parsing. Keep policy schema/project facts separate from host facts. Tests must prove that substituted policy JSON, origin drift, stale project inventory, and a mismatched route record fail before any automatic bridge action. The trusted-main library entry must run without creating bytecode files inside the verified installed bundle; the caller or library must set the standard no-bytecode guard before importing bundle modules, and the regression test must verify the installed inventory remains valid after bridge preparation.
