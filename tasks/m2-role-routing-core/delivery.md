# GKD-M2-A 最终返工交付

## 结果

- Outcome: `blocked`
- F-005: 最小整改完成
- F-004: 本机登录态握手已执行一次，可信 host evidence 仍不完整
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Implementation/evidence commit: `707a0c1156fbf14537746bb2a11a4432ff2b0e48`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，保持 Draft

本交付不宣称 `role_routing_core_ready`，不启用 automatic route，不进入 M2-B，不验收或合并。

## F-005

canonical/installable payload 不再包含 activation writer、`FixtureEvidenceProvider` 或 `make_fixture_evidence`。activation 与 M1 runtime evidence 的 fixture seam 均只存在于 tests，未进入 source、manifest、bundle 或 installed inventory。

正常公开 CLI/library v2 claim 与 recovery 在没有真实 host attestation 时返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`；回归断言返回前 activation、claim、runtime 和 tracked bytes 不变。未增加 monkeypatch/subclass 防御、daemon、IPC、签名服务或新密码学协议。CAS、锁、journal、recovery、freshness、replay、cross-task/cross-role 和 digest drift 合同保持通过。

## F-004

- Preflight: `codex-cli 0.147.0`，`Logged in using ChatGPT`
- Live attempts: `1`
- Fixed role/model/effort/sandbox: `gkd_executor` / `gpt-5.6-sol` / `xhigh` / `workspace-write`
- Bound bundle digest: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- Bound role digest: `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16`
- Bound config digest: `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`
- Host exit status: `1`
- Event types: `error`, `item.completed`, `thread.started`, `turn.failed`, `turn.started`
- Failure class: `CUSTOM_ROLE_HANDSHAKE_INCOMPLETE`
- Custom-role activation: 未证明
- Effective model/effort/sandbox host facts: 未观察到
- Host digest binding: 未观察到
- Child terminal / parent terminal: 均未观察到
- Raw JSONL / temporary repo: 已删除

未切换 `CODEX_HOME`，未读取认证材料，未使用 fixture fallback、模型降级或第二次 live probe。候选输出和自述未被提升为可信证据。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content digest: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- M2 evidence digest: `163f4d549004869614b83b536627a71f3226d995d1e6345be744bdeaaa98dd23`
- Evidence file SHA-256: `4f6f3133204c47a38318d16b238639d7e1539521f489074b6b1c09f5ffa345bf`
- Handshake digest: `cedb684eddf07fdd345415d07f59f99dfe34a0687fa6b35cd487072781f175f0`
- Handshake file SHA-256: `6682ad625e6ddc8002b095fd6c0934847f9e292eaed2fb68e388b5730585ad6b`
- Role source: `469d5ed752d1ff22073eda1b67bbcff19da26f4bb0369459c904b68a17b36819`
- Hard rules: `7ec55402138ea389afeaa26be68e724384d2a320f64b36e3369089b04ecd2a87`
- Activation provider catalog: `033c387ce08a71dcaa4f455a0e43e5f28f4e4cb09ee87a36c4509f59bdfc4c94`
- Role digests: executor `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16`; acceptor `b2392f4a78ae9774920a100cc4d5fbdca0424c906c194a7f8545156b15481532`; CI reviewer `8f3dfbe5b8b3cc1e596acd38dd0a9016f222858b5a585e50b4f8825e39785177`
- Config digests: executor `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`; acceptor `75f0326e0e8f07ba54655fbb90130b5497814c30f6a0307457772d8d7432b57f`; CI reviewer `e0acef621cfdc01cd64e1df3a85d695b8f5fbcb752e62c667ab4bc41501dd8b6`
- Context digests: executor `89ed5ac0e9e641cabeebfbfb790912f6058adcc6b55f86a43a1c36db835b36dc`; acceptor `5bd84ee3e3cb1eabb8228275e16f26e991e70936fd0360df4d921d3153d98a9d`; CI reviewer `64ac9ebda50236e90434964d46ad174449058bab1b5af46aa7c77bee9615df3f`
- Skill digests: `gkd-accept` `656d2fa58bc681767c6a2cab147b6184b33864e7c8cacd4a909fc702ef5c45e3`; `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`; `gkd-main` `7c24cd74a1b572b7677f255580f4df2ec3221a39aa2310a4dbef6f3dc1e1d14e`

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 56/56 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

两次独立 M2 evidence 逐字节一致；两次安装 inventory 均为 49 文件。生产保护面保持 2289 entries / `db47d57e24c9a23f185ecafad1ac0d9bb8c7b4fa5c930b1b3a6abfb2776dcd6d`，AIO 保护面保持 8 entries / `21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`。临时 fixture、repo、JSONL 均清理；未安装依赖、运行大型构建、历史 live probe 或真实一小时等待。

## 停止边界

PR #6 保持 OPEN/Draft。仓库无 configured checks，事实为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。未满足条件仍是可信 custom-role activation、effective config host facts、host digest binding、child terminal 与 parent terminal；因此保持 manual-only，并停在独立验收前。
