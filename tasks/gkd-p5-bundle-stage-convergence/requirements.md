# P5 Bundle Stage Convergence

## Goal

Make development bundle installation, project stage refresh, verification, and removal CLI-driven with minimal manually supplied paths and digests.

## User Decisions

The production home, AIO installations, GitHub settings, secrets, paid runners, tags, and releases remain outside this task.

## Scope

- Add a trusted high-level stage transition that derives bundle inventory and digest from canonical source.
- Make old stage removal, staging, and verification one explicit transition with fail-closed drift handling.
- Reduce high-level skill instructions that teach agents to hand-write JSON, roots, digests, or argv.

## Non-Goals

- Do not remove legacy low-level diagnostic compatibility commands.
- Do not alter task lifecycle, acceptance semantics, or production migration.

## Acceptance Criteria

- CLI can refresh an owned development stage from canonical source without manually entered bundle digest or target layout.
- Stage drift, symlink, overlap, and unknown-file cases remain fail-closed.
- Core skills no longer contain manual JSON/CAS/root templates for normal paths.
- Python 3.9 verifier and fixed-head CI pass.
