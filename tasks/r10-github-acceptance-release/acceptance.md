# GKD-R10 GitHub Acceptance Release 收尾

## 结果

- Source merge: `60ac0c49f1054ce2edea49b3ab6758bfbd3432b3` from PR #33.
- Candidate fixed head: `81ee21751634d5c4609db6313a73353e8221e65d`.
- Version/bundle digest: `0.1.5` / `d749b753fb11aeab44d41b4e1d8bec44c7fa2d18a4b08148fbc0e0c127e27e6d`.
- Release asset: `gkd-0.1.5-final-60ac0c4-a.tar.gz`, SHA-256 `f259475f4ca6c3425e53d734d03633541d6a1997e41991eb5a6115958d06a298`.

## Independent Gates

- The fixed candidate passed the full versioned verifier: 434 contracts across 11 scopes.
- PR #33 `GKD Verify` passed at the exact fixed head.
- Two clean release-contract runs passed 15/15 with byte-identical evidence.
- L3 record digest: `922fdd3b3e071ea485b5289838f2a59ecc22f539895cba90130eb68fed478de5`.
- Sandbox PR #8 fixed head `dbd55a78c25e8208f715562755fee5f3790ffec7` passed `GKD Canary`; request/observation digests are `f5fb04688bb6ab5afd46302dcd3312926992f15ea22319db23f52e8c5021edf8` / `cad91ac09a5249c3bb3a4beab65fd1043cbb6b655582d53bd6d464f7c94c7197`.
- Final record/provenance digests are `1ed5923d1090bf2c11fa8a54da8033a4c085b4fd93ffbce6557f376561bac6de` / `d794024d7a354d349fcd46a7944704fdb4bbb09e148b140136d80c7a00beb2ef`.
- The GitHub-downloaded asset was independently installed and verified as `0.1.5` with the exact bundle digest.

## Canonical Acceptance

`gkd-task accept --merge` used the R9 packaged `gkd-github-acceptance` adapter, returned `accepted` with `merged: true`, and did not use a temporary merge adapter.

## Restage

The prior `v0.1.4` project staging was removed and the released `v0.1.5` asset was staged and verified. Its project inventory digest is `c8e2e37b8c21655202adf9595120b31c098ae1846a39c261d3c0ac8fe2c8180e`. Production and AIO were not changed by R10.
