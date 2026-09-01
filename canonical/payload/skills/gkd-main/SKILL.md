---
name: gkd-main
description: Coordinate canonical GKD task planning, manual or explicit automatic routing, fixed-head acceptance handoff, and closeout from a trusted main checkout.
---

# GKD Main

Use durable task Markdown for decisions and installed CLI output for machine state.

1. Read the applicable `AGENTS.md`, task requirements, plan, and execution contract.
2. Start from a trusted checkout with `gkd-main inspect` or `preflight`; use the task selector when needed and let the CLI resolve repository, worktree, runtime, policy, bundle, and lifecycle facts.
3. Keep the development stage current with `gkd-main stage --production-root <explicit-non-production-root>`; use `--refresh` only when replacement is intended. The command derives the canonical source, digest, ownership, and inventory, and fails closed on drift. Never stage a production home or candidate worktree.
4. Use `gkd-main planning create` with the three reviewed Markdown contents, then use its selector for inspection. Do not hand-write task, route, offer, claim, receipt, activation, inventory, or wait JSON.
5. Choose manual or automatic routing explicitly. For automatic work, the trusted facade verifies the project stage and policy, seals the spawn handoff, and consumes one direct `gkd_executor` acknowledgement. Do not reconstruct roots, digests, CAS values, argv, identities, or runtime facts.
6. When the trusted wait transition returns `wait_again`, immediately call `wait_agent(timeout_ms=3600000)` without extra inspection. Stop on terminal, error, drift, or deadline timeout.
7. Deliver through the trusted facade. Route the delivered fixed head to an independent acceptor; merge or rework remains an explicit trusted-main decision.
8. Only trusted main owns lifecycle transitions, merge, archival, and cleanup.
