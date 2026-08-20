# GKD-M3-A Requirements

## Goal

Deliver the smallest generic GitHub CI policy and fixed-head terminal monitor needed for later GKD acceptance. Repository-specific check choices must live in a versioned `.gkd/policy.json`; canonical code must validate that policy against the checkout origin and the explicit live pull-request head before reporting a terminal result.

## User Decisions

- Execute this task through the accepted explicit automatic route with exactly one `gkd_executor`, the accepted M2-C execution bundle, the accepted M2-B one-hour wait gate, and no role, model, or worker fallback.
- Keep M3-A limited to generic `.gkd` policy schema, repository/policy/origin consistency, GitHub-only fixed-head monitoring, and the minimum standard GitHub Actions and verification entry required to prove that surface.
- Use `implement_and_merge_on_acceptance` under the existing `gkd_core_implementation` authorization. Executor may commit, push, create or update the task PR, repair in-scope CI, and mark it ready; only trusted main may accept, merge, and clean up.
- Keep mechanism and repository policy separate. A checked-in policy may name this repository and its required checks; reusable library and Skill code may not hard-code an owner, repository, check name, branch, username, or machine path.
- Do not modify production `~/.codex`, AIO, paid runners, Secrets, repository settings, tags, Releases, or the approved sandbox repository.

## Scope

- Add a strict, versioned, generic schema and parser for repository-local `.gkd/policy.json`, plus the GKD repository policy needed to exercise the feature.
- Validate the canonical GitHub repository identity and base branch declared by policy against the checkout's `origin`, accepting only explicitly supported equivalent GitHub remote URL forms and rejecting ambiguity, mismatch, symlinks, traversal, unknown fields, and non-GitHub origins.
- Add one installed, machine-readable GitHub fixed-head monitor interface. Its required inputs are an explicit checkout/repository, pull-request number, lowercase full expected head SHA, and applicable policy. It owns polling and returns one canonical terminal result without asking an Agent to hand-poll.
- Update the existing `gkd-ci-monitor` Skill and only the minimum adjacent main/acceptance documentation or contracts needed to consume the policy-backed terminal result.
- Add the minimum versioned local verification entry and standard GitHub Actions workflow needed for GKD pull requests to run the policy-declared required checks without dependency installation or large local artifacts.
- Add hermetic fake-GitHub/subprocess tests, multi-repository and remote-form fixtures, mutation coverage, deterministic evidence, documentation, canonical source declarations, and regenerated manifest/lock.

## Non-Goals

- M3-B artifact classification, local resource presets, runner or billing fact discovery, speed/cost recommendations, secret scanner wrappers, credential-exposure workflow, or any large-build policy.
- M3-C shared review core, `gkd-optimize-ci`, `gkd-review-remediation`, seven-Skill bundle closeout, or broader review/acceptance redesign.
- Supporting non-GitHub forges, modifying branch protection or required-check settings, dispatching/rerunning/cancelling workflows, changing PR metadata, or merging from the monitor.
- Installing production configuration, changing AIO or consumer adapters, initializing the sandbox repository, adding paid services or Secrets, or creating tags or Releases.
- Re-running the historical custom-role probe, M2-B one-hour experiment, M2-B early-final experiment, or any M2-C bootstrap state.

## Acceptance Criteria

1. `.gkd/policy.json` is validated by a strict versioned schema with no unknown fields. It contains repository-specific GitHub identity, base branch, and required-check policy while reusable code contains no project-specific repository, owner, branch, workflow, check, username, or absolute-path constant.
2. Policy loading rejects an absent or non-file policy, symlinked policy or ancestor, noncanonical content, malformed repository/check values, duplicate required checks, unsupported provider, and path traversal before any GitHub query.
3. Checkout validation derives the canonical identity from `origin`, supports only documented equivalent GitHub HTTPS/SSH forms, and fails closed on missing origin, non-GitHub origin, repository mismatch, base-branch mismatch, ambiguous identity, or policy/check drift.
4. The monitor requires an explicit repository identity, PR number, lowercase full expected head, and matching policy. It validates live repository, PR number, base branch, head branch/head SHA, state, and configured required checks on every observation.
5. The only successful result binds the exact expected head and reports every policy-required check successful. A new PR head returns terminal `head_drift`; any required terminal failure returns terminal failure; pending or absent checks never become success; deadline exhaustion returns one timeout result.
6. The deterministic monitor owns bounded polling and produces one canonical, versioned, path-minimized terminal JSON result. It performs read-only GitHub operations and never reruns, dispatches, cancels, edits PR metadata, accepts, or merges.
7. GitHub response parsing is strict and deterministic across check runs/status contexts, duplicate or ambiguous names, unknown conclusions, pagination, API errors, and rate/transport failures. Errors remain stable and do not expose tokens, authorization headers, environment secrets, raw API bodies, or machine paths.
8. The repository policy and standard GitHub Actions workflow agree on required check names. The workflow uses standard GitHub-hosted runners, no Secrets or paid runner, and invokes the same versioned verification entry used by `gkd-local-verify`.
9. The versioned local verification entry accepts an explicit full base SHA, verifies ancestry, selects the repository-approved M3-A and retained short contracts, installs no dependencies, and creates no large build, dependency, or cache artifact.
10. L1/L2 tests cover multiple repository identities, remote URL forms, policy/origin mismatches, fixed-head success/failure/drift/timeout, missing and duplicate checks, pagination, transport/API errors, no-write behavior, and mutation failures for every material gate.
11. Two clean temporary evidence generations are byte-identical, candidate Git remains clean outside declared files, protected production/AIO surfaces do not drift, and historical live probes are not run.
12. Retained task-core, role-routing, runtime-bridge, foundation, watcher-core, and watcher live-negative contracts pass as required by the versioned verifier. The candidate output bundle digest is reported separately from the immutable accepted execution bundle digest.
