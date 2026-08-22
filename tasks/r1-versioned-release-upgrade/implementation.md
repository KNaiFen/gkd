# GKD-R1 Implementation

## Internal Design

Define the stable release version grammar beside the existing release-candidate validator, use it
when building a candidate, and derive the promotion tag from the validated record. Keep all source
version declarations and test fixtures explicit. The canonical generator remains the sole writer
for manifest/lock.

## Execution Details

Work only in the registered candidate worktree. Update the narrow release implementation, fixtures
and tests; set `source.toml` to `0.1.2`; regenerate canonical metadata; run focused evidence twice
and the full verifier from the registered base. Commit/push a single PR, write delivery and stop at
the final fixed head. Do not create task runtime facts, tags, Releases, production/AIO changes or
post-merge records in the executor scope.
