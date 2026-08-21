# GKD-M3-B Requirements

## Goal

Add generic resource-aware CI planning and a fixed-scope secret scanner wrapper for GKD without hard-coding a consumer repository, machine, runner, billing source, or secret value.

## User Decisions

- Continue automatic execution through M3, M4 and M5 with one exact accepted `gkd_executor` route.
- Keep M3-B limited to resource/artifact classification, runner/billing facts and scanner boundaries; do not implement M3-C review/Skills.
- Do not modify production `~/.codex`, AIO, paid runners, Secrets, GitHub settings, tags or Releases.

## Scope

- Define deterministic zero/bounded/build-or-unknown artifact classes and resource-constrained, standard and high-capacity presets.
- Parse visibility, runner, policy and billing facts and provide speed-first, balanced and cost-aware recommendations with runtime price verification.
- Provide a fixed scanner wrapper with redacted results and explicit diff/PR/artifact input boundaries; credential exposure is a terminal finding.
- Add generic schemas, hermetic fixtures, mutation coverage, deterministic evidence, docs and bundle declarations.

## Non-Goals

- M3-A policy/monitor changes, M3-C shared review core or Skills, AIO adapters, production installs, branch protection, paid services or historical live probes.

## Acceptance Criteria

1. Artifact/resource classification and presets are deterministic and fail closed on unknown or peak-disk violations.
2. Runner/billing facts and recommendations are schema-bound, source-aware and never claim unverified prices.
3. Scanner inputs are bounded to declared diff/PR/artifact surfaces; output is redacted and credential exposure stops the result.
4. Reusable mechanisms contain no repository, owner, machine path, username, token or secret constants.
5. Local verifier, retained contracts, focused tests, mutations, two byte-identical evidence runs and candidate bundle verification pass.
