# GKD-R2 Plan

## Goal

Make the final L3 gate truthful: it must be an explicit trusted-main evaluation
of observable release inputs, not a schema-shaped assertion that a fresh
executor session existed when this host cannot verify one.

## User Decisions

- Trust is limited to facts available to the host. Missing child identity,
  terminal, and effective runtime data are not replaced with placeholders.
- The existing untagged `0.1.2` candidate is superseded before publication; the
  release version remains `0.1.2` because no `v0.1.2` tag or Release exists.
- This self-hosting repair uses a documented manual bootstrap exception because
  the installed/staged release is `v0.1.1`; it must not create automatic
  lifecycle state for itself.

## Behavior And Defaults

- L3 is a versioned trusted-main post-merge evaluation record with an explicit
  read-only effect boundary, exact release SHA, and digest-bound canonical
  release inputs. It states neither an executor role nor a child event stream.
- The record is validated independently before it can enter final provenance.
  Any mismatch in source SHA, candidate digest, traceability digest, or the
  fixed no-write boundary is terminal.
- L4 remains the only live GitHub canary and keeps its existing sandbox marker,
  fixed head, and successful-check requirements.

## Scope

- Update only release-core L3 validation/building, final-gate integration,
  fixtures/tests, release evidence, and generated canonical metadata required
  by the revised contract.
- Produce deterministic candidate evidence, run the complete verifier from the
  registered base, write delivery, and submit one GKD PR.

## Non-Goals

- Do not change automatic bridge host acknowledgement, role routing, task
  lifecycle, L4 semantics, asset format, source version, production install,
  AIO integration, GitHub settings, Secrets, paid runners, tags, Releases, or
  a live canary in executor scope.

## Acceptance Criteria

- The canonical L3 record contains only trusted-main-observable release-gate
  facts and rejects all source/candidate/boundary substitutions.
- M5 post-merge provenance continues to require independently validated L3 and
  L4 records bound to the exact same source SHA and bundle digest.
- Focused release tests, full verifier, manifest generation, and isolated
  bundle install/verify pass deterministically.
- Independent fixed-head review and policy-backed PR CI pass before trusted
  main may use the revised post-merge gate.

## Compatibility

- `v0.1.0` and `v0.1.1` releases remain historical facts and are not re-parsed,
  rewritten, or re-promoted.
- The only unpublished source version remains `0.1.2`; this task replaces its
  unpublishable candidate evidence with a newly generated candidate digest.

## Security And Data

- Persist only canonical public source/digest/boundary facts. Do not persist
  raw session data, agent/thread identifiers, model receipts, prompts, machine
  paths, or task capabilities.
- Unknown fields and all drift fail before a post-merge record or promotion
  request is accepted.

## Migration

- No user-directory or consumer migration occurs. After a successful release,
  a later trusted-main step may isolate-install and restage the exact published
  bundle before a separately scoped AIO task.

## Public Interfaces

- `gkd-release` retains side-effect-free candidate and post-merge validation.
  Its L3 record changes from an executor-forward-eval shape to a
  trusted-main-observed release-evaluation shape with an explicit schema bump.

## Execution Route

- Use one manual trusted-main bootstrap candidate. Work is confined to the
  registered worktree; it commits, pushes, writes delivery, and stops at an
  exact fixed head. No automatic offer, activation, claim, receipt, or delivery
  task state is generated for this bootstrap repair.

## External Side Effects

- Allowed: one GKD worktree/branch/PR, isolated temporary evidence/install
  roots, and standard repository CI. Forbidden during execution: tag, Release,
  production, AIO, sandbox canary, settings, Secrets, and paid runners.

## Action Mode

- `implement_and_merge_on_acceptance` under the user's 2026-08-23 authorization
  to continue the repair. Only trusted main may merge and subsequently perform
  separately verified post-merge release actions.

## Implementation Notes

- Keep the change narrow and make the new L3 data model self-describing. Reuse
  canonical digest helpers and existing final-gate composition. Add focused
  negative/mutation tests for every removed unavailable field and every
  retained observable binding; do not add a compatibility alias that permits
  new records to claim legacy executor facts.
