# ADR-001: Keep release and finalization engines separate

## Status

Accepted

## Context

`gkd-finalize` and `gkd-release` both produce canonical records and promotion inputs, but they serve different public workflows. Finalization records express closeout or authorized promotion readiness for a task. Release records bind a stable bundle candidate, layered verification, sandbox observations, and post-merge provenance. Extracting a shared engine during the O8 compatibility-lane change would combine public CLI, record, authority, and provenance migrations with verification scheduling changes.

## Decision

O8 keeps the `gkd-finalize` and `gkd-release` public CLIs, record schemas, error behavior, stdin/stdout shape, and trusted-main authority boundaries unchanged. This task does not extract or merge either engine. A future migration may extract only a stateless canonical helper after a separate approved task proves the required compatibility contracts.

## Alternatives

Extract a shared engine in O8: rejected because it would make catalog and lane changes depend on a public record migration.

Leave the overlap undocumented: rejected because a later refactor could treat structural similarity as permission to merge public behavior.

## Consequences

The release-upgrade lane can validate current records without changing their implementation ownership. A future migration task must first provide CLI golden output for both commands, old record read and reject contracts, promotion request shape checks, provenance split checks, adapter contracts, and Python 3.9.6 and Python 3.14.6 verification. It must stop before changing either public CLI, record schema, authority boundary, or promotion adapter unless that task explicitly includes and proves the corresponding migration.
