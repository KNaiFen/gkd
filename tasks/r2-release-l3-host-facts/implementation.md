# GKD-R2 Implementation

## Internal Design

Define a new L3 trusted-main release-evaluation schema with a fixed no-write
boundary and digests derived from the immutable release candidate and its
traceability. Replace the legacy fresh-executor trace validator at the
post-merge boundary, preserve the existing L4 and final-provenance structure,
and regenerate canonical metadata only through the repository generator.

## Execution Details

Work only in the registered candidate worktree. Change the narrow release
implementation, fixtures, tests, and generated metadata; run focused evidence
twice, the full verifier from the registered base, and isolated bundle
install/verify. Commit/push one PR, write delivery, and stop at the final fixed
head. Do not run live L3/L4, create a tag or Release, mutate production/AIO, or
create task runtime facts.
