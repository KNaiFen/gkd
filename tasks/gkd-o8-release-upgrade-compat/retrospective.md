# GKD O8 Release Upgrade Compatibility Retrospective

## Result

O8 makes legacy compatibility scheduling explicit. Default/core now proves the minimum public promise for each legacy format, while the full historical upgrade matrix is a separate reproducible release-upgrade lane.

## Lessons

- Compatibility cost can only be reduced safely after cataloging the public formats and retaining independent, stable positive and negative test IDs for each one.
- A lane is meaningful only when its complete scope, fixed head, environment and digest are independently bound; core success cannot stand in for a release-upgrade result.
- Similar canonical-record mechanics do not authorize merging public engines. ADR-001 makes the required migration proof and stop boundary explicit before any future extraction.

## Next

The O1-O8 optimization plan is complete. Any shared release/finalization engine migration requires a separately approved task that first proves the ADR-001 CLI, record, promotion-shape, provenance, adapter and dual-interpreter compatibility contracts.
