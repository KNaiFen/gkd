# GKD-M5-C Delivery

## Result

- Outcome: `cross_repository_final_gate_ready`
- Fixed base: `c1de724d686af291cb1ffcf0a2cb12d6621244c6`
- Claim base head: `5b93e75b5f90919cb8bb206628f0cf7f050b951e`
- Offer: `933d7978ecb58523512ccca54357644cc18ace31a2a97343e70045c51c0fe08d`
- Activation: `682b8631668c01c2498a6d972c807a441ad3c033ae7553ea036cd18efa570578`
- Envelope: `c75bb7206483ca3147606b519cd9479161cbc7fdd34a612f1009becd2cc99ffa`
- Claim ID: `71a56116ac317136cf94b686f34b71105b94f586a5d4e7c42df3a37a11ecf99c`
- Implementation/evidence commit: `4f990dde289fb0d1325de68ec90b46ddabcbf591`
- Accepted execution bundle: `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912`
- Candidate output bundle: `6dd423ab0662ba0563d222cc07f35cfdd508d00fffaa893a9d9355783df2dba9`
- Evidence digest: `ea3ccd983f60b1d7539fb57469a5758060b44dd5caa12ff0374efc19cc50a21c`
- Evidence file SHA-256: `0c300601b415b0685a0e53e178c2d74055204411ee3d267dae5d14656ed839e0`
- Role/config/route digests: `b7660cee9bdab5b1011ae9e92a2a817536f508ef1475a10cc53acd9a1d99c25b` / `d44d2286d0a01a7b0f82610c02a6ada9fb1dc74f05730b1e8629f784d68595d2` / `a298f65210f9b163633bb3043491231020a2f3754d0ea2285e1e859c87ce01a4`

## Implementation

- L4 preserves `releaseSourceSha` and `sandboxHeadSha` as distinct,
  immutable final-gate facts.
- The read-only GitHub boundary confirms canonical `canary.json` bytes at the
  fixed sandbox head bind the expected release SHA and bundle digest before
  accepting `GKD Canary`.
- L3 is an exact-SHA, redacted eval-only record with explicit no-write
  boundaries for source mutation, pull requests, and task lifecycle.
- Final provenance cross-binds the release candidate, L3 record, L4 marker
  observation, and prebuilt assets to the release SHA. Promotion inputs retain
  the same source SHA for tag and Release without rebuilding assets.
- Fake-GitHub contracts reject substituted release source, sandbox head,
  marker bundle, L3 record, and L4 result.

## Verification

Only the versioned verifier was used:

`scripts/gkd-verify --base-sha c1de724d686af291cb1ffcf0a2cb12d6621244c6`

It passed `412/412`: M5 release candidate `13`, M4 finalization `9`, M3 CI
policy `29`, M3 resource scanner `14`, M3 review core `11`, task core `129`,
role routing `70`, runtime bridge `37`, foundation `53`, and watcher/live-negative
`47`. The verifier exited with status 0 and did not install dependencies.

The M5-C evidence generator recorded the candidate bundle and evidence digests
above without machine paths or a live L3/L4 invocation.

## Stop Boundary

This executor stops at fixed-head delivery. It did not run real L3 or L4,
create a tag or GitHub Release, accept, merge, archive, or clean up. Production
Codex, AIO, Secrets, paid runners, and GitHub settings were not modified.
