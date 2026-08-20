# GKD-M2-C Requirements

## Goal

Make the already approved explicit automatic route operational without installing the bundle into production `~/.codex`. Deliver a deterministic project-scoped role staging surface and a trusted-main orchestration bridge that binds one exact host `gkd_executor` spawn to the existing offer, activation, claim, wait, delivery, and independent acceptance contracts.

## User Decisions

- M2-A role/route/activation core and the user-accepted M2-B one-hour wait gate remain valid and bind execution bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`.
- This is the last manual top-level bootstrap task because the current session cannot discover a custom role that was not staged before session startup. Do not use a generic worker, nested `codex exec`, model downgrade, alternate role, or fallback.
- After M2-C is accepted, a fresh trusted main session may automatically execute M3/M4/M5 with exactly one `gkd_executor` per task and native one-hour waits.
- Keep the workflow pragmatic. The trusted-main bridge is a workflow authority boundary, not same-OS-user security isolation; do not add signing, keys, daemon, IPC, credential copying, session databases, or transcript parsing.
- Production `~/.codex`, AIO, paid runners, Secrets, repository settings, tags, Releases, and M3 product features remain outside this task.

## Scope

- Promote deterministic project-scoped role/config/Skill staging from the M2 test fixture into a supported canonical main-only surface. It must use canonical role and Skill sources, validate bundle/role/config/Skill digests, and target only an explicit non-production trusted project root.
- Stage the minimum parent/executor project layer needed for a fresh main to discover exact `gkd_executor` while allowing that executor to operate on the registered candidate worktree without contaminating candidate Git state.
- Add a main-only orchestration bridge that consumes an exact successful host spawn result, validates task name, `agent_type=gkd_executor`, `fork_turns=none`, unique agent identity, role/config/execution-bundle facts and offer window, then records trusted activation and performs the existing exact envelope claim with the existing provider seam.
- Bind the deterministic route decision to the automatic offer so an arbitrary `route=automatic` string cannot bypass the six readiness gates.
- Distinguish the pinned execution bundle digest used to launch/claim from the candidate output bundle digest produced by implementation. Candidate source changes must not retroactively invalidate the in-flight executor; changing the execution bundle requires a separately accepted runtime upgrade.
- Keep candidate-facing `gkd-task` activation/claim and default library paths fail-closed. The bridge belongs only to the main role context; deliberate same-user private API or file tampering remains a non-goal.
- Add L1/L2 contracts, temporary project fixtures, generic host-spawn normalization, documentation updates, deterministic evidence, retained M1/M2 regressions, and manifest/lock regeneration.

## Non-Goals

- Implementing `.gkd` CI policy, fixed-head monitoring, resource presets, billing recommendations, secret scanning, review core, `gkd-optimize-ci`, or `gkd-review-remediation`.
- Installing or modifying production user configuration, authentication, global AGENTS, user Skills, legacy roles, or Codex session storage.
- Reading rollout JSONL/session databases, copying auth state, adding an alternate `CODEX_HOME`, or proving same-user process isolation.
- Allowing the executor to accept, merge, archive, clean up, create another executor, or substitute another role.
- Re-running the real one-hour M2-B wait; its accepted user decision and M2-A fake-clock contracts remain authoritative.

## Acceptance Criteria

1. Two clean temporary staging roots produce byte-identical project config, exact executor role TOML, minimum parent/executor Skills, inventory, modes, and digest report from the pinned execution bundle.
2. Staging rejects symlinks, traversal, source/target overlap, production home, undeclared files, unknown role/config fields, digest drift, non-Git targets, and existing conflicting project configuration before mutation; failure restores exact preimages or leaves a recoverable freeze result.
3. A fresh-project fixture proves exact `gkd_executor` discovery and candidate-worktree access without tracked or untracked staging artifacts in the candidate. No user config, auth, session, AIO, or production path bytes change.
4. The bridge accepts only one exact successful spawn bound to the current task, offer, envelope, route decision, agent identity, role/config/execution-bundle digests and offer window. Missing, stale, duplicate, cross-task, wrong role/task/fork, fallback, or drifted facts fail before activation or claim writes.
5. The successful path deterministically proves route decision → automatic offer → handoff envelope → trusted activation → exact claim → delivery. Candidate-facing CLI/default library claim remains `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE` and byte-unchanged.
6. Automatic offers persist and validate the route decision digest and all six readiness gates. Manual route remains the default and no failed automatic attempt creates a manual claim or generic-worker fallback.
7. Execution bundle identity is immutable for an in-flight task while candidate output bundle changes are allowed and separately reported. Tests reject silently replacing the execution bundle between offer, activation, claim, wait, and delivery.
8. Main-only orchestration output is canonical, path-minimized, and contains no prompt, transcript, credentials, capability, raw session/thread identity, or host configuration. Agent identity is retained only where runtime claim fencing requires it and is not committed as evidence.
9. README, canonical README, gkd-main/gkd-execute contracts, schemas, source manifest and lock describe the operational automatic route without claiming production installation or M3 completion.
10. Dedicated M2-C contracts and all retained task-core, role-routing, foundation, watcher-core, and live-negative regressions pass; two evidence generations are byte-identical and protected production/AIO surfaces do not drift.
