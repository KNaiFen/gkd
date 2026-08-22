# GKD-M5-B Requirements

## Goal

Close the final stable-release gate left by M5-A: bind the one post-merge L3 forward evaluation and L4 public sandbox canary to an explicit immutable source SHA, then produce promotion inputs whose provenance cannot be split from that SHA.

## User Decisions

- Continue within the frozen M5 scope using the exact automatic executor route.
- Do not tag or create a GitHub Release until independent final acceptance succeeds.

## Scope

- Add exact-SHA L3 input, validation and redacted evidence contracts; a fixture-only placeholder SHA is insufficient.
- Add a trusted-main-only, sandbox-only L4 execution contract that binds the canary request, observed check result and source SHA without exposing a generic production writer.
- Correct release-provenance inputs so the final tag and GitHub Release can bind the real M5 remediation merge SHA.
- Preserve all M0-M5-A contracts and prohibit production Codex, AIO, Secrets, paid runners and GitHub settings changes.

## Non-Goals

- No production installation, AIO integration, paid runner, Secret or GitHub settings work.
- The executor does not perform the live canary, final acceptance, tag or Release.

## Acceptance Criteria

- The final trusted main can perform one L3 and one L4 pass using its exact post-merge SHA, and each resulting canonical record rejects a substituted SHA.
- The public sandbox action is constrained to `github.com/KNaiFen/gkd-sandbox` and the `GKD Canary` check.
- A release record, tag and Release asset provenance all reference the same immutable M5-B merge SHA; no asset rebuild is necessary during promotion.
