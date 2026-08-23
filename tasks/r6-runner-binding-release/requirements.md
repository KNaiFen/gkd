# GKD R6 Runner Binding Release

## Goal

Publish the accepted R5 runner-resource binding as stable `v0.1.4`, then provide its exact asset for AIO restage.

## User Decisions

- The user authorized continuation and automatic release work within the existing GKD/AIO boundary.
- Consumers must use only a verified published asset, never the R5 source tree.

## Scope

- Bump canonical source from `0.1.3` to `0.1.4`, regenerate manifest/lock, update release candidate fixtures/evidence and run the complete verifier.
- Deliver one fixed-head GKD PR; trusted main performs post-merge release gates, exact tag/Release asset and isolated restage.

## Non-Goals

- Do not alter R5 resource semantics, task bridge, workflows, production, AIO files, GitHub settings, Secrets or paid runners.

## Acceptance Criteria

- [ ] `0.1.4` metadata, candidate record and tag input are internally consistent and historical releases remain readable.
- [ ] Complete verifier and fixed-head `GKD Verify` pass; candidate stops before tag/Release/production/AIO mutation.
- [ ] Post-merge gates publish and independently verify only the exact `v0.1.4` asset before AIO restage.
