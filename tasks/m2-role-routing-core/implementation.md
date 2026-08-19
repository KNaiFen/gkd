# GKD-M2-A Implementation Notes v4

## Internal Design

- Represent role definitions in one strict canonical source model and generate
  installed TOML, role/config digests, context manifests, installer inventory,
  and evidence from it. Do not duplicate model/effort/sandbox constants across
  the three role files and five Skills.
- Extend the milestone 1 runtime provider boundary with a one-time activation
  record written by trusted orchestration. The record should bind the exact
  task, offer, envelope, agent/thread identifier, custom role, role/config
  digests, bundle digest, route, timestamp, and consumption state. Claim must
  validate it under the existing task lock and journal protocol.
- Keep every candidate-callable activation writer out of the installable
  production path. A test-only host seam belongs under tests and cannot be
  exported by the bundle. If the current host exposes no writer/attestation
  boundary that the candidate cannot invoke or forge, installed activation
  recording must remain fail-closed and delivery must report that limitation.
- Model routing as a pure decision over explicit request plus fixed readiness
  facts. Keep `manual` as the default output. A failed automatic request returns
  one refusal and does not create a replacement offer or select built-in
  `worker`.
- Model waiting as pure canonical state transitions over claim time, elapsed
  completed one-hour intervals, bound agent identity, and observed terminal or
  error facts. A Skill performs the actual `wait_agent` call and must use the
  transition output without additional inspection during healthy timeouts.
- Package the five workflow Skills as generic GKD mechanism using `gkd-task`
  state and portable locators. Keep repository-specific CI policy unavailable
  until milestone 3 rather than embedding AIO assumptions.
- Generate per-role context manifests and Skill disable overrides. Executor,
  acceptor, and CI reviewer must receive disjoint authority even when they share
  read-only helpers.
- Implement temporary installation migration with exact owned-file preimages,
  same-transaction legacy-role replacement, exact duplicate-path disablement,
  idempotence, and fail-closed recovery.
- Keep the implementation in Python standard library plus existing canonical
  payload patterns. Add new schemas and commands only where they remove prose
  state or enforce a cross-module contract.

## Execution Details

- Begin from fixed base `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
  and synchronize only the later main registration commit if it changes
  `.agents`/task registration records without product code.
- Establish baseline results for task-core 104, foundation 53, watcher core 47,
  and watcher live-negative 15 before implementation. Do not run the historical
  live watcher probe.
- Inspect the five production GKD Skills, the legacy `ci_reviewer` role, and six
  duplicate Skill groups read-only as migration inputs. Never edit those paths.
- Check the current official Codex custom-agent, subagent, AGENTS, Skill, and
  config references before freezing generated formats.
- Build L1 schema/unit/property and mutation contracts first, followed by L2
  temporary-home, real Git/worktree, concurrent activation/claim, installer,
  and recovery fixtures.
- After hermetic contracts pass, prepare a clean temporary Git repo and render
  the exact candidate `gkd_executor` plus required Skills into project scope.
  Resolve the normal CLI with `command -v codex`; strictly parse the generated
  project config and `gkd_executor.toml` using Python `tomllib` and exact source
  comparison. Then run non-strict `codex app-server --listen off` with explicit
  project trust and `agents.enabled=true`, accepting only its no-transport
  boundary, and use the exact live command with `--help` for argument parsing.
  Prove zero model invocations/attempts, exact digests, trust, accepted project
  role definition, clean repo, and unchanged production configuration. Do not
  interpret no-transport as real custom-role activation. Push this static fixed
  head and stop for a new live authorization.
- Under that later authorization, launch one ephemeral parent with normal user
  provider/auth/model routing and no parent `--model` or effort override. The
  project role fixes the child to `gpt-5.6-sol`/`xhigh`/`workspace-write`.
  Normalize only host turn, named activation/no-fallback, child/parent terminal,
  exit and redacted error facts; deterministic preflight owns digest binding.
  Delete raw events and the temporary repo. Do not set alternate `CODEX_HOME`,
  copy authentication, install production files, retry, downgrade, or perform
  repository implementation work.
- The live command omits `--strict-config`. The v3 strict parser rejection is
  retained as historical environment-compatibility evidence with zero model
  invocations and zero consumed live attempts.
- Generate evidence twice from disjoint clean system temporary roots. Confirm
  byte identity, temporary cleanup, production/AIO protection snapshots,
  manifest/lock consistency, and installed inventory/modes.
- Deliver only `role_routing_core_ready` or `blocked`. Do not claim the M2-B
  one-hour gate, automatic-route readiness, production installation, milestone
  3 readiness, or release readiness.
