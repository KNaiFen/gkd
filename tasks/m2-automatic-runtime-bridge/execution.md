# GKD-M2-C Execution

## Sole Entry

This is the last manual bootstrap execution task before the canonical automatic route becomes operational. Work only in the registered candidate worktree and task branch. Use GPT-5.6 Sol with `xhigh` reasoning in an independent top-level Session. Do not use a subagent, generic worker, nested `codex exec`, alternate role, downgrade, or fallback.

Read `task.json`, `requirements.md`, `plan.md`, `implementation.md`, and this file completely before changing files. This task uses the documented one-time bootstrap exception below; do not attempt the revoked public claim path.

## Bootstrap Exception

The initial manual offer/envelope was revoked because the public `gkd-task claim`
path always constructs an unavailable evidence provider while schema-v1/manual
claim still requires runtime evidence. Requiring claim before implementing this
bridge is therefore a self-bootstrap deadlock and would make the task impossible.

For this task only, the authority is the fixed planning package, registered
worktree/branch, manual top-level Session, implementation authorization, and
independent fixed-head acceptance. The execution Session must not call
`gkd-task claim`, `gkd-task deliver`, `gkd-role activation-record`, or any private
API to manufacture a claim, activation, receipt, or delivery. The revoked offer,
envelope, and runtime capability are historical registration facts only and must
not be reused. This exception ends when M2-C is accepted; M3 and later tasks must
use the supported automatic bridge implemented here.

## Required Reading

1. Root `AGENTS.md`, `VISION.md`, `.agents/context.md`, `.agents/decisions.md`, and `.agents/open-items.md`.
2. This task's four Markdown documents and machine-generated `task.json`.
3. `tasks/m2-role-routing-core/acceptance.md`, `tasks/m2-one-hour-live-gate/acceptance.md`, and `tasks/m2-role-routing-core/retrospective.md`.
4. The approved GKD plan index and core plan at the read-only AIO planning paths supplied in the launch Prompt.
5. Exact canonical code and tests for role rendering, handshake project staging, route decisions, activation authority, task offers/claims/delivery, runtime transactions, role contexts, bundle generation, and installed Skills.
6. Current official Codex project custom-agent and Skill documentation only where the on-disk format is version-sensitive.

Do not read production auth/config contents, cookies, tokens, session databases, rollout JSONL, or unrelated conversation records.

## Startup Gates

1. Confirm the physical repository root, branch `task/m2-automatic-runtime-bridge`, remote identity `github.com/KNaiFen/gkd`, fixed base ancestry, clean worktree, task state, runtime attachment, and revoked-offer record.
2. Confirm the parent is a manually opened top-level GPT-5.6 Sol/xhigh Session. Stop rather than downgrade or delegate.
3. Run `gkd-task status` and `doctor --mode live` using the explicit candidate/runtime/task facts from the launch Prompt. Confirm phase `planning`, epoch `1`, revision `5`, no active offer/envelope, and no claim/receipt. Do not try to restore or consume the revoked envelope.
4. Establish the short retained regression baseline. Do not run historical watcher probes, a real one-hour wait, dependencies, large builds, or production installation.
5. Snapshot only the approved production/AIO protection surfaces with path-minimized digests; normal host-owned metadata is not task evidence.

## Implementation Contract

- Implement every requirement and material plan field, but keep the design small. Promote tested staging shapes into canonical code; do not import tests from the payload.
- Provide a supported project-scoped stager that deterministically renders and verifies the exact main/executor project layer from a pinned execution bundle without modifying production Codex state or contaminating the candidate worktree.
- Provide a main-only direct-spawn activation/claim bridge using the existing authority/provider seam. Candidate-facing public activation and default claim paths remain fail-closed. The bridge must be the supported claim path for M3 and later; this task itself is the sole bootstrap exception.
- Persist the route decision binding for automatic offers and distinguish execution bundle identity from candidate output bundle identity through offer, activation, claim, wait, delivery, and evidence.
- Preserve single writer, exact CAS/lock/journal/recovery, manual default, no fallback, executor authority limits, data minimization, and the simplified same-user threat model.
- Correct README/Skill documentation that still claims M2-B or automatic routing is unavailable, without claiming M3 completion or production installation.

## Required Verification

- Add dedicated M2-C positive, negative, recovery, and mutation contracts for all acceptance criteria.
- Run dedicated M2-C contracts twice from disjoint clean temporary roots and require byte-identical canonical evidence.
- Run all retained task-core, role-routing, foundation, watcher-core, and watcher live-negative suites. Do not run historical live probes.
- Exercise two temporary project stagings and an end-to-end synthetic route → offer → handoff → trusted activation → claim → delivery flow inside tests/main-only fixtures. Do not claim or deliver M2-C itself.
- Confirm candidate Git is clean after staging fixtures, manifest/lock are generated by canonical tooling, temporary roots are removed, and production/AIO protection digests do not drift.

## Autonomy And Stop Conditions

Complete the whole authorized repair loop autonomously: investigate, implement, test, regenerate, document, commit, push, open/update the task PR, repair in-scope failures, and deliver a fixed head. Do not pause for main after each diagnostic or local failure.

Stop as `blocked` only when a locked user decision or material plan field must change, production/AIO access is required, the canonical task state cannot be safely recovered, or the platform makes the approved contract genuinely impossible. Do not expand into signatures, daemon, IPC, security isolation, M3 features, production installation, or generic-worker fallback.

## Delivery

The successful outcome is `automatic_runtime_bridge_ready`. Write `delivery.md` with the fixed base, implementation/evidence commits, revoked bootstrap offer fact, execution and output bundle digests, role/config/Skill digests, tests, evidence equality, protection results, PR/check reality, deviations, and residual risks. Do not fabricate M2-C claim, activation, receipt, or delivery facts.

Commit and push the exact task branch, create or update one task PR against `main`, mark it Ready only on success, verify local/upstream/origin/PR heads match, and stop before independent acceptance, merge, real project staging, fresh-main startup, M3, production installation, AIO, branch deletion, or worktree cleanup.
