# GKD O4 Watcher Historical Lane R2 Delivery

## Implementation

- Implementation commit: `4a306746bb46c06c4a92e5f29aee36debdad2aa4`
- Base commit: `528959a97bf9c4f5abe0c7dbe3b841beff15e074`
- Execution bundle digest: `b0174e6c154c22dd73975857e084e26d095f7fb73e5b80588bb7a8a8f697a618`
- Candidate output bundle digest: `894cb41bec407ca633c3e82d63a3319198d8df8a2fcec722420bb4095f3ed869`

## Delivered Contract

- The default verifier now runs ten core scopes only and emits a fixed manifest without the watcher/probe scope.
- `--lane historical` is the explicit watcher lane. It runs the preserved 47 watcher contracts and writes an independent canonical result manifest.
- Historical core evidence and the optional host-capability probe are explicit output paths. An unavailable or drifted host is recorded as `unsupported` without changing the historical M-1B/M-1C conclusions.

## Verification

- System Python 3.9.6 canonical verifier: 398 tests passed across ten default scopes.
- Development Python 3.14.6 canonical verifier: 398 tests passed across the same ten default scopes.
- Historical lane: 47 watcher tests passed twice; both historical evidence files were byte-identical and recorded `unsupported` for the unavailable host capability.
- `verification-results.json`, `verification-evidence.json`, and `result-manifest.json` are direct changes of the implementation commit. The result manifest does not declare the implementation commit SHA.

## Stop Boundary

This document is the only change in its commit. The executor now invokes `gkd-task deliver` for this fixed candidate and stops without acceptance, merge, archive, cleanup, or follow-on task work.
