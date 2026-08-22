# GKD-R1 Plan

## Goal

Restore a truthful release path for the accepted M2-K bundle by separating reusable semantic
version validation from a prior patch-release literal and creating a `0.1.2` release candidate.

## User Decisions

- Continue in dependency order: release the accepted M2-K bundle before isolated project restage
  and before any AIO consumer work.
- Fix the reusable mechanism with strict stable semantic versions; this task's concrete release
  version is `0.1.2`.
- Use a narrowly documented manual bootstrap route because the verified staged bundle is still
  `0.1.1`; no automatic lifecycle record is honest for this self-hosting upgrade.

## Behavior And Defaults

- A release candidate validates one stable `major.minor.patch` string and promotion derives
  `v<that-version>` from the immutable candidate record.
- `source.toml` is the canonical declaration for `0.1.2`; generated manifest/lock bind all
  payload bytes and metadata to the resulting candidate digest.
- Historical records keep their recorded version and validator path. Fresh candidates can use
  the same generic rule without accepting pre-release or range syntax.

## Scope

- Update the release core/verification fixtures/tests, canonical version declaration and generated
  metadata only as needed for strict generic version propagation.
- Add deterministic evidence, delivery documentation and one PR; validate with the approved
  repository verifier from the registered base SHA.

## Non-Goals

- No release side effects in the executor path, no production/AIO mutation, no GitHub settings,
  no rework of release layers or automatic bridge, and no support for prerelease/build metadata.

## Acceptance Criteria

- Version validation has focused positive, negative and mutation coverage; exact tag propagation
  is demonstrated for `0.1.1` compatibility and `0.1.2` candidate use.
- Canonical generation is deterministic; bundle install/verify and all versioned regressions pass.
- Evidence is path-minimized and byte-identical across two clean temporary roots.
- Trusted-main independent review, policy-backed fixed-head CI and exact merge are required before
  any post-merge tag, Release or restage.

## Compatibility

- Existing release records that contain `0.1.1` remain valid under the strict stable-version rule.
- No older bundle is altered and no consumer pin moves during candidate execution.

## Security And Data

- Only public version strings, canonical digests and redacted evidence metadata are persisted.
- Unknown fields, malformed versions and source/lock inconsistencies fail before release records
  or installation writes.

## Migration

- This is a source-release upgrade, not a production migration. After post-merge release gates
  pass, trusted main will separately install the published `0.1.2` asset into an isolated root
  and stage a project from that exact digest.

## Public Interfaces

- `gkd-release` continues to expose side-effect-free candidate/promotion records; only its
  version validator becomes generic within stable semantic-version syntax.

## Execution Route

- Use one manual trusted-main bootstrap candidate because current staging is bound to the old
  release. The execution session works only in its registered worktree, commits, pushes, writes
  delivery and stops at an exact fixed head. It does not create automatic task runtime facts.

## External Side Effects

- Allowed: one GKD worktree/branch/PR, isolated temporary evidence/install roots and standard
  repository CI. Forbidden during execution: tag, Release, production, AIO, sandbox, settings,
  Secrets and paid runners.

## Action Mode

- `implement_and_merge_on_acceptance` under the user's 2026-08-23 continue authorization; only
  trusted main may merge and later invoke separately verified post-merge release actions.

## Implementation Notes

- Prefer one reusable strict regex/helper at the release-core boundary. Keep the change additive
  in behavior for `0.1.1`, regenerate metadata with canonical tooling, and do not invent a new
  packaging layer or release service.
