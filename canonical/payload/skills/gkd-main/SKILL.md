---
name: gkd-main
description: Coordinate a manual-first Agent task with a plan, Git worktree, progress report, and main-agent review.
---

# GKD Main

This is the only active GKD Skill. Use the task worktree and three human-readable Markdown files as the coordination surface.

1. Read the applicable `AGENTS.md` and the worktree's `plan.md` before editing.
2. Ensure `plan.md` states the goal, worktree, and behavior constraints. Add scope, non-goals, or completion conditions only when they clarify this task; do not create a machine state copy.
3. Start the execution session with the prompt in `docs/manual-workflow.md`. Work only in the declared worktree and update `progress.md` when making decisions, reaching milestones, or becoming blocked. The execution session is a normal Codex session, not a GKD role or lifecycle.
4. Let the execution agent finish and stop. Do not ask it to accept, merge, archive, or operate another task.
5. Review the Git diff, recent history, `plan.md`, and `progress.md`. Record the decision in `review.md`.
6. If the result is incomplete, edit `plan.md` or `review.md` with the next concrete request and continue in the same worktree. A new session resumes by reading the same files.
7. If the result is complete, use ordinary Git operations to keep or merge the branch. Run only the local checks that the plan calls for and report anything not run.

Do not route normal work to `gkd-task`, `gkd-role`, `gkd-execute`, `gkd-accept`, `gkd-ci-monitor`, or any migration command. Do not require offer/claim/activation/receipt JSON, CAS arguments, fixed-head acceptance, or machine-facts documents for a normal manual task.
