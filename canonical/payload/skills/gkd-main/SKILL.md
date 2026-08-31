---
name: gkd-main
description: Coordinate canonical GKD task planning, manual or explicit automatic routing, fixed-head acceptance handoff, and closeout from a trusted main checkout.
---

# GKD Main

Use durable task Markdown for decisions and `gkd-task` output for machine state.

1. Read the applicable `AGENTS.md`, task requirements, plan, and execution contract.
2. Begin normal task location with installed `gkd-main inspect` or `preflight`. From trusted main use its explicit task selector; do not reconstruct candidate/runtime roots, repository, branch, task path, status/doctor argv, capabilities or envelopes from prose. Use `gkd-main planning create` only with the three actual reviewed Markdown contents, and pass its selector to `planning inspect` rather than handing over a package path.
3. Use `gkd-task status` and `doctor` only when the lower-level lifecycle operation requires their exact trusted context; never hand-edit task JSON, offers, claims, receipts, journals, activation records, or project inventories.
4. Default to manual handoff. A first consumer must commit its strict `.gkd/policy.json` before `gkd-task bootstrap`; bootstrap records that binding. Automatic routing requires accepted M2-B wait evidence and a `gkd-role project-verify` result from the trusted base checkout, bound to the exact accepted execution bundle and the same policy record. Never stage production `~/.codex` or the candidate worktree.
5. Obtain the six-gate decision from `gkd-role route` with the verified project-policy record, then invoke the supported `TrustedMainRuntimeBridge.prepare` library interface with the trusted project and production roots. Spawn exactly one direct `gkd_executor` with the returned request leaf and `fork_turns=none`; never substitute `worker`, another role, nested Codex, downgrade, or fallback.
6. Normalize only one successful host acknowledgement: one direct `gkd_executor` call and `fork_turns=none`, with the host's canonical `/root/<requested-task-name>` preserved as the task identity. Do not strip, reconstruct, or substitute it, or reconstruct agent IDs, thread digests, effective model/effort/sandbox/runtime, timestamps or fallback evidence the host did not return. The bridge binds configured role values from the verified bundle and derives a non-secret executor-attempt handle. Use `TrustedMainRuntimeBridge.recover` only after an interrupted claim transaction or receipt completion. Public `gkd-role automatic-*`, candidate `gkd-task claim`, and default task-library claim paths are unavailable trust boundaries and must remain byte-unchanged on rejection.
7. Feed the executor-attempt handle to `gkd-role wait-transition`. When it returns `wait_again`, immediately call `wait_agent(timeout_ms=3600000)` with no commentary, analysis, repository/CI reads, or other tool call.
8. Stop on terminal/error/drift. If the host terminal/error event is not machine-bound to the executor task name, block the task for manual recovery; do not call terminal reclaim. On `deadline_timeout`, interrupt the bound executor task name exactly once and report the single timeout result.
9. Keep the execution bundle digest immutable through wait and delivery. Treat the candidate output bundle digest as a separate deliver input.
10. Route a delivered fixed head to `gkd_acceptor`. If canonical independent review rejects it, invoke only `gkd-task rework` from a clean synchronized trusted main checkout with the exact delivered head, PR snapshot, review, candidate worktree, and runtime root. Never hand-edit or reuse the retired offer, activation, envelope, or claim; create a fresh automatic offer and claim after rework.
11. Only trusted main owns merge, archival, and cleanup.
