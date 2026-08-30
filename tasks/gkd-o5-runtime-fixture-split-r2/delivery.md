# GKD O5 Runtime Fixture Split R2 Delivery

## Implementation

- Implementation head: `df16d51372a319ac679c5be4a836d3d09a30a55a`
- Code head: `765ee79bab141d28d7ea927b6b40c6d7d9c2e7da`
- Base head: `419549747fdf06918a5db9f31290bde37e598120`
- Execution bundle digest: `b7a70cb64624f1b44a96e1367af07ffb98f17c11994c1ddfebcf4093d2ae5ff4`
- Candidate output bundle digest: `b7f1d783cf01cdcecfb12f98ce426877aec99b7b4647dacc542fdae8cc053d02`

## Delivered Contract

- The four finalization, release-traceability, trusted-main-evaluation, and multi-repository inputs move from the core payload to the explicit `canonical/inputs` surface without changing their bytes.
- The source declaration and lock bind each input name, kind, source, mode, size, and SHA-256. `gkd-bundle verify-input` validates a named test or release-verification input without an implicit fallback to the installed runtime.
- Core installation remains manifest-driven and contains 107 payload files, 111 installed files including metadata, and no `gkd/fixtures` directory. Installed verification rejects any leaked fixture as extra content.
- The existing manifest schema, release traceability, O4 lanes, Python 3.9 compatibility, task/role/bridge behavior, and public release/finalization CLI shapes remain unchanged.

## Verification

- Python 3.9.6 and Python 3.14.6 each passed the fixed-head default/core verifier: 405 tests across ten scopes.
- Their canonical result digests are `7619496afa8a62bafa24c87296989ddc564ef03c02abefbe3898ec3298f121b1` and `01c28d6b30a4f7944534fa3a6ec9c01f6439034bcd9d4684505181a12b6a3518`.
- Both interpreters generated, installed, verified, and versioned the same candidate output bundle digest. Both verified all four explicit inputs, and neither isolated installation contained a fixture directory.
- Fixed-tree delivery validation returned verifier result digest `402ad97709e7af71c596b43b77c64c37152b926981edbc40ca58b3fbaa17ef97` and evidence digest `b3aef4ad933ad065065a4f8144c125dc56b4c10039d1f6317fd4788ae98bdd2b`.
- `git diff --check`, canonical status, and static doctor passed. No dependency was installed and no production, AIO, settings, Secrets, runner, tag, Release, or published asset state changed.

## Stop Boundary

This document is the only change in its commit. The executor invokes the canonical delivery transition for this fixed candidate, pushes the delivered branch, opens or updates its pull request, and stops without acceptance, merge, archive, cleanup, or follow-on task work.
