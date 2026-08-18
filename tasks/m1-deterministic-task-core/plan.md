# GKD-M1-A Plan v1

## Approval Record

- Requirements: `ready`
- Plan: `approved` under the frozen GKD core implementation plan
- Implementation: `authorized` by `gkd_core_implementation`
- Action mode: `implement_and_merge_on_acceptance`
- Execution: manual top-level execution session

The choices below refine internal implementation details without changing the
approved milestone scope, user-visible authorization model, external action
boundary, or release boundary. Any material departure requires the execution
session to stop and return to main for a new plan version.

Because this task creates the deterministic core, no pre-existing trusted CLI
can generate its plan digest or machine state. The exact planning commit and
these reviewed Markdown files are the bootstrap approval anchor. This exception
ends after M1-A and must not be represented as proof that the new core managed
its own creation.

## Technical Choices

### 1. Separate task CLI and library

Add an executable `gkd-task` rather than adding task lifecycle commands to
`gkd-bundle`. The existing bundle CLI retains its current install, verify,
version, evidence, and governance responsibilities.

Install a standard-library package under `gkd/lib/gkd_task/` with narrow modules
for canonical encoding/schema, planning gates, Git identity/worktrees, runtime
attachments, transactions, offers/claims, doctor/migration, and acceptance.
Install strict JSON schemas under `gkd/schema/task/`. Exact file splitting may
change if it improves cohesion, but public command and state contracts may not.

`canonical/source.toml` declares every new payload file. The existing
development bundle version remains non-release; `gkd-bundle generate` is the
only writer for `manifest.json` and `manifest.lock.json`.

### 2. Human documents and machine state

Formal future tasks use three reviewed Markdown documents:

- `requirements.md`: goals, user decisions, scope, non-goals, and acceptance
  criteria.
- `plan.md`: the material contract and approval-visible execution/external
  action boundary.
- `implementation.md`: internal design notes and execution details that do not
  change the material contract.

The task CLI validates fixed headings and generates a strict tracked
`task.json`. It stores both the complete document digest and a material digest
computed from the plan's fixed material sections. Internal implementation notes
can change without retaining a stale full-document digest, while every material
field change invalidates plan and implementation/action authorization.

The CLI, not the Agent, owns task IDs, schema versions, revisions, digests,
timestamps, normalized repository/branch/SHA values, action records, offer IDs,
claim state, and canonical JSON serialization.

### 3. Durable and runtime authority

Tracked `task.json` plus its exact Git commit is the durable task authority.
It never contains an absolute worktree path, capability secret, session
transcript, process ID, or other machine-local data.

Machine-local state lives below the repository Git common directory in a GKD
runtime namespace, with an explicit `--runtime-root` test/administration
override. This makes the default untrackable and clone-local while keeping the
core independent of a consumer's task directory layout. Runtime attachments,
claim secrets, transaction journals, and session cursors are caches/evidence,
not authorization by themselves.

### 4. Lifecycle and gates

The planning facts are independent of lifecycle phase. The initial lifecycle is
`planning`; an approved and authorized plan can create one active offer and move
to `awaiting_claim`; successful claim moves to `implementing`; delivery moves to
`delivered`. Trusted acceptance records fixed-head acceptance and conditional
merge evidence. Post-merge completion/archive fields are supported for doctor
and later finalization orchestration, but milestone 4 remains responsible for
the complete finalization-PR and release workflow.

A block record overlays the lifecycle and preserves the prior phase. Unsafe
transaction recovery uses the terminal freeze state `transaction_in_doubt`.
No command may infer a transition from Markdown prose alone.

### 5. Lock, CAS, and recovery protocol

Use an atomic task lock directory with a random owner token. Lock acquisition is
bounded; stale ownership is never removed merely from elapsed time. Explicit
recovery must prove the recorded owner/transaction is no longer active.

Every mutation validates, under the lock, the exact Git head, task revision,
offer/claim identity, plan digest, authorization digest, and clean/staging
preconditions. A prepared journal entry records the canonical preimage,
postimage, expected head, and intended file set. The CLI writes only expected
coordination files through same-directory atomic replacement, fsyncs file and
directory when the platform supports it, creates the exact coordination commit,
then marks the runtime journal committed.

Recovery compares the current Git head/blob and task bytes to the prepared
preimage/postimage. It may complete or restore only when one result is provable;
otherwise it writes a path-free `transaction_in_doubt` marker and freezes. Broad
Git reset/checkout/clean is never a recovery primitive.

### 6. Offer and claim capability

Offer creation commits nonsecret offer metadata and stores the hash of a
one-time capability. The plaintext capability exists only in runtime state and
the generated launch envelope. Handoff may render the currently resolved local
worktree path, but rendering must not modify tracked state.

Claim requires the one-time capability plus verifiable runtime/session/role
evidence. M1 implements the evidence-provider boundary and fixture provider;
milestone 2 supplies the fixed role policy and live routing. Missing reliable
evidence fails closed rather than accepting Agent self-report.

Concurrent claims serialize under the lock and compare the same expected state.
Exactly one can consume the capability. Revoke/reclaim advances an epoch so old
launch envelopes and late executors remain permanently invalid.

### 7. Locator, doctor, and migration

Repository identity is normalized from verified Git facts and checked against
the task's durable identity. Locator order and zero/multi-result errors follow
the requirements exactly. Runtime attachment never bypasses same-common-dir,
repository, branch, task, and symlink checks.

Doctor has three composed modes:

- static: strict schema, canonical JSON, digest, transition, identity, and SHA
  checks;
- live: static plus worktree, Git, writer/claim, attachment, and transaction
  checks for active tasks;
- historical: static plus completion, acceptance, merge, archive, and absence
  of live attachment/session state, without requiring a deleted worktree.

The v1 migration library accepts only the documented legacy shape. Active
migration validates the old path before attaching and deleting the tracked
field; archive migration can delete/ignore a missing legacy path. Repeated
migration is byte/semantically idempotent. It is exercised only in generic
fixtures during this task and is not run against a consumer repository.

### 8. Action authorization and trusted acceptance

Authorization is a CLI-generated record bound to task, canonical repository,
base branch/base SHA, task branch, plan version/material digest, mode, and
explicit action allowlist. Capabilities are scoped to an action; refusal is one
terminal machine result with no retry or command substitution.

Acceptance is invoked from trusted synchronized code with explicit candidate
root, PR, and full head. It reads candidate task data and required files through
fixed-tree Git operations and never imports candidate modules. A narrow GitHub
adapter queries repository/PR/check/merge facts and performs at most one
conditional merge tied to the authorized head. Repository-specific branch,
required-check, and merge policy are inputs, not canonical constants. L2 tests
use a fake adapter; this execution session does not use candidate acceptance code
to merge its own PR.

### 9. Verification and evidence

Create a dedicated `tests/task_core/` runner and
`evidence/m1-deterministic-task-core/` machine evidence. Foundation tests keep
their milestone 0 discovery set and evidence semantics; task-core tests do not
move into `tests/foundation/`.

Use temporary bare remotes, clones, real Git worktrees, concurrent subprocesses,
fake clocks/nonces, failure injection, and fake GitHub responses. No dependency
installation or live sandbox is needed. The runner maps stable contract IDs to
the exact tests and emits canonical, path-free evidence.

## Planned Command Surface

The exact argparse grouping may be refined, but the public capabilities must be
covered by narrow commands equivalent to:

- `bootstrap`, `status`, `doctor`, `attach`, `migrate-v1`
- `requirements-ready`, `plan-propose`, `plan-approve`, `authorize`
- `offer`, `handoff`, `claim`, `revoke`, `reclaim`, `block`, `resume`
- `deliver`, `accept`

Commands return one canonical JSON object on stdout for success or stderr for
failure. Stable error codes include invalid transition/state/schema, plan or
authorization mismatch, worktree missing/ambiguous, offer/capability/claim
conflict, lock timeout, transaction in doubt, delivery/head mismatch, candidate
invalid/head changed, required-check failure, merge rejection, and
`authorization_mismatch`.

## File Scope

Expected changes are limited to:

- canonical task CLI/library/schema payload and generated manifest/lock;
- dedicated task-core tests and deterministic evidence;
- task requirements, plan, execution, and delivery records;
- minimal canonical README or governance updates required to describe the new
  installed development component;
- `.agents` updates reflecting task delivery state.

Existing watchdog evidence is historical and must not be rewritten. Existing
foundation behavior may only change where adding declared payload files
necessarily changes the development bundle content digest.

## Risks and Controls

- Multi-file/Git transactions cannot be made magically atomic. The explicit
  prepared journal, exact pre/postimage recovery, and `transaction_in_doubt`
  freeze prevent false success.
- Runtime identity evidence is platform-sensitive. M1 provides a strict provider
  seam and fails closed; milestone 2 must prove real fixed-role handshakes before
  automatic routing.
- Locator convenience can select the wrong clone. Full branch matching,
  same-common-dir verification, canonical repository identity, and ambiguity
  failure prevent guessing.
- A candidate can tamper with its own scripts. Trusted acceptance runs installed
  or main code and reads only fixed-tree candidate data.
- A broad GitHub wrapper could exceed authorization. The adapter exposes only
  read facts and one conditional exact-head merge; runtime refusal is terminal.

## Exit Boundary

Successful delivery establishes only `deterministic_task_core_ready`. It does
not establish role readiness, automatic execution, one-hour waiting, CI monitor
readiness, production installation, release readiness, or consumer adoption.
