# GKD R10 GitHub Acceptance Release Plan

## Goal

Turn the accepted R9 source into the verified stable `0.1.5` bundle required before AIO can consume the repaired acceptance path.

## User Decisions

- Continue under the authorized GKD release and acceptance boundary.
- Bind execution to the verified published `v0.1.4` asset and bind source, tag, Release, asset, and provenance to the eventual single release merge SHA.

## Behavior And Defaults

- `source.toml` is the only new release input; existing strict release mechanisms derive tag, asset, and provenance from immutable merge facts.

## Scope

- Version declaration, generated metadata, release fixtures, evidence, and tests needed for `0.1.5`.

## Non-Goals

- No change to R9 acceptance or delivery behavior, resource semantics, bridge behavior, workflow policy, production, AIO, GitHub settings, Secrets, or paid runners.

## Acceptance Criteria

- All requirements criteria plus deterministic candidate evidence, complete verifier, fixed-head CI, and independent acceptance pass.

## Compatibility

- `v0.1.0` through `v0.1.4` remain immutable and readable.

## Security And Data

- Persist only public version, digest, source, and redacted release evidence.

## Migration

- Trusted main restages only the verified published `v0.1.5` asset after promotion.

## Public Interfaces

- Existing `gkd-release` contract; version input only.

## Execution Route

- Automatic route using the accepted published `v0.1.4` runtime and one exact `gkd_executor`.

## External Side Effects

- Candidate PR and CI; only after acceptance and merge, exact tag, GitHub Release asset, L3/L4, asset-local verification, and isolated GKD project restage.

## Action Mode

- `implement_and_merge_on_acceptance` with `ci_repair`, `commit`, `conditional_merge`, `pr_update`, `push`, and `ready_for_review`.

## Implementation Notes

- Reuse the canonical generator and release contracts without aliases or new release mechanisms.
