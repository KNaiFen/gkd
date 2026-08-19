---
name: gkd-main
description: Coordinate canonical GKD task planning, manual or explicit automatic routing, fixed-head acceptance handoff, and closeout from a trusted main checkout.
---

# GKD Main

Use durable task Markdown for decisions and `gkd-task` output for machine state.

1. Read the applicable `AGENTS.md`, task requirements, plan, and execution contract.
2. Use `gkd-task status` and `doctor`; never hand-edit task JSON, offers, claims, receipts, journals, activation records, or project inventories.
3. Default to manual handoff. Automatic routing requires accepted M2-B wait evidence and a `gkd-role project-verify` result bound to the exact accepted execution bundle. Never stage production `~/.codex` or the candidate worktree.
4. Obtain the six-gate decision from `gkd-role route`, then use `gkd-role automatic-prepare`. Spawn exactly one direct `gkd_executor` with the returned task name and `fork_turns=none`; never substitute `worker`, another role, nested Codex, downgrade, or fallback.
5. Normalize only the exact successful host spawn facts required by the spawn-result schema. Pass them to `gkd-role automatic-claim`; do not expose or persist its capability or raw agent/thread identity. If receipt completion was interrupted after claim commit, use `gkd-role automatic-recover`.
6. Feed each host result to `gkd-role wait-transition`. When it returns `wait_again`, immediately call `wait_agent(timeout_ms=3600000)` for the same executor with no commentary, analysis, repository/CI reads, or other tool call.
7. Stop on terminal/error/drift. On `deadline_timeout`, interrupt the bound executor exactly once and report the single timeout result.
8. Keep the execution bundle digest immutable through wait and delivery. Treat the candidate output bundle digest as a separate deliver input.
9. Route a delivered fixed head to `gkd_acceptor`; only trusted main owns archival and cleanup.
