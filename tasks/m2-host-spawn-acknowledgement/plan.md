# GKD-M2-K Plan

## Goal

Replace the unimplementable host-runtime receipt assumption in the automatic bridge with a minimal, explicit host-spawn acknowledgement contract that the current host can actually provide.

## User Decisions

- The user selected host-observable facts over retaining a stronger but unavailable host-runtime assertion.
- The automatic route still has exactly one direct `gkd_executor`, the deterministic prepared task name and `fork_turns=none`; no alternate role, retry, downgrade or fallback is permitted.
- The repair is generic and repository-neutral. It must not depend on private Codex rollout/session storage or a particular host's hidden implementation.
- A bounded manual bootstrap exception is necessary for this repair because the v1 automatic bridge cannot honestly claim its own executor under the current host receipt surface.

## Behavior And Defaults

- `prepare` continues to bind the six-gate route decision, immutable execution bundle and configured executor catalog to one automatic offer/envelope.
- The only new host observation is successful direct spawn acknowledgement with the returned exact task name. Requested role and `fork_turns` are checked against the prepared request; configured runtime values are checked against the verified catalog and labelled configured rather than effective.
- The bridge derives a non-secret executor-attempt handle from immutable task/offer/envelope/task-name facts. It replaces the v1 use of a raw agent/thread identity for fresh attempts.
- A normal executor delivery remains the successful terminal path. If a fresh attempt ends without delivery, the trusted main records the host-visible stop and blocks the task for manual recovery; it does not invoke terminal reclaim from an unbound event.

## Scope

- Add an additive versioned automatic offer/envelope/activation/claim contract for host-spawn acknowledgement and executor-attempt handle semantics.
- Update bridge, activation authority, task service/model/runtime/acceptance, wait-state handling, schemas and main/executor documentation for the new contract.
- Preserve v1-v3 parsing and validation as explicit legacy behavior. New tasks use the new contract only after complete prepare/acknowledge/claim validation.
- Add focused positive, negative, mutation, migration and deterministic-evidence tests, then regenerate manifest/lock through canonical tooling.

## Non-Goals

- No host API modification, session/rollout parser, raw identity persistence, effective-setting inference, M3 product scope, production/AIO change or GitHub configuration change.
- No automatic reclaim, hidden retry or replacement executor for a fresh host-acknowledgement attempt.

## Acceptance Criteria

- All requirements have positive and negative coverage; material protocol changes have mutation coverage.
- The test host fixture supplies only the current public acknowledgement surface. Tests prove that adding unavailable v1 identity/effective-setting fields is neither required nor accepted as a new-contract prerequisite.
- New and legacy fixed-head acceptance remain deterministic, and no public candidate surface obtains activation, claim, reclaim, acceptance or merge authority.
- Evidence is path-minimized, byte-identical across two disjoint temporary roots, and protected surfaces do not drift.

## Compatibility

- Historical automatic v1/v3 records retain their original validators and receipts. They are not rewritten, reinterpreted or used as proof for the new contract.
- Existing manual route behavior, role names, execution-bundle pinning, route gates, task delivery binding and fixed-head acceptance remain compatible.
- Fresh automatic attempts use an explicit protocol version so accepting a v1-shaped result cannot silently select the revised trust model.

## Security And Data

- Persist only canonical task/offer/bundle/route bindings and a deterministic attempt handle. Do not persist raw thread IDs, capabilities, prompts, transcripts, credentials, paths or host configuration.
- Fail closed before writes on acknowledgement mismatch, duplicate spawn, expiry, digest drift, malformed handle or unavailable host fact.

## Migration

- No production or consumer migration. The new protocol applies only to future automatic offers after acceptance and restaging of the new bundle.
- In-flight or historical legacy attempts remain governed by their recorded version; recovery never converts them to the new protocol.

## Public Interfaces

- Expose a main-only host-acknowledgement input and corresponding machine-readable bridge outcome. Public `gkd-role automatic-*`, candidate `gkd-task` claim/reclaim and default task-library paths remain unavailable trust boundaries.
- The main Skill states exactly which host facts it may normalize and how it blocks an unbound terminal observation.

## Execution Route

- This repair is a one-time manual trusted-main bootstrap task because the defect prevents an honest automatic claim. The implementation session works only in its registered worktree, verifies, commits, pushes and stops at a fixed head without fabricating task runtime records.
- Trusted main independently accepts and conditionally merges the exact fixed head. Subsequent tasks must use the accepted revised automatic bridge.

## External Side Effects

- Allowed: one GKD task worktree/branch/PR, standard repository CI, isolated test roots and read-only GitHub observations.
- Forbidden: production `~/.codex`, AIO, host/session storage, Secrets, paid runners, settings, tags, Releases and unrelated PRs.

## Action Mode

- `implement_and_merge_on_acceptance` under the existing GKD core repair authorization; only trusted main may accept, merge, release or clean up.

## Implementation Notes

- Prefer an additive protocol discriminator and narrow adapters over broad task-state rewrites. Reuse canonical digest, CAS, journal, bundle verification and fixed-head validation helpers.
- Run the registered verifier from the explicit base SHA. Commit the delivery document before any final delivery transition if the bootstrap exception is replaced by a claimable route; otherwise record the exception in delivery and acceptance without manufacturing state.
