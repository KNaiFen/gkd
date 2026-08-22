# GKD-M5-C Delivery

## Result

- Outcome: cross_repository_final_gate_ready
- Fixed base: c1de724d686af291cb1ffcf0a2cb12d6621244c6
- Claim base head: 4c79c5edaf8fc3b89a4c6cbe783e7d68124119e7
- Offer: b7dc2a7d93a7a134550f77775b04e527c2d585b45ff53d365a073b1289bf49a6
- Envelope: cfe55dd1745b9d1a56a7178c044199b02a83591e76d8a065b1d42c187a95e9d4
- Implementation/evidence commit: 4f990dde289fb0d1325de68ec90b46ddabcbf591
- Accepted execution bundle: 27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912
- Candidate output bundle: 6dd423ab0662ba0563d222cc07f35cfdd508d00fffaa893a9d9355783df2dba9
- Evidence digest: ea3ccd983f60b1d7539fb57469a5758060b44dd5caa12ff0374efc19cc50a21c
- Evidence file SHA-256: 0c300601b415b0685a0e53e178c2d74055204411ee3d267dae5d14656ed839e0

## Implementation

- L4 now preserves releaseSourceSha and sandboxHeadSha as distinct,
  immutable final-gate facts.
- The read-only GitHub boundary confirms canonical canary.json bytes at the
  fixed sandbox head bind the expected release SHA and bundle digest before
  accepting GKD Canary.
- L3 is an exact-SHA, redacted eval-only record with explicit no-write
  boundaries for source mutation, pull requests, and task lifecycle.
- Final provenance cross-binds the release candidate, L3 record, L4 marker
  observation, and prebuilt assets to the release SHA. Promotion inputs retain
  the same source SHA for tag and Release without rebuilding assets.
- Fake-GitHub contracts reject substituted release source, sandbox head,
  marker bundle, L3 record, and L4 result.

## Verification

Only the versioned verifier was used:

scripts/gkd-verify --base-sha c1de724d686af291cb1ffcf0a2cb12d6621244c6

It passed 412/412: M5 release candidate 13, M4 finalization 9, M3 CI policy
29, M3 resource scanner 14, M3 review core 11, task core 129, role routing
70, runtime bridge 37, foundation 53, and watcher/live-negative 47.

The M5-C evidence generator recorded the candidate bundle and evidence digests
above without machine paths or a live L3/L4 invocation.

## Stop Boundary

This executor stops at fixed-head delivery. It did not run real L3 or L4,
create a tag or GitHub Release, accept, merge, archive, or clean up. Production
Codex, AIO, Secrets, paid runners, and GitHub settings were not modified.
