# ADR-003: Separate closeout routing from the main workflow

## Status

Accepted

## Date

2026-09-05

## Context

`gkd-main` previously carried the detailed procedure for archive creation, cleanup commits, worktree and branch removal, restoring `main`, and the final user report. That made the orchestration Skill carry both routing decisions and a long operational procedure.

## Decision

Introduce `gkd-closeout` as the single procedural Skill for the post-review closeout of delegated and direct-main tasks. `gkd-main` keeps the entry conditions, authorization decisions, review conclusion, and success/blocking judgment, then routes to the closeout Skill after review passes.

The closeout Skill does not become a state machine and does not infer authorization for commits, merges, releases, remote branch deletion, or other external writes. It stops and preserves the worktree whenever a prerequisite or authorization is missing.

The configured roles are updated to `gpt-6-astra` / `xhigh` for `gkd_execute` and `gkd_accept`, and `gpt-5.6-terra` / `medium` for `gkd_ci_monitor`.

## Consequences

The main routing Skill is shorter and the closeout procedure has one maintained source. The final delivery of this repository (commit, release, and installation into the active Codex directory) remains a separate release operation and is not part of the task closeout Skill.
