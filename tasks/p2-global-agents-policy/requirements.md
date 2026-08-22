# GKD-P2 Requirements

## Goal

Perform the authorized user-specific global `AGENTS.md` policy migration without placing the policy itself in the portable GKD bundle.

## Scope

- Bind the actual preimage by SHA-256 and keep a private machine-local recovery copy.
- Preserve every non-empty preimage line in the same order; only remove redundant blank lines.
- Reject symlinked, missing, changed or already-recovering input before mutation.
- Atomically replace the target and verify its exact postimage relation to the private preimage.

## Non-Goals

- No GKD bundle source change, role change, production bundle migration, AIO change, GitHub action, tag or Release.
- No prompt update is inferred: the preimage contains no legacy reviewer or GKD-role reference.
- No global policy contents, absolute production path or recovery bytes enter Git or machine evidence.

## Acceptance Criteria

- The recorded preimage digest matches the actual private backup before replacement.
- The postimage is exactly the ordered sequence of non-empty preimage lines plus a single final newline.
- The private recovery surface is regular, mode-restricted and records only digests and transformation facts.
- The production bundle and AIO remain unchanged.
