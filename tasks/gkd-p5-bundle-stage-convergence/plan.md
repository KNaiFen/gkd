# P5 Plan

## Goal

Converge development bundle/project staging and retire unnecessary high-level manual inputs.

## User Decisions

Production and external account surfaces remain untouched.

## Behavior And Defaults

The trusted main CLI derives source metadata, target ownership, bundle digest, and inventory; the default action is dry validation unless refresh is explicitly requested.

## Scope

Add a stage transition facade and update core GKD skills to call it.

## Non-Goals

No production migration, release publishing, or lifecycle protocol changes.

## Acceptance Criteria

Owned development stage refresh is deterministic and idempotent; all drift and overlap negative contracts remain fail-closed; 3.9 verification and fixed-head CI pass.

## Compatibility

Retain low-level bundle/project commands for diagnostics and legacy callers.

## Security And Data

Do not expose home paths, capabilities, credentials, or raw runtime facts in machine output.

## Migration

Existing staged files are removed only when ownership and inventory match; failed transitions preserve recoverable preimages.

## Public Interfaces

Add only a trusted high-level stage transition entry point; keep existing low-level commands compatible.

## Execution Route

Fresh GKD lifecycle with one executor, fixed-head delivery, independent acceptance, and trusted-main merge.

## External Side Effects

Non-production temporary stage only; no production or GitHub configuration changes.

## Action Mode

Implement and merge only after independent acceptance.

## Implementation Notes

Prefer existing bundle/project helpers and generated inventory; avoid new duplicate abstractions.
