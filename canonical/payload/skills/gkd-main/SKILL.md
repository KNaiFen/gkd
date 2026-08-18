---
name: gkd-main
description: Coordinate canonical GKD task planning, manual or explicit automatic routing, fixed-head acceptance handoff, and closeout from a trusted main checkout.
---

# GKD Main

Use durable task Markdown for decisions and `gkd-task` output for machine state.

1. Read the applicable `AGENTS.md`, task requirements, plan, and execution contract.
2. Use `gkd-task status` and `doctor`; never hand-edit task JSON, offers, claims, receipts, journals, or activation records.
3. Default to manual handoff. Request automatic routing only through `gkd-role route` with explicit readiness facts. Never substitute `worker` or another command.
4. For automatic execution, spawn only `gkd_executor`, obtain trusted activation evidence, then let that exact role claim the exact envelope.
5. Feed each host result to `gkd-role wait-transition`. When it returns `wait_again`, immediately call `wait_agent(timeout_ms=3600000)` for the same executor with no commentary, analysis, repository/CI reads, or other tool call.
6. Stop on terminal/error/drift. On `deadline_timeout`, interrupt the bound executor exactly once and report the single timeout result.
7. Route a delivered fixed head to `gkd_acceptor`; only trusted main owns archival and cleanup.

Automatic routing remains unavailable unless fixed M2-B fresh-runtime evidence is present and bound to the installed bundle digest.
