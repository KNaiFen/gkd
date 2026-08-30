# GKD O4 Watcher Historical Lane R6 Delivery

## Implementation

- Implementation head: `e0d0b00a725e282005e72565161362b0977805ad`
- Base head: `ba32d14729eb38058f4d59e9c83b3e22ff0c8993`
- Execution bundle digest: `04efd9ce5f1e0f678f9853eef5d9fb20606fff6e667aba69d9b204bddeb9b5d6`
- Candidate output bundle digest: `b7a70cb64624f1b44a96e1367af07ffb98f17c11994c1ddfebcf4093d2ae5ff4`

## Delivered Contract

- The default verifier records `default/core` and runs only ten core scopes.
- The explicit `historical/watcher` lane preserves the 47 watcher contracts and records an unavailable host capability as `unsupported`.
- Fixed-tree delivery artifacts declare the lane, profile, and exact scope list. The existing consumer, acceptance, and rework paths reject unknown or mismatched lane, scope, test, head, base, and digest facts.

## Verification

- Python 3.9.6 and Python 3.14.6 each passed 403 default-lane tests across ten core scopes.
- Two independent Python 3.14.6 historical-lane runs each passed 47 watcher tests. Their historical evidence was byte-identical with SHA-256 `2c1c4d7eb5f8428756b770a811dbdd8d7eed0ac40982e37b1a70987c5d336df9`; the explicit host-capability probe recorded `unsupported`.
- The implementation tree contains canonical `verification-results.json`, `verification-evidence.json`, and lane-aware `result-manifest.json`. Fixed-tree validation returned verifier digest `cf8b5d6407d76fe72803fb1131c44c86b680cdfc004378ed357d05dd3ff23c1b` and evidence digest `2fcc3e8776e32bc2d8d4e129331da1252d410d6919588f18ce1df031a7066909`.
- The candidate bundle installed and verified in an isolated temporary root with 115 files and the declared candidate output bundle digest.

## Stop Boundary

This document is the only change in its commit. The executor invokes the delivery transition for this fixed candidate and stops without acceptance, merge, archive, cleanup, or follow-on task work.
