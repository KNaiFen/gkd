# GKD-M2-K Requirements

## Goal

Revise the automatic bridge trust contract so it uses only spawn and wait facts that the current trusted host actually exposes, without representing configured role values or an unavailable child thread identity as host-observed runtime evidence.

## User Decisions

- On 2026-08-23 the user selected the host-observable contract route after the trusted-main review established that the current host returns a successful direct-spawn acknowledgement and exact task name, but not the v1 bridge's thread digest or effective runtime receipt.
- Keep one exact direct `gkd_executor`, its prepared task name, and `fork_turns=none`; do not use a worker, role/model substitution, fallback, nested Codex, private session/rollout records, or executor self-report as evidence.
- Preserve the configured role, role/config digest, execution bundle, route decision, offer window, CAS, single-writer, fixed-head delivery and independent-acceptance guarantees where their facts remain available.
- This bootstrap repair may use the same narrow manual trusted-main execution exception as M2-C because the broken automatic claim path is the subject of the repair. The exception ends when this task is accepted; no synthetic claim, activation, receipt or delivery record may be created for the repair itself.

## Scope

- Add a versioned automatic host-acknowledgement contract that binds one successful direct host spawn and its returned exact task name to the prepared offer/envelope.
- Make configured model, reasoning effort, sandbox and runtime explicit bundle/catalog expectations, rather than asserting they were effective host-observed values.
- Replace the unavailable raw agent/thread identity in fresh automatic activation, claim and wait records with a deterministic executor-attempt handle derived from the acknowledged exact task name and the immutable offer/envelope binding. The handle must not be described as a host session or raw agent identity.
- For new automatic attempts, remove automatic terminal reclaim when the host cannot provide a machine-bindable terminal identity. A missing delivery after a terminal/error/deadline observation must become an explicit blocked/manual-recovery outcome; legacy reclaim records remain readable under their original contract.
- Update schemas, task/role state validation, trusted-main bridge, wait transition, acceptance, Skills, documentation, focused deterministic tests, evidence and canonical metadata.

## Non-Goals

- No private rollout/session parsing, platform API change, prompt/transcript inspection, credential access, daemon, IPC, signatures, same-user isolation, generic-worker fallback or synthetic host receipt.
- No M3/M4/M5 feature work, production installation, AIO change, GitHub settings, paid runners, Secrets, tags or Releases in the task executor scope.
- No reinterpretation or mutation of historical v1/v3 activation, claim, terminal or delivery records.

## Acceptance Criteria

1. Fresh automatic attempts can claim only after one successful direct host acknowledgement whose returned task name exactly matches the prepared `gkd_executor` request and whose call used `fork_turns=none`.
2. New activation and claim records distinguish host-observed acknowledgement facts from bundle-configured role expectations and do not contain or claim a raw agent ID, child thread digest or host-effective runtime setting.
3. A deterministic executor-attempt handle binds offer, envelope, task name, execution bundle and route decision through claim, wait, delivery and acceptance without leaking raw host identities.
4. New automatic terminal/error/deadline handling cannot reclaim an attempt without a host-bindable terminal identity; it records the bounded stop condition for manual recovery. Legacy records retain their legacy validation behavior and are never silently upgraded.
5. Missing, duplicate, stale, cross-task, wrong role, wrong task name, wrong `fork_turns`, fallback, bundle/route drift and offer-window drift fail before activation or claim writes.
6. Candidate-facing activation/claim/reclaim paths remain fail-closed and byte-unchanged. Executor authority remains implementation and delivery only.
7. Focused contracts, retained verifier scopes and two deterministic evidence generations pass; protected production and AIO surfaces remain unchanged.
