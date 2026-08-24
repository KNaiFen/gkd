# GKD R10 GitHub Acceptance Release

## Goal

Publish the accepted R9 GitHub acceptance and delivery sequencing repair as stable `v0.1.5`.

## User Decisions

- The user authorized the existing GKD release flow, fixed-head acceptance, merge, tag, GitHub Release, asset-local verification, and isolated project restage.
- The task must execute from the published and verified `v0.1.4` bundle, never from the R9 source tree.
- R7 and R8 remain blocked or rejected history; R10 must not alter or recreate their lifecycle records.

## Scope

- From R9 source base `790d592d63c7c34a0047f136e18fa15238e722d6`, bump canonical release metadata from `0.1.4` to `0.1.5`.
- Regenerate only the manifest, lock, release candidate fixtures, evidence, and tests required by the existing stable release contract.
- Deliver one fixed-head GKD PR; after independent acceptance and merge, trusted main runs L3/L4, exact tag/Release promotion, asset-local verification, and isolated GKD project restage.

## Non-Goals

- Do not change R9 GitHub acceptance behavior, task bridge behavior, workflows, production `~/.codex`, AIO files, GitHub settings, Secrets, paid runners, or R7/R8 records.

## Acceptance Criteria

- [ ] `0.1.5` version metadata, candidate record, generated lock and tag input are internally consistent while historical releases remain readable.
- [ ] The complete verifier and fixed-head `GKD Verify` pass, and the candidate stops before tag, Release, production, or AIO mutation.
- [ ] Post-merge release gates publish and independently verify only the exact `v0.1.5` asset, then restage the isolated GKD project runtime.
