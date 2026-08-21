# GKD-M4-A Requirements

## Goal

Implement the frozen milestone 4 generic acceptance, finalization and release mechanism without creating a release, tag, production installation, or consumer adoption.

## User Decisions

- Continue automatic execution through M4 and M5 with one exact accepted `gkd_executor` route.
- Keep this task limited to deterministic task/finalization/release mechanics; the final release candidate and live L3/L4 work belong to M5.
- Do not modify production `~/.codex`, AIO, paid runners, Secrets, GitHub settings, tags or Releases in this task.

## Scope

- Strengthen executor/acceptor separation, fixed-head acceptance and synchronized-main revalidation where required by the M4 contract.
- Add deterministic task PR plus finalization PR state machinery with closeout-only and release-mode authorization boundaries.
- Add deterministic version, lockfile, changelog, release-intent, exact-main candidate, same-SHA tag promotion, release asset and provenance interfaces.
- Add generic fixtures and evidence proving normal closeout uses at most two PRs and does not split records, version or evidence paths.

## Non-Goals

- M3 policy/resource/review product semantics, M5 L3/L4 execution, actual tag/Release creation, production installation, AIO adapter or migration.

## Acceptance Criteria

- Executor cannot merge; independent acceptor fixed-head acceptance neither imports nor executes candidate code and revalidates synchronized main.
- Closeout-only forbids product logic; release mode requires a bound adapter and authorization.
- Version/lock/changelog/release intent and provenance are canonical; source, candidate, tag and assets bind one exact SHA.
- Local verifier, focused mutations, two byte-identical evidence runs, candidate bundle verification and `GKD Verify` fixed-head CI pass.
