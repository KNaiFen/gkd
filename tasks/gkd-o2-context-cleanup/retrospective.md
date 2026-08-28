# GKD-O2 Retrospective

## What Worked

- Context now has one current-state section, one next-task section and a historical index; duplicate AIO C and stale production/AIO wording were removed without rewriting history.
- Rework preserved the old rejection fact and required a new epoch, offer, claim and delivery before acceptance.
- Explicit real checkout paths made fixed-head CI observation succeed; executor/acceptor/main separation held.

## Workflow Friction

- The first acceptor attempt used a symlink alias and correctly stopped at `CHECKOUT_PATH_SYMLINK`; the workflow needs a canonical-path preflight before monitor invocation.
- The host default Python 3.9.6 still reports payload incompatibility as `FILESYSTEM_ERROR`; executor and acceptor prompts now need an explicit supported interpreter.
- The bootstrap contract copies requirements/plan/implementation but not execution.md, so the task template must state which execution material is durable and which is runtime-only.

## Follow-up

- O3 should add a machine-readable preflight for interpreter, canonical checkout path and route/monitor inputs before any fixed-head monitor attempt.
- Keep rework as a new epoch with a new offer/claim; never add in-attempt retries for path or environment failures.
