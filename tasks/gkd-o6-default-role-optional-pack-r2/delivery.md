# GKD O6 Default Role And Optional Pack R2 Delivery

## Implementation

- Implementation head: `188b52558279872e8b67874cbfcf8d19b32203e7`
- Code head: `e1214c16daa959124b9b427850e7ccc25300782c`
- Base head: `ce2d6814a1a4b75e16fe9e096f66b399a28de07f`
- Execution bundle digest: `fe1098fd1be01e8b59dd268b0ed45cc7b44217063e00e0a20afd0bf1c9b1014c`
- Candidate output bundle digest: `a06a8f75ad1b6fd4811e1a85b38e39de3c68ff193b4dad55525b7aa466f288b5`
- Core digest: `7b5ef2e92891d0a591a19b75a94bbe8b3b9938c9f14d4948a8fc3d7b21a3c9ce`

## Delivered Contract

- The default executor context contains only `gkd-execute`, `gkd-local-verify`, and `gkd-ci-monitor`. `gkd-main` and `gkd-accept` retain their existing trusted role boundaries.
- The default core installation owns 84 runtime files and installs 88 files including metadata. It excludes resource/recommendation/scanner, review/adapter/remediation, their dedicated schemas/input, and both optional Skills.
- `ci-advice` owns 11 files with pack digest `f2e570ec6e72f31e73ff83ca9d4916dc84445c3570585c7dc06e0310e4383af9`. `review-remediation` owns 12 files and one explicit input with pack digest `a6da97399e28cdca7965cb68f5748494f32a521cf0ce8da639d4ecaaa4cdc9d9`.
- `gkd-bundle pack-stage`, `pack-verify`, and `pack-remove` accept declared names only. Role context and project staging use explicit repeated `--pack` values and bind pack, Skill, role, config, project inventory, file, mode, size, and SHA-256 facts.
- Existing optional CLIs and Skills remain available after explicit staging. The default verifier no longer runs their scopes; separate and combined optional lanes retain their contracts.
- Schema-v1 source generate/verify and full installs remain readable; schema-v2 alone requires pack declarations. V1 v2-field, v2 missing-pack, unknown-schema, and pack-ownership drift inputs fail closed. Task/route/bridge/acceptance/rework, fixed-head monitor, migration duplicate-Skill disabling, production migration, finalization, release, and legacy task/result formats retain their existing behavior.

## Verification

- Python 3.9.6 and Python 3.14.6 each passed the default/core verifier: 395 tests across eight scopes.
- Their core canonical result digests are `80fed2d240a110cff257b629b268b81791c056d1f56de55d704a0f4dac55bd1a` and `72e775656c7dd8c023e6bb06bfb6270187e3f0a2e3b537691c1df4ec4608150d`.
- Each interpreter passed 19 `optional-ci-advice`, 11 `optional-review-remediation`, and 30 combined `optional-packs` tests. Combined canonical result digests are `2cfc43711952d7333ebad68bbf9e9e809ff38bee871b40625004ce3b2f7230ed` and `8b0d3d93b004da3d6f25525d99db3707d57b7861b0e5613c24aaf08b2f5e6388`.
- Fixed-tree sidecars bind verifier result digest `78b3ae7f171625ebc51a3c63aef18afd6789a42161b5e5542979aeeed4f88bbb` and evidence digest `0cb91e3ec0216f6fbe9a75e5693e2262cedf98429d74d5f999dca98e6b4be118`.
- `git diff --check` passed. No dependency was installed and no production, AIO, settings, Secrets, runner, tag, Release, or published asset state changed.

## Stop Boundary

This document is the only change in its commit. The executor invokes the canonical delivery transition for this fixed candidate, pushes the delivered branch, opens or updates its pull request, and stops without acceptance, merge, archive, cleanup, or follow-on task work.
