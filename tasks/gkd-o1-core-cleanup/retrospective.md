# GKD-O1 Retrospective

## What Worked

- Requirements/plan/implementation documents were parsed and bound by the task state machine.
- The bridge created one exact executor attempt; envelope and capability deletion after claim was expected one-time credential consumption.
- Executor stopped at delivery, and acceptor/main separation preserved the fixed-head acceptance boundary.
- Core behavior remained stable while payload size and test duplication decreased.

## Workflow Friction

- The host default `python3` was 3.9.6, while the bundle requires `zip(strict=...)` and other newer standard-library features. CLI commands returned misleading `FILESYSTEM_ERROR` until Python 3.14 was selected explicitly.
- `/tmp` is a symlink on macOS and was correctly rejected as a candidate parent; real `/private/tmp` paths were required.
- A manually copied route decision initially omitted `outcome`; bridge validation caught the malformed input before state mutation.
- Executor delivery did not create a PR, so trusted main had to create PR #34 before acceptance. The executor contract should make PR creation/update evidence explicit.
- Waiting schema v2 accepts a task-name handle without `/root/`, while host acknowledgement preserves the full `/root/...` name. The two contracts need an explicit normalization rule or a shared type in a later task.

## Follow-up

- O2 should clean persistent context without copying host-level recovery configuration.
- Later routing work should add a preflight command that reports the supported Python interpreter and validates route JSON before bridge preparation.
- CI/evidence work should make PR creation and task-name normalization machine-verifiable, without weakening fixed-head or no-fallback rules.
