# GKD-R4 Policy Binding Release Plan

## Goal

Create a truthful stable `0.1.3` release candidate for the already accepted R3 policy-binding source, so consumers can later restage from a published artifact rather than canonical source.

## User Decisions

- Continue after R3 under the explicit user authorization.
- Use a patch version because the reusable release mechanism and public interfaces already support strict stable semantic versions; R3 adds a compatible policy-binding requirement.
- Use the manual bootstrap exception only for this self-hosting release candidate. The previous published runtime cannot create the new policy-bound automatic state required by R3 itself.

## Behavior And Defaults

- `source.toml` declares `0.1.3`; generated manifest and lock bind the complete candidate payload to a new content digest.
- Existing release core derives `v0.1.3` from the immutable candidate record and keeps L3 trusted-main evaluation, L4 sandbox canary, deterministic asset, and final provenance exact-source bound.
- The candidate task remains manual-bootstrap planning state. No automatic offer, activation, claim, receipt, or delivery is manufactured for the self-hosting transition.

## Scope

- Change the canonical version declaration and generated metadata.
- Adjust only deterministic release fixtures, evidence, and tests necessary to make `0.1.3` the current candidate.
- Create deterministic evidence, verify the candidate from its fixed base, and submit one PR.

## Non-Goals

- Do not alter policy parsing/binding, automatic bridge behavior, route gates, review/resource features, release protocol semantics, production state, or AIO state.
- Do not create tag, Release, live canary, production, AIO, settings, Secret, or paid-runner side effects in candidate execution.

## Acceptance Criteria

- Stable-version propagation derives `v0.1.3` from the candidate while prior published records remain readable.
- Canonical generation and isolated install/verify are deterministic, and the new bundle digest differs from `v0.1.2`.
- Candidate evidence is path-minimized and equal across two clean temporary roots; the complete verifier passes.
- Independent fixed-head review and the policy-backed `GKD Verify` check pass before trusted main may merge or invoke release gates.

## Compatibility

- Existing `v0.1.0`, `v0.1.1`, and `v0.1.2` tags, Releases, assets, records, and historical task states remain immutable and readable.
- Only the new `0.1.3` candidate binds the R3 policy-binding source; no consumer pin moves until its published asset is verified and restaged.

## Security And Data

- Persist only public versions, source SHAs, canonical digests, release records, and redacted evidence metadata.
- All source, record, tag, asset, or boundary drift fails before a release result is accepted. No session, credential, home-path, or task capability data is persisted.

## Migration

- This task does not mutate production or AIO. After a successful post-merge release, trusted main will isolated-install and verify the exact `v0.1.3` asset, then deliberately restage the project before starting AIO inventory.

## Public Interfaces

- `gkd-release` retains its existing strict stable-version and side-effect-free candidate/promotion interfaces. This task changes the current canonical version input only.

## Execution Route

- Use one documented manual bootstrap candidate because the accepted `v0.1.2` runtime predates R3 policy-bound task state. Implementation is limited to its registered worktree and stops at a fixed PR head; it does not create automatic lifecycle facts.

## External Side Effects

- Candidate execution may create one GKD worktree, branch, PR, isolated evidence/install roots, and standard repository CI. After independent acceptance, trusted main may merge, run existing release gates, create the exact `v0.1.3` tag/Release and asset, and perform isolated project restage. Production and AIO writes remain outside this task.

## Action Mode

- `implement_and_merge_on_acceptance` under the user's 2026-08-23 continuation authorization. The manual bootstrap exception covers task execution only; trusted main owns acceptance, merge, release promotion, restage, and cleanup.

## Implementation Notes

- Reuse the existing strict semantic-version, release-candidate, L3/L4, deterministic asset, and restage mechanisms. Do not add a compatibility alias or copy R3 policy code into release logic. Regenerate metadata with canonical tooling and bind all verification to the registered base SHA.
