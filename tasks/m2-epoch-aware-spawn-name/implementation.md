# GKD-M2-E Implementation Notes

## Internal Design

- Extend the private bridge task-name derivation to bind a sanitized task identifier and validated attempt identity available from the automatic claim context.
- Return that name in the existing spawn request and reconstruct the same expected name during claim validation; do not persist a second mutable name registry.
- Keep the host-safe name contract deterministic, bounded, ASCII-only, and collision-resistant across epochs of the same task.
- Add focused runtime-bridge tests for initial prepare, rework/new epoch, revoked offer/new epoch, wrong old task name, recovery, and mutation of each attempt-binding input.

## Execution Details

- Begin with installed `gkd-task status` and `doctor`, then inspect bridge, offer/context, rework tests, schemas, Skills, and verifier routing before editing.
- Add failing contracts demonstrating the real duplicate host task-name problem before changing implementation.
- Run `scripts/gkd-verify --base-sha <full-base-sha>` and two disjoint deterministic evidence generations; regenerate canonical manifest/lock only through bundle tooling.
- Push and maintain one task PR, repair only failures introduced by this narrow change, deliver with immutable accepted execution bundle and separate candidate output bundle, then stop before acceptance, merge, cleanup, M3-A, production, or AIO work.
