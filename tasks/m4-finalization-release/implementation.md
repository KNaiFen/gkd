# GKD-M4-A Implementation

## Internal Design

Keep task finalization, release intent and provenance in portable deterministic modules. Release adapters are explicit data boundaries; no candidate-facing API may create a tag or release outside trusted acceptance.

## Execution Details

Implement only the approved M4 requirements and plan. Use installed `gkd-execute` and `gkd-local-verify`, run the fixed-base verifier, produce deterministic evidence and bundle declarations, commit delivery.md before the final `gkd-task deliver`, then stop for trusted-main acceptance.
