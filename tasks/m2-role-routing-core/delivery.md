# GKD-M2-A 交付

## 结果

- Outcome: `role_routing_core_ready`
- Route: `manual_only`
- F-001/F-002/F-003/F-004/F-005: 已整改，等待独立验收
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Implementation commit: `f86a092a9ba42fd8965209dfe18f3a70debe0ef6`
- Evidence commit: `0108c1c50dc3c4437cadf0cbea1ebd480768e83c`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，Ready

本交付只表示固定角色与路由核心可供独立验收。M2-B 真实一小时等待、
automatic route、生产安装、AIO 接入和里程碑 3 均未启动或授权。本 session
不验收、不合并、不清理 worktree/branch。

## Activation → Claim

安装 bundle 提供 `TrustedMainActivationAuthority` 工作流权限入口。trusted main
将已验证的 host activation facts 绑定到 exact task/repository/branch、offer、
envelope、route、role/config/bundle digest 和 offer window，并将一次性 provider
显式传给 `TaskService`。完整临时任务合同证明：main-owned activation record →
exact claim → claim/activation receipt → delivery。

候选公开 `gkd-role activation-record`、`gkd-task claim --activation-id` 和默认无
provider library claim/recovery 均在 runtime/tracked 写入前返回
`TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。missing/candidate-written、stale、
replay、cross-task、cross-role、digest drift、并发单赢家和 recovery 合同保留。
`FixtureEvidenceProvider`、`make_fixture_evidence` 与 tests-only seam 不在 bundle、
manifest 或安装 inventory。

该边界是 trusted main 与 candidate 支持路径之间的工作流权限边界，不是同一
OS 用户进程间的安全隔离。monkeypatch、私有 API 和直接修改 runtime 文件是明确
非目标；没有加入签名、daemon、IPC、密钥或其他安全基础设施。

## Handshake

本轮未执行新的 Codex live probe 或模型 turn。纯静态 preflight 以当前 bundle
重新生成受信项目的 exact role/Skill/config，使用 `tomllib` 和非 strict
app-server no-transport 边界验证配置，记录 `modelInvocations=0`、
`liveAttemptsConsumed=0`，随后只离线归一化用户已授权的既有 test-session
rollout。

规范化证据要求并证明：

- 唯一 `agents.spawn_agent`；
- `agent_type=gkd_executor`、`task_name=gkd_executor_handshake`、
  `fork_turns=none`；
- 对应 `sub_agent_activity` 的实际 child thread 与 exact child session/parent/
  role/path 绑定；
- child terminal 只来自该 exact child rollout；
- parent terminal、Codex exit code `0`；
- 无 alternate role、downgrade 或 fallback。

child thread identity 只保留 SHA-256
`0d44f3a3964d654f115c24da39a85861a49953f8e40f65345aa44355109d5897`。
wrong task name、wrong fork turns、unrelated child terminal、multiple spawn、wrong
child identity 与 built-in fallback 均有负向合同。原始 rollout、prompt、路径和
明文 thread identity 未复制进仓库 evidence。隔离模式 HTTP 400、v3 strict parser
失败和早期 wait-only 诊断只存在于 `historicalNegativeEvidence` /
`historicalCompatibilityEvidence` 等明确历史字段。

## Digests

- Bundle version/content: `0.0.0-dev.0` / `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`
- M2 evidence digest/file SHA-256: `2f292830f2e9674a4ea95db1e4026ccf9abd3b6a3ef2241deec799329b590068` / `9cea06f174a7b544b1f4289dd2e348515c9d5caa59fd373d77d8bc89eb0fbe67`
- Handshake digest/file SHA-256: `e2f69c4b5c7a0e3945fbd06f432defbe65e703174ebb28833a9a510276fb6940` / `5bcc8b476856bef554665d0ff81af470dfb36e3472d31fdae41319b2efffe127`
- Preflight/project config/AGENTS: `47b493db61ab240c1969d1678a191512daa75fdde7d6ab50ff215f78ef03b66b` / `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0` / `777519597b1a4ca62ee662bfdbe03760ffe64eed6cd6066b0d4b4585011a41da`
- Role source/hard rules: `469d5ed752d1ff22073eda1b67bbcff19da26f4bb0369459c904b68a17b36819` / `7ec55402138ea389afeaa26be68e724384d2a320f64b36e3369089b04ecd2a87`
- Roles: executor `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`; acceptor `b2392f4a78ae9774920a100cc4d5fbdca0424c906c194a7f8545156b15481532` / `75f0326e0e8f07ba54655fbb90130b5497814c30f6a0307457772d8d7432b57f`; CI reviewer `8f3dfbe5b8b3cc1e596acd38dd0a9016f222858b5a585e50b4f8825e39785177` / `e0acef621cfdc01cd64e1df3a85d695b8f5fbcb752e62c667ab4bc41501dd8b6`
- Skills: accept `656d2fa58bc681767c6a2cab147b6184b33864e7c8cacd4a909fc702ef5c45e3`; CI monitor `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; execute `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; local verify `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`; main `7c24cd74a1b572b7677f255580f4df2ec3221a39aa2310a4dbef6f3dc1e1d14e`
- Contexts: executor `8f650166cd8255b68ab73f17b1dfffa5ca81c9a87caf8442022de45fb8ed28c6`; acceptor `59ea6a57dc6749edbd846b7d1f6fa96fa19f3eaa6f0aca14ac1f197f9ca2da8b`; CI reviewer `276278029a38de64e8304d6b13653d30f3396830c8b320e607965f08b11eb3be`
- Migration plan/inventory/surface: `7452652223af580eed2bc8e687ebb09ac73b5dd206e7c6b75daf25701bd295cb` / `67f6b438a883675abe8bf39ba4a39328c4edfc05a620caba7c24e6d6dc0e5dd2` / `cd740202a620e1997f124d9d4ef9faad2f40a46cd9946695d627f0ba78159205`

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 70/70 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

M2 evidence 在两个独立系统临时根逐字节一致；`contract-results.json` 与
`m2-contracts.json` 也逐字节一致。每次临时根结束为空，两次安装 inventory 均为
49 文件。生产保护面为 `f1b9cb277305039196067cb6621ecc2c50b09b0349824bc04ff684be775c1232`
（2289 entries），AIO 保护面为
`27358a2dcde47816b6dd213005167645b0a86644693e446ca4da8c1c656d98c3`
（15675 entries），每次 before/after 相同。未安装依赖、未运行大型构建、历史
watcher live probe 或真实一小时等待。

## PR 与停止边界

PR #6 无 configured checks，事实为 `required_checks_not_configured_bootstrap`，
不表述为 CI 成功。最终 push 后须核对本地 HEAD、upstream、origin branch 和 PR head
完全一致且工作树干净。交付停在独立验收前，不验收、不合并、不启动 M2-B、
不启用 automatic route、不修改生产 `~/.codex` 或 AIO。
