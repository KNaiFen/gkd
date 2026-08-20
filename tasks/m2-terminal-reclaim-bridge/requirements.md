# GKD-M2-F Requirements

## Goal

Close the two trusted-host lifecycle gaps proven by real automatic execution: a fresh attempt for the same task needs a non-colliding deterministic host task name, and trusted main needs a narrow way to bind a real terminal child result to reclaim an implementing claim without candidate or public-CLI authority.

## User Decisions

- Continuous automatic execution through M3, M4, and M5 includes this minimal prerequisite without further confirmation.
- Execute through one accepted six-gate automatic route and exactly one `gkd_executor`, Sol/xhigh/workspace-write, `fork_turns=none`; no worker, alternate role, downgrade, nested Codex, reuse, retry, or fallback.
- Keep the change generic. Do not special-case GKD-M2-E, GKD-M3-A, any PR, repository, agent identity, epoch, username, or path.
- Use `implement_and_merge_on_acceptance`; executor implements and delivers, while trusted main alone accepts, merges, installs, reclaims superseded attempts, and cleans up.
- Production `~/.codex`, AIO, paid runners, Secrets, settings, tags, Releases, and M3 product features remain out of scope.

## Scope

- Derive a canonical bounded host-safe `spawnRequest.taskName` from task identity plus current automatic attempt identity; the same prepared offer is stable and a later epoch/offer cannot collide.
- Reconstruct and require that exact task name during claim; old-attempt, invented, truncated, fallback, multiple-spawn, wrong-role, wrong-fork, or wrong-runtime facts fail before writes.
- Add a trusted-main-only bridge method that validates a normalized real host terminal/error result against the exact active claim, offer, agent/task name, session digest, role/config/bundle/route and terminal timestamp, then invokes the existing atomic reclaim transaction through an in-memory one-shot evidence provider.
- Keep candidate-facing CLI/default library reclaim unavailable; never expose a terminal writer seam through public automatic CLI or persist raw host messages, agent/thread IDs, prompts, transcripts, or capabilities.
- Add focused bridge/rework/reclaim L1/L2 tests, mutations, deterministic evidence, documentation, manifest/lock regeneration, and versioned verifier coverage.

## Non-Goals

- Reusing/deleting a completed host agent, automatic retries, concurrent executors, fallback names, hand-editing state, weakening claim or rework invariants, or adding daemon/IPC/signing/secret infrastructure.
- Implementing M3-A policy/monitor, M3-B resource/scanner, M3-C review/Skills, finalization, release, production installation, AIO integration, or historical live probes.

## Acceptance Criteria

1. Initial and later automatic attempts return deterministic ASCII task names with a documented length/character contract; distinct attempt identity cannot collide for one task.
2. Names contain no raw capability, nonce, agent/thread identity, path, username, credential-shaped data, owner, PR, or environment fact.
3. `prepare` and `claim` bind the same exact name; every material task/attempt/name mutation fails before activation, receipt, runtime, or tracked writes.
4. One normalized terminal result can reclaim only its exact currently implementing claim; active, unrelated, stale, replayed, wrong task/name/identity/session/role/config/bundle/route/time or malformed results write nothing.
5. Successful reclaim atomically revokes the active offer, retires the exact claim, increments epoch and returns authorized planning; old offer/envelope/activation/claim/task name remain unusable.
6. Candidate/public CLI/default library cannot manufacture terminal evidence or reclaim; trusted bridge retains no fallback and does not persist raw host result content.
7. Rework/revoke followed by a fresh prepare/claim and terminal reclaim followed by another fresh prepare/claim are covered end to end.
8. Existing acceptance, delivery, activation receipts, recovery, project staging, task core, role routing, runtime bridge and M2-D contracts remain valid.
9. Complete verifier and mutations pass; two clean evidence generations are byte-identical, execution/candidate bundle digests remain separate, protected production/AIO surfaces do not drift, and historical live tests do not run.
