---
name: gkd-main
description: Coordinate a manual-first Agent task with a plan, Git worktree, progress report, and main-agent review.
---

# GKD Main

Use the task worktree and three human-readable Markdown files as the normal coordination surface.

1. Read the applicable `AGENTS.md` and the worktree's `plan.md` before editing.
2. Ensure `plan.md` states the goal, worktree, behavior constraints, scope, non-goals, and completion conditions. Do not create a machine state copy.
3. Start the execution session with the prompt in `docs/manual-workflow.md`. Work only in the declared worktree and update `progress.md` when making decisions, reaching milestones, or becoming blocked.
4. Let the execution agent finish and stop. Do not ask it to accept, merge, archive, or operate another task.
5. Review the Git diff, recent history, `plan.md`, and `progress.md`. Record the decision in `review.md`.
6. If the result is incomplete, edit `plan.md` or `review.md` with the next concrete request and continue in the same worktree. A new session resumes by reading the same files.
7. If the result is complete, use ordinary Git operations to keep or merge the branch. Run only the local checks that the plan calls for and report anything not run.

Do not require `gkd-task`, offer/claim/activation/receipt JSON, CAS arguments, fixed-head acceptance, or machine-facts documents for a normal manual task.
