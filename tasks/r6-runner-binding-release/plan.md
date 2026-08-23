# GKD R6 Runner Binding Release Plan

## Goal

Turn the accepted R5 source into a verified stable `0.1.4` bundle for AIO.

## User Decisions

- Continue under the existing implementation and release authorization.

## Behavior And Defaults

- `source.toml` is the only new release input; existing strict release mechanisms derive tag, asset and provenance from the immutable merge SHA.

## Scope

- Version declaration, generated metadata, release fixtures/evidence/tests needed for `0.1.4`.

## Non-Goals

- No resource/bridge/workflow/product behavior change; no candidate-side tag, Release, production or AIO write.

## Acceptance Criteria

- All requirements AC plus deterministic candidate evidence, complete verifier, fixed-head CI and independent acceptance.

## Compatibility

- `v0.1.0` through `v0.1.3` remain immutable and readable.

## Security And Data

- Persist only public version, digest, source and redacted release evidence.

## Migration

- Trusted main restages only the verified published asset after promotion.

## Public Interfaces

- Existing `gkd-release` contract; version input only.

## Execution Route

- Automatic route using the accepted `v0.1.3` runtime and one exact `gkd_executor`.

## External Side Effects

- Candidate PR/CI; after acceptance, exact tag/Release asset and isolated project restage only.

## Action Mode

- `implement_and_merge_on_acceptance` with `ci_repair`, `commit`, `conditional_merge`, `pr_update`, `push`, `ready_for_review`.

## Implementation Notes

- Reuse canonical generator and release contracts; do not add aliases.
