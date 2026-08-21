# GKD-M3-B Plan

## Goal

Implement the generic resource/scanner layer needed to make CI recommendations and bounded secret scanning trustworthy on constrained machines.

## User Decisions

- Use one exact automatic `gkd_executor`; no fallback, worker, retry, role/model substitution or nested agent.
- Keep repository-specific policy in checked-in inputs and keep reusable code portable.
- Trusted main alone accepts, merges and cleans up.

## Behavior And Defaults

- Unknown artifact commands remain cloud-owned or `unknown`; local cleanup after peak usage never retroactively satisfies a resource gate.
- Resource-constrained is the conservative default when facts are incomplete; standard/high-capacity require explicit facts.
- Scanner output is canonical, redacted and terminal on credential exposure.

## Scope

- Artifact classification, resource presets, runner/visibility/billing facts, recommendations and fixed scanner wrapper.
- Versioned schemas, fake providers, subprocess contracts, mutations, evidence, docs and manifest/lock regeneration.

## Non-Goals

- M3-A monitor/policy, M3-C review/Skills, release logic, production/AIO, GitHub settings, paid runners or historical probes.

## Acceptance Criteria

- Multi-repository, constrained-resource, zero-large-artifact, price-source and scanner-redaction fixtures pass deterministically.
- No protected surface drift and no raw credential-shaped data in machine output.

## Compatibility

- Preserve M3-A policy/monitor, M2 runtime bridge, task acceptance and project staging contracts.
- Candidate output bundle remains separate from immutable execution bundle.

## Security And Data

- Treat scanner input and GitHub facts as external data; retain only canonical redacted facts and digests.
- Never print raw secret candidates, authorization headers, environment secrets or machine paths.

## Migration

- No production or consumer migration. New capabilities are installed only in the candidate bundle and project staging after acceptance.

## Public Interfaces

- Add generic machine-readable resource/recommendation and scanner interfaces; no merge, rerun, dispatch or settings writer.

## Execution Route

- Trusted main obtains six gates, prepares and claims one exact executor, waits in one-hour intervals, then independently accepts the fixed head.
- Executor implements, verifies, pushes, repairs in-scope CI and delivers; it never accepts, merges or cleans up.

## External Side Effects

- Allowed: one task worktree/branch/PR, standard Actions, read-only GitHub observations and isolated evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, settings, tags and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with commit, push, PR update, scoped CI repair, ready-for-review and conditional merge authorization.

## Implementation Notes

- Prefer standard-library deterministic parsers and fake providers; preserve M3-A's no-dependency verifier and path-free output boundary.
- Commit delivery.md alone before `gkd-task deliver`, then stop at the final fixed head.
