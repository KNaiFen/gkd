# GKD-R2 Requirements

## Goal

Repair the post-merge L3 release-gate contract so it requires and records only
facts that the current trusted-main host can actually observe, without claiming
a fresh executor identity, child lifecycle, or effective runtime setting that
the host does not expose.

## User Decisions

- The user selected the route that revises GKD's trust contract to match facts
  the current host can provide, rather than fabricating missing runtime facts.
- The untagged `0.1.2` R1 merge must not be promoted while its L3 prerequisite
  requires unavailable facts. Its source version remains unpublished; this task
  produces its replacement release candidate before any restage or AIO work.
- The currently published `v0.1.1`, production installation, and AIO adoption
  are outside this task and must remain unchanged.

## Scope

- Replace the L3 fresh-executor trace requirement with an explicitly
  trusted-main-owned, post-merge, read-only evaluation record bound to the
  release source SHA and immutable release-candidate inputs.
- Reject legacy-shaped L3 records and all substituted source, candidate,
  traceability, or effect-boundary inputs; update release fixtures, focused
  tests, generated metadata, and deterministic evidence accordingly.
- Keep L4 canary, assets, tag/Release writes, automatic bridge, task lifecycle,
  production state, and AIO state unchanged during candidate execution.

## Non-Goals

- No fresh-agent probe, custom-role spawn, executor claim, host identity,
  raw agent/thread/session receipt, effective-runtime assertion, retry, or
  fallback is introduced or inferred.
- No production `~/.codex` mutation, AIO write, GitHub settings, Secrets, paid
  runner, release tag, GitHub Release, or live sandbox canary occurs in this
  candidate task.
- No changes to semantic-version grammar, L0-L2/L4 behavior, release assets,
  or historical tags, Releases, evidence, and task runtime records.

## Acceptance Criteria

1. L3 accepts one canonical trusted-main, read-only evaluation record that is
   exact-source and exact-candidate bound, and it contains no executor role,
   child lifecycle, host identity, or effective runtime fields.
2. Any unavailable legacy L3 shape, non-read-only boundary, missing required
   observation, or substituted source/candidate/traceability fact fails closed.
3. Existing L4 marker/check validation, post-merge provenance, semantic-version
   propagation, and historical published records remain compatible.
4. Focused release contracts and the complete repository verifier pass; evidence
   produced in two disjoint temporary roots is byte-identical, while production
   and AIO protected snapshots remain unchanged.
5. Candidate execution stops at a fixed PR head with no tag, Release, live L3/L4
   promotion, production, AIO, or fabricated task runtime state. Only trusted
   main may independently accept, merge, and later run the revised live gate.
