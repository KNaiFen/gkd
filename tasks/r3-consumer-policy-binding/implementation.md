# GKD-R3 Implementation Notes

## Internal Design

Use the existing `gkd_ci.policy` parser as the only source for consumer policy semantics. Introduce a small canonical binding record rather than duplicating policy JSON in task, inventory, route, and bridge state. Each consumer of the record must recompute or validate it from the local checkout before relying on it.

## Execution Details

Update the task, role/project, routing, bridge, and their focused tests together. Regenerate the canonical bundle and run the repository-approved GKD verifier from the task base. Document the manual bootstrap exception and the exact first-consumer follow-up required for AIO, without constructing any artificial claim, delivery, activation, receipt, or Release evidence.
