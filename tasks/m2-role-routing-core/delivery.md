# GKD-M2-A 返工交付

## 结果

- Outcome: `blocked`
- F-001/F-002/F-003：实现与回归已闭环
- F-004：唯一获授权本机握手未形成可信 host evidence
- F-005：候选 activation writer 已移除；无候选不可伪造的 host attestation，安装态继续 fail-closed
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Coordination merge: `8b4927c34d4db5c725236643cdf9e29dc72469c3`
- Implementation/evidence fixed head: `010746ba5eda61bde22db0ca4b08f5ff647a698d`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，保持 Draft

本交付不宣称 `role_routing_core_ready`，不启用 automatic route，不进入 M2-B，不验收或合并。

## F-005 边界

canonical payload 已删除 `gkd_role.activation.record_activation`、`ActivationEvidenceProvider` 和 `RuntimeStore.write_activation`。测试 host seam 仅位于 `tests/role_routing/activation_support.py`，未进入 `source.toml`、manifest 或 installed inventory。安装态 CLI、库级 `TaskService` v2 claim/recovery 在缺少候选不可访问的 host attestation 时返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。

executor-equivalent 独立子进程覆盖 import/call writer、直接库级 claim 和 CLI claim；均在写 activation 或 claim commit 前失败。stale、replay、cross-task/cross-role、digest drift、candidate-written 和并发单赢家回归保持通过。plan delta 固定为 `candidate-inaccessible-host-attestation-required`。

## F-004 握手

- Read-only preflight：`codex-cli 0.147.0`；`Logged in using ChatGPT`
- 唯一尝试：1 次；无重试、无模型降级、无 fallback
- 机器分类：`HANDSHAKE_SETUP_FAILED`
- path-free handshake file SHA-256：`6679b69884e2dc448457f9865fcc62732eb1d2900741566572922209a339eb4a`
- handshake digest：`e7d207730a578e3f43384d9e902b61f11d0696a014006ad1e726fddad1ec8e00`
- custom-role activation：未证明
- child/parent terminal：均未证明
- 临时 repo、原始 JSONL：已清理

握手在临时 role/Skill 挂载准备阶段中止，因此没有可信 host event；不使用自述、fixture、候选文件或旧失败事实升级结论。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content digest: `f0bf2bd20b0555e15522c4ea7c8ceaebb8d498bc78bea0d0c449f4a31883d29d`
- M2 evidence digest: `4af07127f85a3e69731b535d13c6680bac6f20f8cab7950dc34c00af5d606b31`
- Evidence file SHA-256: `04d8f0151fd58c9d624cb8c8a55c9cefcdddac1b159d96a2768000d8a0a3a516`
- Role source: `469d5ed752d1ff22073eda1b67bbcff19da26f4bb0369459c904b68a17b36819`
- Hard rules: `7ec55402138ea389afeaa26be68e724384d2a320f64b36e3369089b04ecd2a87`
- Activation provider catalog digest: `033c387ce08a71dcaa4f455a0e43e5f28f4e4cb09ee87a36c4509f59bdfc4c94`
- Role digests：executor `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16`；acceptor `b2392f4a78ae9774920a100cc4d5fbdca0424c906c194a7f8545156b15481532`；CI reviewer `8f3dfbe5b8b3cc1e596acd38dd0a9016f222858b5a585e50b4f8825e39785177`
- Config digests：executor `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`；acceptor `75f0326e0e8f07ba54655fbb90130b5497814c30f6a0307457772d8d7432b57f`；CI reviewer `e0acef621cfdc01cd64e1df3a85d695b8f5fbcb752e62c667ab4bc41501dd8b6`
- Skill digests：`gkd-accept` `656d2fa58bc681767c6a2cab147b6184b33864e7c8cacd4a909fc702ef5c45e3`；`gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`；`gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`；`gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`；`gkd-main` `7c24cd74a1b572b7677f255580f4df2ec3221a39aa2310a4dbef6f3dc1e1d14e`
- Context digests：executor `bc538416558efb9b0d50e9521d756a327dc5f06318de8662630491b661a88e30`；acceptor `e92762a482f407984c3cb03bcf04f02e7ea142112b82f8390ff825fc38e73d72`；CI reviewer `b0eeea0493dcace808b5ac8c353b9bc09924787710daaf6b1951cbd0a0c32b00`

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 56/56 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

两次独立 M2 evidence 逐字节一致；两次安装 inventory 均为 49 文件；临时 fixture root、临时 repo、原始 handshake JSONL 均清理。生产 `~/.codex` 保护面与 AIO planning source 在运行前后未改变；未安装依赖、未运行大型构建、历史四场景 live probe、真实一小时等待。

## PR 与停止边界

PR #6 仍为 OPEN/Draft，base `main`、head 与 task branch 匹配；无 configured checks，事实为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。最终分支 head 将在本轮记录提交后以本地/远端完整 SHA 复核并回报。

未满足条件：可信 custom-role activation、effective model/effort/sandbox 的 host event 绑定、bundle/role/config 的可信 host binding、child terminal、parent terminal、candidate-inaccessible host attestation、M2-B 一小时 gate。保持 manual-only；停止于独立验收前。
