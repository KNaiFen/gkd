# GKD O4 Watcher Historical Lane R5 Delivery

## Implementation

- Implementation head: `5881d354e5658dbd5e601882b12ec8d9db8e8ec5`
- Base head: `edf0f5c316d828594df58197c043cbc7ee74defb`
- Execution bundle digest: `b0174e6c154c22dd73975857e084e26d095f7fb73e5b80588bb7a8a8f697a618`
- Candidate output bundle digest: `530ad0712e3970f699544eec14651f96be3be4077d93f94c6762c5aa4b7dfd8e`

## Delivered Contract

- The default `gkd-verify` lane records `default/core` and runs only ten core scopes.
- The explicit historical lane records `historical/watcher`, runs the preserved 47 watcher contracts, and retains host-capability `unsupported` facts.
- Fixed-tree result consumers require a known lane/profile, its exact complete scope list, matching verifier summary, and matching evidence and bundle digests. Legacy manifests remain strict to the original full scope set.

## Verification

- Python 3.9.6 and Python 3.14.6 each passed 402 default-lane tests across ten core scopes.
- Two independent historical-lane runs each passed 47 watcher tests. Their historical evidence was byte-identical with SHA-256 `84fcad480c30058bceb4d055df8b5de8aed4f7038db6a2a696cc5c90fb90ea5c`; the optional host-capability result was `unsupported`.
- The implementation commit contains canonical `verification-results.json`, `verification-evidence.json`, and lane-aware `result-manifest.json` artifacts. Fixed-tree artifact validation returned verifier digest `aa4dfae8f0f647b09ff7571b6df283d32d51fcb6478bdf6e86347092e3a765d7` and evidence digest `93f5540c3838f0778448abf0b64fdaeff113bf412784e9172d6e42c38752967e`.

## Stop Boundary

This document is the only change in its commit. The executor invokes the delivery transition for this fixed candidate and stops without acceptance, merge, archive, cleanup, or follow-on task work.
