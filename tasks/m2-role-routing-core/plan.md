# GKD-M2-A Plan v4

## Goal

Build the deterministic role, route, activation, wait-state, context, and
temporary migration layer that sits above the milestone 1 task core. The result
must be installable and independently reviewable while remaining manual-only
until the separate M2-B live wait gate passes.

## User Decisions

- Use one manual top-level GPT-5.6 Sol / `xhigh` execution session for M2-A.
- Split the real fresh-runtime one-hour gate into GKD-M2-B after M2-A merges.
- Define exactly `gkd_executor`, `gkd_acceptor`, and `gkd_ci_reviewer`; replace
  the old `ci_reviewer` without an alias in temporary migration fixtures.
- Fix executor and acceptor to GPT-5.6 Sol / `xhigh`; fix CI reviewer to
  GPT-5.6 Terra / `high` / read-only.
- Keep manual as the default and automatic as explicit plus fully gated.
- Use native one-hour `wait_agent` calls only; never shorten or substitute the
  wait, and cap orchestration at 12 elapsed one-hour intervals after claim.
- Canonicalize five existing GKD Skills, disable discovery of six approved
  duplicates without deleting them, and preserve all mapped AGENTS hard rules.
- Do not install or modify production user configuration in this task.
- Validate F-004 through the normal production-use Codex environment. The parent
  loads existing user provider/auth/model routing and receives no explicit model
  override; a trusted temporary project supplies the candidate custom role.
  Never create an alternate Codex home, copy auth state, or modify production
  configuration. Finish and push static preflight first; each later live launch
  requires one new fixed-head authorization.
- Strictness is scoped to generated project and role TOML through Python
  `tomllib` plus exact canonical comparison. The host compatibility check is
  non-strict and must reach only the expected app-server no-transport boundary;
  it does not establish a real role activation.

## Behavior And Defaults

- Role and configuration files are generated from strict canonical data. The
  installed TOML is an output, not an editable authority.
- Role selection is by exact role name and digest. Built-in `worker` is never a
  substitute for an unavailable GKD role.
- Manual routing requires no automatic readiness claim. Automatic routing
  requires an explicit request plus fixed bundle, role/config, offer/claim, and
  M2-B wait-gate evidence. Any absent or stale fact returns manual-only without
  creating a replacement offer.
- Trusted main records a one-time activation fact after a specific custom role
  is spawned. Claim consumes evidence bound to the exact launch envelope and
  role instance. Candidate output and child prose are untrusted inputs.
- Healthy one-hour wait expiry is not interpreted as health proof. It advances
  only the deterministic elapsed-interval state and instructs main to call the
  same native wait again immediately.
- Child terminal/error, user intervention, identity drift, or the 12-hour
  deadline ends the loop. Deadline handling emits one bound interrupt decision
  and one timeout terminal result.
- Role context defaults to deny-by-omission: only required GKD Skills and hard
  instructions appear in each role manifest. Unrelated discovered Skills are
  explicitly disabled for that role where supported.
- Installer migration defaults to plan/verify against an explicit temporary
  target. It does not discover or edit production home implicitly.

## Scope

- Canonical role source, schemas, renderers, digests, and installed TOML.
- Trusted activation/evidence provider integrated with milestone 1 claim.
- Manual/automatic router and stable readiness/refusal output.
- Fake-clock one-hour/12-hour wait state machine and Skill orchestration
  contract; actual one-hour host wait is deferred to M2-B.
- Minimal role-context manifests and five canonical GKD Skills.
- Temporary installer migration for three roles, old CI reviewer replacement,
  six duplicate Skill discovery overrides, and AGENTS hard-rule mapping.
- L1/L2 fixtures, static preparation for one short local-authenticated and
  project-scoped role handshake, deterministic machine evidence, canonical
  manifest/lock, and retained regressions. The live launch follows only under a
  separate authorization for the resulting fixed head.

## Non-Goals

- M2-B live one-hour result or enabling automatic execution.
- Milestone 3 CI policy/monitor readiness, resource and billing strategy,
  secret scanning, `gkd-optimize-ci`, or `gkd-review-remediation`.
- Milestone 4 acceptance/finalization/release expansion or milestone 5 evals.
- Production install, AIO adoption, GitHub settings, paid services, tag, or
  Release.
- Profiles, plugin/MCP removal, context-window changes, cache cleanup, or
  deletion of duplicate source directories.

## Acceptance Criteria

- Every requirement in `requirements.md` has a named positive and negative
  contract; authority, role boundary, route fallback, and wait deadline have
  mutation guards.
- Two clean evidence runs and two clean temporary installs are byte-identical
  and bind the same bundle, role, Skill, context, and migration digests.
- Real Git/worktree fixtures prove task/offer/activation/claim identity binding
  and first-writer behavior with no candidate-created evidence shortcut.
- Wait fixtures prove exact one-hour parameters, at most 12 intervals, healthy
  silence, early terminal return, identity drift refusal, and one final
  interrupt/timeout decision.
- Temporary-home migration proves exact legacy-role replacement, duplicate
  discovery disablement without deletion, idempotence, recovery, and hard-rule
  preservation.
- All retained M1/foundation/watcher short regressions pass and protected
  production/AIO surfaces remain unchanged.
- Outcome is `role_routing_core_ready` only when deterministic preflight and
  trustworthy host activation/terminal evidence are both demonstrated.
  Otherwise delivery is `blocked` with the exact failed stage.

## Compatibility

- Preserve milestone 1 task JSON, authorization, offer, claim, receipt, journal,
  migration, delivery, and acceptance schemas unless a versioned compatible
  extension is required. Existing M1 fixtures must remain readable.
- Preserve `gkd-bundle` and `gkd-task` existing command behavior. New commands
  and fields must be additive or explicitly versioned.
- Role files follow the current Codex custom-agent schema: `name`,
  `description`, and `developer_instructions` are required; supported session
  settings may add model, reasoning effort, sandbox, MCP, and Skill overrides.
- Skill directories retain standard `SKILL.md` progressive-disclosure shape.
- The old `ci_reviewer` disappears only in an explicit migration transaction;
  M2-A does not mutate a live installation.

## Security And Data

- Treat role activation as an authorization provenance problem, not Agent
  identity prose. Bind only minimal path-free facts and never store transcript
  content, prompts, private session databases, rollout logs, credentials, or
  environment secrets.
- Keep plaintext claim capabilities and machine-local agent identifiers outside
  Git and published evidence. Evidence may contain only stable digests and
  synthetic fixture identifiers.
- Use `codex login status` only as a boolean preflight. Normal Codex startup may
  parse existing user provider, routing, and login configuration, but the task
  must not print configuration, read or copy auth files, tokens, cookies, or
  private session state. Snapshot approved production configuration surfaces
  before/after and require byte identity. Raw handshake JSONL may exist only in
  an explicit temporary directory while minimized; delete it before delivery
  and commit only path-free structured facts.
- Reject unknown fields, path traversal, symlinks, credential-shaped echoed
  identifiers, cross-task reuse, stale bundle/role/config digests, and replay.
- Role permissions follow least authority: executor cannot merge; acceptor does
  not implement; CI reviewer is read-only and cannot mutate GitHub state.
- Data protection remains narrow and does not expand GKD into a general Cyber
  platform.

## Migration

- Generate an explicit migration plan from a supplied source/target inventory.
  Apply only beneath a validated temporary test home during M2-A.
- Install three canonical role files and five canonical Skill directories with
  owned-file inventory and mode validation.
- Remove legacy `ci-reviewer.toml`/`ci_reviewer` in the same transaction that
  installs `gkd_ci_reviewer`; reject ambiguity or multiple legacy facts.
- Add exact `skills.config` disabled entries for the approved six `.agents`
  duplicate paths. Preserve those directories and every unrelated Skill.
- Generate and verify an AGENTS rule mapping; do not rewrite production AGENTS.
- Repeated apply is idempotent. Failure restores exact preimages; uncertainty
  creates a machine-readable freeze result instead of partial success.

## Public Interfaces

- Installed custom roles: `gkd_executor`, `gkd_acceptor`, `gkd_ci_reviewer`.
- Installed Skills: `gkd-main`, `gkd-execute`, `gkd-accept`,
  `gkd-local-verify`, `gkd-ci-monitor`.
- Deterministic CLI/library surfaces for role render/verify, activation record
  and consumption, route decision, wait-state transition, role-context
  manifest, and migration plan/apply/verify. Exact argparse grouping may be
  refined without changing behavior.
- Canonical JSON outputs use stable outcomes and error codes. Normal output is
  path-free and contains no capability, prompt, transcript, or secret material.
- GKD-M2-B consumes the fixed M2-A bundle version/content digest and its wait
  contract; it must not reinterpret or hand-edit M2-A machine state.

## Execution Route

- This task uses a manually opened independent top-level execution session in
  its registered worktree. It does not use `gkd_executor` to implement itself.
- The executor may not delegate investigation, design, implementation, review
  judgment, or repository writes. After deterministic contracts pass, it must
  push a static fixed head and stop. A subsequent explicit authorization may run
  one bounded live handshake from a clean temporary Git repo. The parent uses
  normal user provider/auth/model routing with `--ephemeral`; the tested child
  role is discovered only from temporary project-scoped `.codex/agents` files.
- The existing M1 CLI cannot provide trusted production claim evidence, so this
  task retains a documented bootstrap exception and does not create a fake
  `task.json`, offer, claim, activation, or receipt for itself.
- Independent main acceptance remains fixed-head and separate from execution.

## External Side Effects

- Allowed now: changes in the M2-A worktree, temporary fixture homes/repos, the
  existing task branch and Draft PR, task-related push/PR updates, and no-model
  static parsing of normal user/project configuration. A later short
  local-authenticated parent/child handshake is allowed only after the user
  explicitly authorizes one call against the new static fixed head.
- Forbidden: production `~/.codex`, AIO writes, GitHub settings, Secrets,
  runners, billing, tags, Releases, sandbox repository initialization, and any
  live one-hour or 12-hour wait claim.

## Action Mode

- `implement_and_merge_on_acceptance` applies to the task PR under the existing
  `gkd_core_implementation` authorization.
- Execution may commit, push, update the task PR, perform in-scope repair, and
  mark it ready. It must stop before acceptance or merge.
- Only an independent trusted main/acceptor may conditionally merge the exact
  delivered head after review. Missing checks remain a bootstrap fact, not a CI
  success claim.

## Implementation Notes

- Extend the existing standard-library bundle and task core rather than adding
  dependencies or a second state authority.
- Keep role policy as canonical data plus strict generators. Avoid handwritten
  TOML/JSON drift and duplicate role constants across Skills.
- Prefer a small deterministic transition core for route/wait/migration facts;
  Skills should orchestrate host tools and consume machine decisions rather
  than reimplementing counters or gates in prose.
- Validate current Codex role and Skill formats against official OpenAI
  documentation during execution because the host schema is version-sensitive.
- Treat the temporary custom-agent file as the object under test, not the
  authority that certifies its own activation. Only minimized host events can
  establish F-004. A callable writer inside the installable bundle cannot
  establish activation provenance and must remain fail-closed unless a
  candidate-inaccessible host boundary is demonstrated.
- Preserve the v3 `USER_CONFIG_PARSE_FAILED` result as historical compatibility
  evidence. It records that `codex-cli 0.147.0 --strict-config` rejected the
  existing user field `disable_response_storage` before project discovery; it is
  neither a live attempt nor a reason to edit production configuration.
