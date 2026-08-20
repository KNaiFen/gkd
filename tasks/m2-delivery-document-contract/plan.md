# GKD-M2-J Plan

## Goal

Bind the delivery document to the delivery state transition so fixed-head acceptance has one deterministic final tree and no post-delivery ambiguity.

## User Decisions

- Use one exact automatic `gkd_executor`; no fallback, retry, role/model substitution or worker.
- Keep the task a workflow-core prerequisite and do not implement M3 functionality.
- Preserve existing task, offer, claim, activation, rework and bundle boundaries.

## Behavior And Defaults

- Delivery document path and digest are explicit coordination facts.
- The document commit precedes the state transition; the state transition commit is the final coordination commit.
- Acceptance validates the exact sequence and permitted paths before any merge.
- Legacy delivered states remain readable with a clear legacy outcome, but are not silently treated as newly bound delivery.

## Scope

- Task service/model/acceptance delivery binding, CLI contract, executor Skill, tests, evidence and canonical bundle metadata.

## Non-Goals

- Product features, M3 work, release/production/AIO changes, arbitrary post-delivery editing or acceptance bypasses.

## Acceptance Criteria

- Positive fresh delivery sequence and negative post-delivery mutation matrix are covered.
- Existing retained contracts pass; verifier adds the new focused suite without dependencies or large artifacts.
- Evidence is deterministic and path-minimized.

## Compatibility

- Additive state facts only; old task states parse explicitly as legacy and retain existing safety behavior.
- Public candidate acceptance/merge remains unavailable.

## Security And Data

- Validate paths, canonical JSON/digests and fixed-tree ancestry before writes; never persist raw host identity or secrets.

## Migration

- No production/consumer migration. New tasks use the bound sequence; current delivered candidates are accepted only after a trusted rework/redelivery under the new contract.

## Public Interfaces

- `gkd-task deliver` accepts the explicit delivery-document binding required by the task state.
- `gkd-task accept` validates the binding and exact fixed head.

## Execution Route

- Trusted main routes one exact executor through the accepted bridge; executor implements, verifies, commits delivery document before `deliver`, pushes and stops; trusted main accepts/merges.

## External Side Effects

- One task PR, standard Actions caused by tracked workflow changes, read-only GitHub facts and isolated evidence roots only.

## Action Mode

- `implement_and_merge_on_acceptance`; executor owns commit/push/PR/CI repair/ready, trusted main owns merge.

## Implementation Notes

- Reuse existing canonical JSON, digest, fixed-tree and transaction helpers; keep the additive contract small.
