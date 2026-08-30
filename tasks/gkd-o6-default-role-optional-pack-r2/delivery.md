# GKD O6 Default Role And Optional Pack R2 Delivery

## Implementation

- Implementation head: `87ad0a9f2fb41c11f2b48b9255d592edec0b6969`
- Base head: `ce2d6814a1a4b75e16fe9e096f66b399a28de07f`
- Execution bundle digest: `fe1098fd1be01e8b59dd268b0ed45cc7b44217063e00e0a20afd0bf1c9b1014c`
- Candidate output bundle digest: `8c34b7474d4fb55c1d688f515dbd2f4f7cac32c8706865a4bc8eea2060bd10b3`
- Core digest: `ee344ae248afbc21d07987634db13efcb7273769f64960f44588008b8babeebc`

## Delivered Contract

- The default executor context contains only `gkd-execute`, `gkd-local-verify`, and `gkd-ci-monitor`. `gkd-main` and `gkd-accept` retain their existing trusted role boundaries.
- The default core installation owns 84 runtime files and installs 88 files including metadata. It excludes resource/recommendation/scanner, review/adapter/remediation, their dedicated schemas/input, and both optional Skills.
- `ci-advice` owns 11 files with pack digest `f2e570ec6e72f31e73ff83ca9d4916dc84445c3570585c7dc06e0310e4383af9`. `review-remediation` owns 12 files and one explicit input with pack digest `a6da97399e28cdca7965cb68f5748494f32a521cf0ce8da639d4ecaaa4cdc9d9`.
- `gkd-bundle pack-stage`, `pack-verify`, and `pack-remove` accept declared names only. Role context and project staging use explicit repeated `--pack` values; each selected set renders the actual executor TOML and binds its pack, Skill, role, config, project inventory, file, mode, size, and SHA-256 facts.
- Existing optional CLIs and Skills remain available after explicit staging. The default verifier no longer runs their scopes; separate and combined optional lanes retain their contracts.
- Schema-v1 source generate/verify and full installs remain readable; schema-v2 alone requires pack declarations. V1 v2-field, v2 missing-pack, unknown-schema, and pack-ownership drift inputs fail closed. Task/route/bridge/acceptance/rework, fixed-head monitor, migration duplicate-Skill disabling, production migration, finalization, release, and legacy task/result formats retain their existing behavior.

## Verification

- Python 3.9.6 and Python 3.14.6 each passed the default/core verifier: 396 tests across eight scopes.
- Their core canonical result digests are `5082134bf1ab697056ab799bd5bf6514853b9e1b4ae75697d26005670d3ab932` and `fa0907ac8a74fc2ca827d915e0305ccd987bb8120146301c69f98ed7d22aa859`.
- Each interpreter passed 19 `optional-ci-advice`, 11 `optional-review-remediation`, and 30 combined `optional-packs` tests. Combined canonical result digests are `1340c7bb52216d83a869c4da7abd7f837fe7ef7097ec49781de3466fb9b3a132` and `6fcc66484611f735ff8eb14850ae0f273e8c5179a8d59b539b0205340b6126b0`.
- Fixed-tree sidecars bind verifier result digest `2d36ec5f7ab285383889503b1041f8e5db53e2f5fbfc687bb374e240ec33a780` and evidence digest `462b03b07f8d97e81cf07802b1aedfae5620fabffbe5acf724ad6f9ec2f58937`.
- `git diff --check` passed. No dependency was installed and no production, AIO, settings, Secrets, runner, tag, Release, or published asset state changed.

## Stop Boundary

This document is the only change in its commit. The executor invokes the canonical delivery transition for this fixed candidate, pushes the delivered branch, opens or updates its pull request, and stops without acceptance, merge, archive, cleanup, or follow-on task work.
