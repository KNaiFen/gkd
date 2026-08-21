# GKD-M2-I-R Implementation

## Internal Design

Use `git cherry-pick 27cf3293d6cc37c4f19a0b96d934d4b6c079db01` as the implementation baseline. Resolve any manifest or documentation conflict against current main by preserving both the M2-J delivery-contract changes and the M2-I bridge changes. Do not cherry-pick the old M2-I task-state or delivery commits.

## Execution Details

Run the installed `gkd-local-verify` contract and the focused M2-I deterministic evidence. Commit implementation and evidence first. Then create and commit only `tasks/m2-host-recovery-bridge-redelivery/delivery.md`; invoke `gkd-task deliver` with the exact document path and digest, and stop at the returned final fixed head.
