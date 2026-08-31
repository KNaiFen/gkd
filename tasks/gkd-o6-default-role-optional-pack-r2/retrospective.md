# GKD O6 Default Role And Optional Pack R2 Retrospective

## Result

O6 separates the default execution loop from opt-in CI and review capabilities. Core stays minimal and deliverable by default; optional capabilities must be explicitly selected, staged, verified, and enabled in the generated role configuration.

## Lessons

- A self-hosted delivery consumer must understand a new result format before a producer can emit it. PR #50 was a necessary compatibility step.
- Installing optional Skill files is insufficient. The selected set must also determine effective role TOML and all role/config/inventory digests.
- Compatibility testing must exercise source and installed entry points. An installed legacy manifest test cannot prove legacy source generation remains valid.
- Each rework epoch retires the prior authorization, offer, claim, receipt, and review; it requires refreshed planning and a new approval before execution.

## Next

Create O7 from merge `71c90ffdd3e3250be33746acd465b2b3e58de053` with a fresh execution bundle.
