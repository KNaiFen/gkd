---
name: gkd-main
description: Coordinate canonical GKD task planning, manual or explicit automatic routing, fixed-head acceptance handoff, and closeout from a trusted main checkout.
---

# GKD Main

Use durable task Markdown for decisions and `gkd-task` output for machine state.

1. Read the applicable `AGENTS.md`, task requirements, plan, and execution contract.
2. Use `gkd-task status` and `doctor`; never hand-edit task JSON, offers, claims, receipts, journals, activation records, or project inventories.
3. Default to manual handoff. Automatic routing requires accepted M2-B wait evidence and a `gkd-role project-verify` result bound to the exact accepted execution bundle. Never stage production `~/.codex` or the candidate worktree.
4. Obtain the six-gate decision from `gkd-role route`, then invoke the supported `TrustedMainRuntimeBridge.prepare` library interface from this main role context. Spawn exactly one direct `gkd_executor` with the returned task name and `fork_turns=none`; never substitute `worker`, another role, nested Codex, downgrade, or fallback.
5. Normalize only the exact successful host spawn facts required by the spawn-result schema and pass them to `TrustedMainRuntimeBridge.claim`. Use `TrustedMainRuntimeBridge.recover` after an interrupted claim transaction or receipt completion. Public `gkd-role automatic-*`, candidate `gkd-task claim`, and default task-library claim paths are unavailable trust boundaries and must remain byte-unchanged on rejection; do not expose or persist capability or raw agent/thread identity.
6. Feed each host result to `gkd-role wait-transition`. When it returns `wait_again`, immediately call `wait_agent(timeout_ms=3600000)` for the same executor with no commentary, analysis, repository/CI reads, or other tool call.
7. Stop on terminal/error/drift. On `deadline_timeout`, interrupt the bound executor exactly once and report the single timeout result.
8. Keep the execution bundle digest immutable through wait and delivery. Treat the candidate output bundle digest as a separate deliver input.
9. Route a delivered fixed head to `gkd_acceptor`. If canonical independent review rejects it, invoke only `gkd-task rework` from a clean synchronized trusted main checkout with the exact delivered head, PR snapshot, review, candidate worktree, and runtime root. Never hand-edit or reuse the retired offer, activation, envelope, or claim; create a fresh automatic offer and claim after rework.
10. Only trusted main owns merge, archival, and cleanup.
