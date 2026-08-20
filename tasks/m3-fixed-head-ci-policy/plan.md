# GKD-M3-A Plan

## Goal

Introduce one portable repository policy boundary and one deterministic GitHub fixed-head monitor so trusted GKD orchestration can wait for the exact policy-required CI terminal without repository-specific constants in the installed mechanism.

## User Decisions

- Use the accepted automatic runtime bridge and exact `gkd_executor`; manual substitution, generic workers, model downgrade, nested execution, and fallback are forbidden.
- Keep this task strictly within M3-A. Resource/scanner work remains M3-B, and review core/new Skill work remains M3-C.
- Add only the standard GitHub Actions surface necessary to prove the policy and monitor in `KNaiFen/gkd`; do not modify GitHub repository settings.
- Preserve the accepted M2 execution bundle throughout claim and delivery; report any candidate bundle as a separate output digest.

## Behavior And Defaults

- Repository policy is explicit and local at `.gkd/policy.json`; no policy discovery outside the supplied checkout and no implicit global or consumer policy is allowed.
- GitHub-only behavior is explicit. Policy/origin/repository disagreement fails before network observation, and any live head drift is terminal.
- The monitor, not the Agent, owns polling. It emits no intermediate prose and returns one canonical terminal result for success, failure, head drift, timeout, or stable error.
- Required checks are policy facts, not inferred from whichever checks happen to appear. Missing, skipped, ambiguous, or pending required checks cannot be reported as success.
- The monitor is read-only. CI repair remains an executor action outside the monitor and acceptance remains a trusted-main action.

## Scope

- Generic `.gkd/policy.json` schema, strict parser, normalized GitHub origin/repository validator, and current GKD repository policy.
- Installed fixed-head monitor library/CLI and strict GitHub adapter boundary with canonical terminal result schema.
- `gkd-ci-monitor` Skill activation of the deterministic runner and minimal adjacent orchestration documentation/contracts.
- A shared versioned local verification entry and a standard pull-request Actions workflow whose declared check names match policy.
- Dedicated M3-A tests/evidence, retained regression routing, README/governance updates, source inventory, manifest, and lock.

## Non-Goals

- Artifact-size classification, resource presets, hardware/disk safeguards, runner/billing discovery, recommendation modes, scanner or credential-exposure states.
- Review queues, remediation cursors, partial approvals, `gkd-optimize-ci`, `gkd-review-remediation`, or broad changes to `gkd-accept` and `gkd-main`.
- Non-GitHub support, webhook/services, GitHub App installation, branch protection/settings changes, workflow writes, CI reruns/cancellation, PR metadata writes, or merge authority.
- Production or AIO changes, dependency installation, large builds/caches, sandbox initialization, tags, or Releases.

## Acceptance Criteria

- Every requirements AC is covered by positive and negative contracts, with mutations for policy/origin/head/check gates.
- A fake GitHub boundary proves fixed-head terminal classification, pagination and errors without external network or credentials; a live task PR proves the checked-in standard Actions check on one explicit head.
- Repository-specific identity and check names occur only in repository policy, workflow, fixtures, task records, or evidence, never as reusable mechanism defaults.
- The installed Skill invokes one deterministic monitor command and trusts only its terminal result; it does not hand-poll or write GitHub state.
- The versioned verifier and workflow run the approved M3-A plus retained short contracts without dependency installation or large artifacts.
- Evidence is deterministic, protected surfaces do not drift, and execution versus candidate bundle identity stays distinct.

## Compatibility

- Preserve existing bundle CLI, task state, offer/claim/activation/receipt, role routing, project staging, manual route, and historical evidence formats except for additive declared payload needed by M3-A.
- Preserve `gkd-ci-monitor` as the Skill name and keep its existing fail-closed behavior when an applicable policy or runner is absent.
- Existing repositories without `.gkd/policy.json` remain explicitly unsupported for policy-backed monitoring; absence is not converted into a pass.
- Python 3.11+ and standard-library-only bundle constraints remain unchanged.

## Security And Data

- Treat GitHub/API output as external input and validate it strictly at the adapter boundary, without expanding GKD into a general security platform.
- Never persist or emit tokens, auth headers, raw error bodies, prompts, transcripts, capabilities, raw agent/thread identities, environment secrets, or machine-local paths.
- Use read-only GitHub calls in the monitor. Merge and other writes remain behind existing explicit action authorization and trusted acceptance.
- Evidence uses synthetic identities or approved public repository facts and remains path-minimized.

## Migration

- No production or consumer migration. Add the GKD repository policy and workflow as normal tracked project files.
- The policy schema is versioned from its first release; incompatible future changes require an explicit schema version and migration task.
- Existing M2 project staging remains untouched because this task changes the candidate output bundle only; adoption of that bundle follows successful acceptance and merge.

## Public Interfaces

- Stable repository policy path: `.gkd/policy.json`, validated against a canonical schema shipped in the bundle.
- One installed machine-readable fixed-head monitor interface taking explicit checkout/repository, PR number, full expected head, and a bounded deadline or equivalent policy-controlled wait input.
- One versioned canonical terminal-result schema consumed by `gkd-ci-monitor` and later trusted acceptance.
- One repository-versioned local verification entry taking an explicit full base SHA and used unchanged by standard GitHub Actions.

## Execution Route

- Trusted main bootstraps and approves the task through accepted `gkd-task`, obtains a six-gate automatic decision, and uses `TrustedMainRuntimeBridge.prepare` and exact claim around one direct `gkd_executor` spawn.
- Executor works only in the registered candidate worktree, verifies, commits, pushes, creates or updates one task PR, handles in-scope CI repair, writes delivery, and stops at a complete fixed head.
- Trusted main waits only through the approved one-hour `wait_agent` loop, then independently reviews and conditionally merges the exact delivered head.

## External Side Effects

- Allowed: task worktree/branch/PR, standard GitHub Actions runs created by committed workflow changes, read-only GitHub API/CLI observations, in-scope CI repair commits, and isolated temporary test/evidence roots.
- Forbidden: production `~/.codex`, AIO, paid runners, Secrets, repository settings, branch protection, workflow dispatch/rerun/cancel, unrelated PR changes, sandbox repository changes, tags, and Releases.

## Action Mode

- `implement_and_merge_on_acceptance` with actions `commit`, `push`, `pr_update`, `ci_repair`, `ready_for_review`, and `conditional_merge`.
- Executor owns all actions except `conditional_merge`; trusted main may merge exactly once only after independent fixed-head acceptance has no blocking finding.

## Implementation Notes

- Prefer a small standard-library policy/monitor package and one narrow executable rather than adding monitor behavior to unrelated task or role modules.
- Reuse canonical JSON/digest/error helpers and the existing subprocess adapter style where it reduces duplication without coupling monitor state to task state.
- Use fake clocks and a fake GitHub executable for deterministic polling tests. Keep real GitHub observations outside committed evidence except for path-free public PR/check facts.
- Let the implementation choose cohesive module and command names while preserving the fixed policy path, explicit inputs, result schema, and Skill behavior above.
