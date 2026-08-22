# GKD-M5-C Requirements

## Goal

Repair the final M5 release gate so cross-repository L4 evidence binds the GKD release SHA through the canonical sandbox marker instead of equating unrelated Git commit SHAs, and so L3 has an explicit post-merge eval-only contract.

## User Decisions

- This remediation remains within frozen M5 verification and release-candidate scope.
- Use one exact automatic `gkd_executor`; no fallback, generic worker, tag, Release or production installation by the executor.

## Scope

- Model `releaseSourceSha` and `sandboxHeadSha` as distinct immutable facts.
- Verify the canonical `canary.json` at the fixed sandbox PR head binds the expected release SHA and bundle digest before accepting `GKD Canary`.
- Add an eval-only, redacted, exact-SHA L3 contract that has no source mutation, PR or task-lifecycle write surface.
- Cross-bind final promotion inputs to the release SHA, prebuilt assets, L3 record and L4 observation.

## Non-Goals

- No production Codex, AIO, Secrets, paid runner or GitHub settings changes.
- No actual sandbox execution, tag, Release, acceptance or merge by the executor.

## Acceptance Criteria

- Substituting either source SHA, sandbox head SHA, marker bundle digest, L3 record or L4 check result fails closed.
- Fake-GitHub and deterministic tests cover the new cross-repository observation and eval-only contracts.
- Trusted main can run one post-merge L3/L4 pass using the already-created sandbox PR and create one same-source-SHA `v0.1.0` tag and Release without rebuilding assets.
