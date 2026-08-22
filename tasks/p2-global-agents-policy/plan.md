# GKD-P2 Plan

## Goal

Compress the current global policy without changing its rules or moving user-specific policy into GKD.

## Preimage

- Preimage SHA-256: `aa86b3d6f69fb089370a2b36ced910632c37aec827c7b52e129db78ce67a582e`
- Mapping: retain each non-empty UTF-8 line byte-for-byte and in original order; remove blank lines only; terminate with one newline.

## Execution

1. Trusted main verifies the regular target and rejects symlinks, drift and an existing P2 recovery surface.
2. It writes the exact preimage and a canonical digest-only recovery record to a private machine-local directory with restrictive modes.
3. It creates the mapped postimage beside the target, verifies the line mapping and atomically replaces the target.
4. It rechecks the postimage digest, recovery record and production/AIO protection boundaries, then writes only redacted acceptance facts to this repository.

## Rollback

The private recovery copy remains available until trusted-main acceptance. A failed postimage check restores the exact preimage before reporting failure. No recovery bytes are committed.

## Boundaries

P2 is a trusted-main production-policy gate, not an executor task and not a portable bundle feature. It completes before the separately authorized production bundle migration and before AIO adoption.
