# GKD-M2-A Rework Delivery

## Outcome

- Outcome: `blocked`
- Rework result: F-001, F-002, and F-003 fixed; F-004 remains blocked
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Coordination merge commit: `8b4927c34d4db5c725236643cdf9e29dc72469c3`
- Initial rework head: `bbd019ff6a37e89b8d559ce5eb74bc1a0b295d7c`
- Implementation/evidence commit: `b64cab4e76f5ddd372a682531fe5802067a3c1c0`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6), kept Draft
- Bundle version: `0.0.0-dev.0`
- Bundle content digest: `6e9cc8a73fa9e80e3a3061114f53c3daf152439a2886e40000e07d19b9c37a6b`
- M2 evidence digest: `5092c31dd1aaab13623e1131da84e248eb4af0018ce0c37f1a63ba85161b00b6`
- Evidence file SHA-256: `563c4fcad787a5eddbf2e7e3c5a5262be4296594074c24c062b41bb0e2c833b9`

The deterministic implementation findings are closed, but the only permitted
fresh-runtime handshake did not establish trustworthy custom-role activation.
This delivery therefore remains `blocked`; it does not establish
`role_routing_core_ready`.

## Rework Facts

- F-001: rollback uncertainty preserves the original backup, stage, and a
  machine-readable freeze record with plan/before/backup/stage digests. Normal
  staged, old-moved, and new-moved failures still restore the exact preimage.
- F-002: `codex-host-runtime` is the fixed provider contract. Its digest is
  `033c387ce08a71dcaa4f455a0e43e5f28f4e4cb09ee87a36c4509f59bdfc4c94`.
  Role/task CLIs no longer accept caller-selected provider commands, provider
  digests, or bundle roots. Without a host adapter, activation recording fails
  closed. Activation, claim, recovery, delivery, and acceptance bind the exact
  task, offer, envelope, role, config, bundle, and offer time window.
- F-003: healthy observations at or after `deadlineAt` produce one
  `deadline_timeout`, one bound interrupt, and terminal state. Only complete
  pre-deadline intervals 1 through 11 return silent `wait_again`; repeated and
  delayed timestamps cannot extend the deadline.
- F-004: the isolated host rejected `gpt-5.6-sol` for its ChatGPT-account Codex
  runtime. The attempt exited 1 with five host events and one thread identity,
  but no custom-role activation or child/parent terminal event. Handshake digest
  is `0bec6189920b8ed73af3296b5d742040f595957a2b7e30a4f4457e671a3e9826`;
  its file SHA-256 is
  `2e2519784315a494b1b3a161d75025f4e2299984d0ce754fa0dcfcba9a5af8ad`.

No self-report, fixture, candidate file, prompt text, or response text was
promoted to trusted runtime evidence. No fallback model or second handshake was
used.

## Digests

- Role source: `469d5ed752d1ff22073eda1b67bbcff19da26f4bb0369459c904b68a17b36819`.
- Hard rules: `7ec55402138ea389afeaa26be68e724384d2a320f64b36e3369089b04ecd2a87`.
- Role digests: executor `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16`;
  acceptor `b2392f4a78ae9774920a100cc4d5fbdca0424c906c194a7f8545156b15481532`;
  CI reviewer `8f3dfbe5b8b3cc1e596acd38dd0a9016f222858b5a585e50b4f8825e39785177`.
- Config digests: executor `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`;
  acceptor `75f0326e0e8f07ba54655fbb90130b5497814c30f6a0307457772d8d7432b57f`;
  CI reviewer `e0acef621cfdc01cd64e1df3a85d695b8f5fbcb752e62c667ab4bc41501dd8b6`.
- Skill digests: `gkd-accept` `656d2fa58bc681767c6a2cab147b6184b33864e7c8cacd4a909fc702ef5c45e3`;
  `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`;
  `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`;
  `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`;
  `gkd-main` `7c24cd74a1b572b7677f255580f4df2ec3221a39aa2310a4dbef6f3dc1e1d14e`.
- Context digests: executor `bc538416558efb9b0d50e9521d756a327dc5f06318de8662630491b661a88e30`;
  acceptor `e92762a482f407984c3cb03bcf04f02e7ea142112b82f8390ff825fc38e73d72`;
  CI reviewer `b0eeea0493dcace808b5ac8c353b9bc09924787710daaf6b1951cbd0a0c32b00`.

## Verification

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 55/55 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

Two disjoint M2 evidence runs were byte-identical and left both fixture roots
empty. Both isolated installs matched at 49 files. Migration plan digest is
`6cc08c33eaee395e067a5d9400c5a7f87b461605ee6151b6c4c491e7cdde5e20`,
inventory digest is
`67f6b438a883675abe8bf39ba4a39328c4edfc05a620caba7c24e6d6dc0e5dd2`,
and normalized surface digest is
`cd740202a620e1997f124d9d4ef9faad2f40a46cd9946695d627f0ba78159205`.

Production protected surface remained 2289 entries at digest
`1fd465b9f0a65d9542e922dddab7df75595caf4530d4988c6db26f12f40d0117`.
AIO planning remained 8 entries at digest
`21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`.
All current-session temporary roots were removed. No dependency was installed,
no large build, historical four-scenario live probe, or real one-hour wait was
run.

## Remaining Boundary

PR #6 remains Draft and has no configured checks; this is
`required_checks_not_configured_bootstrap`, not CI success. Automatic routing
remains `manual_only` with `waitGateReady` absent. Independent acceptance,
merge, M2-B, production installation, AIO adoption, milestone 3, GitHub
settings, Secrets, runners, tags, and Releases remain outside this delivery.
The final delivery head is reported after the delivery commit is pushed and
verified equal locally and remotely.
