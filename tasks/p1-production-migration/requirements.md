# GKD-P1 Requirements

## Goal

Deliver a production-only GKD migration capability that can install a fixed released bundle into a real Codex home with an inspectable doctor and a recoverable rollback path.

## User Decisions

- The user explicitly authorized production installation, the minimum supporting GKD implementation and a new fixed-bundle release on 2026-08-22.
- AIO adoption remains a later, separate consumer task and may begin only after trusted main verifies the installed production bundle.
- The executor must not write the production home, publish a release, create a tag, alter GitHub settings, use Secrets or paid runners.

## Scope

- Preserve the current temporary-home migration commands and their production rejection behavior.
- Add an explicitly named production migration plan, apply, verify/doctor, rollback/recovery interface with narrow managed surfaces.
- Stage and verify all changed managed files before mutation; retain a durable, path-safe recovery record until the operation reaches a verified terminal state.
- Cover successful installation, injected interruption/failure, explicit rollback/recovery, pre-existing recovery state, home/config/symlink rejection, tampered staged content and no leakage of configuration contents in machine results.
- Bump the canonical source to the next stable patch version and update deterministic bundle/release fixtures and documentation required by that change.

## Non-Goals

- No production mutation, AIO file change, custom provider/auth change, plugin/cache cleanup, Secrets, paid runners or GitHub settings change in this task.
- No replacement of a whole user home or unbounded copy of Codex runtime databases, session history or unrelated configuration.
- No relaxation of existing `migration-*` or temporary bundle installer boundaries.

## Acceptance Criteria

- The existing production-root rejection tests continue to pass for temporary-only interfaces.
- The new production path rejects ambiguous, symlinked, malformed, drifted and unrecoverable states before unsafe mutation.
- An injected failure leaves a deterministic recovery state that restores the exact managed preimage; successful completion leaves no active recovery state and verifies the expected role, Skill and config inventory.
- Tests prove the production transaction touches only declared managed surfaces and result/evidence payloads contain no configuration bytes or absolute home path.
- The candidate produces a self-verified `0.1.1` bundle; trusted main has sufficient deterministic evidence to independently accept and subsequently run the separately authorized release and production-install gates.
