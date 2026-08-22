# GKD-R1 Requirements

## Goal

Make the release-candidate contract version-aware rather than hard-coded to the
previous `0.1.1` release, then prepare a `0.1.2` candidate that can publish the
accepted M2-K host-observable bridge before any consumer restage or AIO adoption.

## User Decisions

- The user instructed trusted main to continue after M2-K acceptance. The recorded next
  gate is an independently accepted release upgrade and isolated project restage; an AIO
  consumer must never pin unpublished canonical source.
- This release is a patch upgrade to `0.1.2`. The reusable release mechanism must accept
  strict semantic versions supplied by the release candidate, not a new hard-coded literal.
- The current installed/project-staged `0.1.1` bundle is not the M2-K bundle, so this task
  uses one manual trusted-main bootstrap execution exception. It must not fabricate an
  automatic claim, activation, receipt or delivery state for itself.

## Scope

- Replace the `0.1.1` literal in release-candidate validation and L1 fixtures with a narrow
  strict semantic-version rule, preserving exact version-to-tag propagation.
- Bump canonical `source.toml` to `0.1.2`, regenerate canonical manifest/lock, and add focused
  positive/negative/mutation coverage for version validation and propagation.
- Produce deterministic candidate evidence and run the complete repository verifier from the
  exact registered base.
- Deliver one GKD PR for independent fixed-head acceptance. Post-merge trusted-main release
  gates, tag/Release, isolated bundle install and project restage are separate follow-up steps.

## Non-Goals

- No production `~/.codex` mutation, AIO write, consumer adapter, GitHub settings, Secrets,
  paid runner, release tag, GitHub Release, or sandbox canary during candidate execution.
- No release-policy redesign, version range negotiation, pre-release syntax, generic package
  manager, M3/M4/M5 feature work, or automatic-route fallback.
- No mutation of historical `v0.1.0` or `v0.1.1` records, tags, Releases, assets or evidence.

## Acceptance Criteria

1. Release-candidate and promotion records accept only strict `major.minor.patch` versions and
   propagate the exact supplied version to their tag; malformed, pre-release, missing or mutated
   versions fail closed.
2. The `0.1.2` canonical source/manifest/lock are internally consistent, deterministically
   installable and have a candidate bundle digest distinct from `v0.1.1`.
3. Existing `0.1.1` fixtures and historical record validation remain readable; the new mechanism
   does not rewrite legacy records.
4. Focused release contracts and the full versioned verifier pass; evidence from two disjoint
   temporary roots is byte-identical and production/AIO protected snapshots remain unchanged.
5. Candidate execution stops at a fixed PR head with no tag, Release, production, AIO or task
   runtime fabrication. Only trusted main may independently accept, merge, release and restage.
