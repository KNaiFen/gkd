# GKD-M2-K Implementation

## Internal Design

Introduce a fresh automatic protocol version with two separate facts: a verified configured executor catalog owned by the accepted execution bundle, and a host-spawn acknowledgement owned by trusted main. The acknowledgement is limited to one successful direct spawn and its returned exact task name. Derive an executor-attempt handle from the immutable automatic context and acknowledged task name; use that handle wherever fresh automatic state previously implied a raw agent/thread identity. Keep old records on their existing validation path. For fresh records, eliminate automatic terminal reclaim unless a future host interface exposes a machine-bindable terminal handle.

## Execution Details

Work only in the registered candidate worktree. Implement focused schemas, validators, bridge/activation/task/wait/acceptance changes, documentation and tests. Generate canonical metadata with repository tooling, run focused evidence twice and the complete approved verifier from the registered base. Commit and push one PR, write a fixed-head delivery document and stop before independent acceptance, merge, release, production installation, AIO or cleanup. This bootstrap task must not fabricate a claim, activation, receipt or delivery state for itself.
