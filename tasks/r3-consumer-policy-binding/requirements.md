# GKD-R3 Consumer Policy Binding

## Goal

Make a first consumer repository's existing `.gkd/policy.json` a continuous, independently verifiable input from task bootstrap through project staging, routing, and trusted-main automatic preparation.

## User Decisions

The user selected the trust-contract route that relies only on facts the current host can actually provide. The accepted GKD v0.1.2 bundle is the fixed implementation baseline. AIO adoption is authorized, but it must not bypass a missing policy/origin binding by using a generic agent, a local fork, or hand-written coordination data.

## Scope

- Reuse the existing strict `.gkd/policy.json` schema and origin validation.
- Bind one validated policy digest and its repository/base/check facts to bootstrap state, project staging/verification, the six-gate route decision, and `TrustedMainRuntimeBridge.prepare`.
- Add deterministic negative and integration coverage for missing, substituted, origin-mismatched, and stale policy facts.
- Update GKD role and main documentation so the first consumer setup has one explicit deterministic entry point.

## Non-Goals

- Do not modify AIO product code, AIO workflows, AIO release policy, or AIO task history.
- Do not change the six route gates, invent host runtime facts, add a generic worker fallback, or weaken fixed-head acceptance.
- Do not create a production install, tag, Release, paid runner, Secret, or GitHub setting outside the existing release process.

## Acceptance Criteria

1. A policy used to bootstrap a consumer task is strictly parsed, origin-bound, copied or recorded through a deterministic bootstrap contract, and its digest is part of durable task identity.
2. `gkd-role project-stage` and `project-verify` independently bind the same policy repository, base branch, required checks, and digest to the staged project inventory.
3. A route decision still contains exactly the existing six gates, but its automatic form carries a validated project-policy binding instead of relying on agent-supplied text.
4. `TrustedMainRuntimeBridge.prepare` independently rejects a task, route decision, staged inventory, or live checkout whose policy facts do not all match.
5. All affected L0-L2 contracts pass, including substitution and first-consumer negative cases; no consumer-specific identity or absolute path enters the canonical bundle.
