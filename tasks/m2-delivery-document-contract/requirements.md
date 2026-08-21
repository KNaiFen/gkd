# GKD-M2-J Requirements

## Goal

Close the generic fixed-head delivery contract gap exposed by M2-I: an executor's delivery document must be part of the declared delivery transition so trusted acceptance can validate the exact final PR head without accepting arbitrary post-delivery commits.

## User Decisions

- Continue automatic execution through M3, M4, and M5 without another confirmation; this is a minimum workflow prerequisite.
- Use exactly one accepted `gkd_executor` through the six-gate route, with Sol/xhigh/workspace-write, exact task name and `fork_turns=none`; no worker, fallback, retry, role/model substitution or nested Codex.
- Keep the repair generic and repository-neutral. Do not special-case PR #14, M2-I, a repository, user, branch or machine path.
- Use `implement_and_merge_on_acceptance`; only trusted main accepts and merges.
- Production `~/.codex`, AIO, paid runners, Secrets, settings, tags, Releases and M3 product features remain excluded.

## Scope

- Define a versioned, deterministic delivery-document sequencing contract: the canonical delivery document is committed before the task delivery state transition, and the final state commit is the only post-document coordination commit.
- Make `gkd-task deliver` require and bind the declared delivery document path/content digest (or an equivalent generic state field) so acceptance can prove exact implementation head -> delivery-document head -> final delivery state.
- Update fixed-candidate acceptance and executor Skill documentation to enforce the same sequence; reject arbitrary post-delivery files, duplicate delivery documents, changed implementation files, stale delivery facts and path traversal before writes.
- Add positive/negative/mutation tests, migration compatibility for existing delivered states, deterministic evidence, manifest/lock regeneration and verifier coverage.

## Non-Goals

- Do not modify M2-I implementation code, M3-A policy/monitor, M3-B resources/scanner, M3-C review/Skills, release logic, production/AIO, GitHub settings, or historical probes.
- Do not accept arbitrary documentation after delivery, weaken fixed-tree checks, hand-edit existing task state, or provide a candidate-facing acceptance bypass.

## Acceptance Criteria

1. A fresh task can commit its canonical delivery document before `gkd-task deliver`; the final delivery state binds the exact document commit/path/digest and fixed candidate head.
2. Trusted acceptance accepts only the exact sequence and rejects arbitrary post-delivery files, changed implementation files, duplicate/stale/malformed delivery docs, path traversal and delivery/state digest mismatch before writes.
3. Existing schema-v1/v2 tasks without the additive delivery binding remain readable but cannot silently claim the new contract; the migration behavior is explicit and tested.
4. Executor documentation and delivery examples state the correct order: prepare delivery document, commit it, then invoke deliver, then stop at the final fixed head.
5. Candidate/public CLI cannot accept or merge; trusted `gkd-task accept` remains the only acceptance path.
6. Complete verifier, mutation tests and two deterministic evidence generations pass; execution and candidate bundle digests remain separate and protected surfaces do not drift.
