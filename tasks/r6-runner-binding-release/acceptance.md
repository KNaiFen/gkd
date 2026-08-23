# GKD-R6 Runner Binding Release 收尾

## 结果

- Source merge: `be1e515a64c4095676922c484555fb2a048da681` from PR #30.
- Candidate fixed head: `399f9ef61ad207c23627b71aa86a2881cdb19e3c`.
- Version/bundle digest: `0.1.4` / `cdaa791ace82a5e7c407b29a93a4211b852d7f364900bbcd8a549dbe918bf2a7`.
- Release asset: `gkd-0.1.4-final-be1e515-a.tar.gz`, SHA-256 `713fc828d234bc7ddd298cb68f5abfe1ede29f7891c283924cf3c3b98b2c0330`.

## Independent Gates

- The fixed candidate passed the full versioned verifier: 429 contracts across 11 scopes.
- PR #30 `GKD Verify` passed at the exact fixed head.
- Two clean release-contract runs passed 15/15 with byte-identical evidence.
- L3 record digest: `99c859ec8faf66b614f53f4eb9ead42c3091abac6b9ab745d9eaf23bcc18cbeb`.
- Sandbox PR #7 fixed head `880f54fc30b5cbe80ec87ad2f8cbb43da86e212c` passed `GKD Canary`; request/observation digests are `d8a2ed119ce1ee9d24e99b69a9b1d2357831c0dece4ee659ce71733f127c22b1` / `e19a3ae94b84571c1d97fa05128f59eccde0274309d2ce082393abb0e3da9737`.
- Final record/provenance digests are `86d12bb4a18cc74fa61b62e786e5413e732679b350ed10b1fa85e1ec109e0e96` / `47f9aab043fb09b5b7d230fe83db7aa45e87c0c6bee8edcfbc61dc862cf4f6a9`.
- The GitHub-downloaded asset was independently installed and verified as `0.1.4` with the exact bundle digest.

## Acceptance Exception

`gkd-task accept` returned `INVALID_GITHUB_RESPONSE` before a successful canonical result. A later adapter self-test incorrectly invoked its merge operation, merging the already verified fixed PR head. This record does not claim a successful canonical acceptance result. The merge, CI, L3/L4, asset and restage facts above are independently verified.

Future trusted-main acceptance adapters must be exercised only through `gkd-task accept`; a standalone adapter test may use `snapshot` but must never invoke `merge`.

## Restage

The prior `v0.1.3` project staging was removed and the released `v0.1.4` asset was staged and verified. Its project inventory digest is `9cf92e98646e44045b3d1a14333cdef2ea56215bcb07be6ffb0d144e8275e9c3`. Production and AIO were not changed by R6.
