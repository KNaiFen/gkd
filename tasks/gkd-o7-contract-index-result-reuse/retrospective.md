# GKD O7 Contract Index And Result Reuse Retrospective

## Result

O7 separates behavioral execution from evidence projection. Canonical scope results run behavior once; delivery and contract evidence reuse that fixed fact while retaining their own boundary checks.

## Lessons

- A canonical result consumer must validate the full scope before choosing a subset; selecting raw JSON test records would lose the head, environment and all-pass guarantees.
- Contract catalogs should use complete test IDs as their primary evidence key. Suffix matching is convenient for discovery but cannot express stable shared ownership.
- Deduplication is only valid when the remaining consumer checks are explicitly lane-specific. Delivery still owns document, head, protected, temporary and output checks.

## Next

Create O8 from merge `5534269e490eb6eb783d451e18f82e670a0db4f4` with a fresh execution bundle. Preserve public legacy read/reject/migrate promises while moving only the expanded matrix to an explicit release-upgrade lane; do not merge release engines without a separate ADR and migration task.
