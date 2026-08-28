# GKD-O4 Retrospective

## What Worked

- The implementation demonstrated the intended default/historical scope separation and preserved watcher fail-closed behavior.
- Fixed-head acceptance reproduced default and historical test counts, negative result handling, bundle separation and host-capability diagnostics.
- Rework and rejection facts were preserved; no stale attempt was accepted or merged.

## Workflow Defects

- Planning-document digests are frozen at claim time, but no trusted transition can update requirements during an implementing rework. A document-only correction therefore makes status, block and rework unreadable.
- The state validator requires wall-clock history ordering across processes. Host clock differences produced a delivered event earlier than its claim, making a valid candidate structurally invalid and preventing rework.
- Delivery declarations can drift from deterministic result manifests unless the delivery command consumes the generated manifest directly; both candidates exposed this risk.
- Fixed-head CI failure and invalid task state can coexist, but the current rework path cannot preserve both through a terminal rejected transition.

## Follow-up

- Create a separate core workflow task for a persisted logical clock or monotonic event sequence, a trusted planning-document refresh transition, and delivery-time manifest binding.
- Add preflight checks before claim/delivery for document digests, clock ordering and result declarations. Only after that task is accepted should O4 restart from a fresh base.
