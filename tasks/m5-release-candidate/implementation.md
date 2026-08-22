# GKD-M5-A Implementation

## Internal Design

Separate deterministic L0-L2 and traceability mechanics from release-candidate-only L3/L4 adapters. Bind every terminal fact, release asset and provenance record to one exact candidate SHA; keep tag and Release mutation outside executor-facing code.

## Execution Details

Implement only the approved M5 scope in the registered worktree. Validate through installed `gkd-execute`/`gkd-local-verify`, fixed-base verifier, deterministic evidence and candidate bundle installation. Do not rerun historical custom-role probes, execute a real one-hour experiment, tag, publish or touch production/AIO. Commit delivery.md before final `gkd-task deliver` and stop for trusted-main acceptance.
