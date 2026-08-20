# GKD-M2-E Requirements

## Goal

Close the host integration gap exposed by the first real delivered rework: after the old direct executor has reached terminal, a fresh automatic attempt for the same task must receive a new deterministic exact task name so the host can perform the one allowed direct spawn and the trusted bridge can bind a fresh activation and claim.

## User Decisions

- Continuous automatic execution through M3, M4, and M5 includes this narrow prerequisite repair without another confirmation.
- Execute this task through the accepted six-gate automatic route with exactly one `gkd_executor`, Sol/xhigh/workspace-write, `fork_turns=none`, and no worker, alternate role, downgrade, reuse, nested Codex, or fallback.
- Keep the change generic and deterministic. Do not special-case GKD-M3-A, PR #8, an agent ID, repository, username, host path, or current epoch value.
- Use `implement_and_merge_on_acceptance`; executor may implement, verify, push, maintain one PR, and repair in-scope CI, while trusted main alone accepts, merges, installs the accepted bundle, and cleans up.
- Production `~/.codex`, AIO, paid runners, Secrets, repository settings, tags, Releases, and M3 policy/resource/review functionality remain outside this task.

## Scope

- Make `TrustedMainRuntimeBridge.prepare` return a deterministic host task name whose identity is bound to the task and the current automatic attempt, so a later epoch cannot collide with an already terminal prior executor.
- Keep the name stable for the same prepared offer and make `claim` validate that exact returned name; wrong task, epoch, offer, route, or name must fail before activation, receipt, task, or runtime writes.
- Preserve one direct spawn per automatic attempt, exact `gkd_executor`, exact returned task name, `fork_turns=none`, and the existing role/config/bundle/route/model/reasoning/sandbox/runtime bindings.
- Add focused runtime-bridge and rework integration contracts, mutation coverage, deterministic evidence, documentation, manifest/lock regeneration, and the existing repository-versioned verifier coverage.

## Non-Goals

- Reusing or reactivating a completed host agent, changing the host agent API, deleting old host agents, adding a fallback task name, retrying failed spawns, or permitting multiple concurrent executors.
- Changing task IDs, task branch names, offer/claim/activation semantics, accepted history, rework authorization, runtime identity storage, or public automatic CLI trust boundaries beyond what the new name binding strictly requires.
- Implementing M3-A policy/monitor fixes, M3-B resources/scanner, M3-C review/Skills, finalization, release behavior, production installation, AIO integration, or historical live probes.

## Acceptance Criteria

1. The initial automatic attempt and every later rework/revocation epoch return deterministic, canonical, bounded task names; distinct attempt identity cannot produce the same host task name for the same task.
2. The returned task name contains no raw agent/thread identity, capability, nonce, machine path, username, repository owner, PR number, or secret-shaped value.
3. `prepare` writes one offer and returns one exact spawn request; repeated read-only derivation for that offer is stable, while a new epoch produces a different name.
4. `claim` accepts only one normalized successful host spawn with exact `gkd_executor`, exact returned task name and `fork_turns=none`; old-attempt, invented, truncated, alternate-role, fallback, and multiple-spawn facts fail before writes.
5. Rework followed by a fresh automatic prepare/claim is covered end to end without reusing the retired offer, envelope, activation, claim, or task name.
6. Existing non-rework automatic bridge behavior, activation/claim receipts, recovery, task core, role routing, project staging, acceptance, and delivered rework contracts remain valid.
7. Candidate-facing public automatic CLI and default task claim paths remain fail-closed and byte-unchanged on rejection.
8. The complete versioned verifier and dedicated mutations pass; two clean evidence generations are byte-identical, execution and candidate bundle digests remain separate, protected production/AIO surfaces do not drift, and no historical live experiment runs.
