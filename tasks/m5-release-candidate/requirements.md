# GKD-M5-A Requirements

## Goal

Complete the frozen GKD verification/release-candidate capability: L0-L4 coverage, decision traceability, a stable `0.1.0` candidate bundle and release evidence suitable for a single trusted-main exact-SHA promotion after acceptance.

## User Decisions

- Continue with one exact accepted `gkd_executor`; no fallback, retry, role/model substitution or nested agent.
- Use `0.1.0` as the first stable GKD release-candidate version because the frozen plan authorizes the first version tag/Release but does not name one.
- Executor implements verification/release-candidate mechanisms and delivers a fixed head; trusted main alone performs post-merge live L3/L4, final promotion and cleanup.
- Do not modify production `~/.codex`, AIO, paid runners, Secrets or plan-external GitHub settings.

## Scope

- Implement L0 static/schema, L1 unit/property, L2 subprocess/fake-GitHub, L3 fresh-agent forward-eval trace fixture and L4 public sandbox canary tooling/contracts.
- Add traceability from `GKD-001..016` decisions to positive/negative tests, with mutation counterexamples for critical gates.
- Produce a deterministic stable `0.1.0` candidate bundle, release evidence, release metadata/assets/provenance inputs and a narrow trusted-main final promotion procedure.
- Keep L3/L4 live execution bound to one post-merge final candidate SHA and the approved public sandbox.

## Non-Goals

- Production installation, AIO adoption/migration, paid runners, Secrets, settings changes, historical custom-role probes or actual tag/Release creation by the executor.

## Acceptance Criteria

- All L0-L2 and versioned verifier scopes pass with deterministic evidence and the stable bundle installs/verifies in isolated roots.
- L3/L4 tooling is schema-bound, redacted, exact-SHA scoped and uses only the designated sandbox for public canary effects.
- Traceability covers every `GKD-001..016` decision with positive/negative evidence; critical gates have mutation tests.
- After M5 merge, trusted main can run the one applicable L3/L4 pass, independently accept the exact release record, and create one same-SHA `v0.1.0` tag and GitHub Release without rebuilding assets.
