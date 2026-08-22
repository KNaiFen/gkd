# GKD-M2-K 验收

## 结论

- Outcome: `accepted_host_acknowledgement_bridge_contract`
- Fixed candidate head: `5e00ed9410ee4c31d6e69b4134ba4157eb517f95`
- Squash merge: `f6374221d1996a9ecd5d84921660b6e45432d859`
- Candidate and squash trees: identical
- Candidate output bundle: `883528f72ce915f089643f8f249fbdda471fc50a4bf87006703c5bbb0d54a2b3`
- Evidence digest/file SHA-256: `6ea2a927b28a42b15603878aecd4783b7d567a8096a31b0f8ce270a6c110ce04` /
  `08f9ca00d8fd9b009926161e348f51be43a2cfdbba4e9259c62a3c004a209a38`

无阻塞 finding。M2-K 的 bootstrap exception 合法且保持最小：任务状态仍为
`planning`，没有为修复本身伪造 claim、activation、receipt 或 delivery machine state。
因此通用 `gkd-task accept` 不适用于本次验收；trusted main 对显式 fixed head 进行了
独立审查和精确 GitHub merge。

## 独立核对

- 逐项核对 requirements、plan、implementation、authorization、完整 fixed-head diff、
  README、main Skill、严格 schema、legacy compatibility 与停止边界。新的 activation
  只包含 configured catalog expectations、task name 和 deterministic attempt handle；
  raw agent/thread identity 与 host-effective settings 没有进入 fresh contract。
- `host-spawn-acknowledgement-v1` 绑定唯一 direct `gkd_executor`、prepared task name、
  `forkTurns=none`、无 fallback、offer/envelope、route decision 与 immutable bundle。
  mismatch、drift、过期和 candidate/public claim 路径都在写入前 fail-closed。
- 新 attempt 的 wait、delivery 和 acceptance 持续绑定同一 attempt handle；没有
  machine-bindable terminal identity 时 `reclaim_terminal` 固定返回
  `HOST_TERMINAL_BINDING_UNAVAILABLE`，不会把无绑定终端解释为可重试 claim。旧 v1
  activation/terminal validators 保持原路径。
- 从 base `d093113f2252a322956cc4f9dae2067be51d33a2` 独立运行唯一版本化 verifier：
  `417/417` 通过，其中 runtime-bridge `35/35`、role-routing `71/71`、task-core
  `129/129`，其余保留范围全部通过。未安装依赖，也没有重跑历史 custom-role probe
  或真实一小时实验。
- 两个不相交临时根生成的 runtime bridge evidence 逐字节一致；production/AIO protected
  snapshot 不变。候选 bundle 在独立临时根 install/verify 为 version `0.1.1`、103 files
  和上述 candidate digest，临时根已清理。

## Fixed-Head CI

当前生产 Skill 安装不含 `gkd-ci-monitor` 可执行文件。为避免使用候选可执行文件，trusted
main 从同步、干净的 `d093113f2252a322956cc4f9dae2067be51d33a2` canonical source 在隔离
临时根安装并验证 trusted monitor bundle（digest
`68188dcaeb98d93902b435c98784e242090ed18828e9d96a8dee735244f7d1ef`）。

用该已验证 monitor 和 main 的 `.gkd/policy.json` 获得唯一终态：repository
`github.com/KNaiFen/gkd`、PR `24`、expected/observed head
`5e00ed9410ee4c31d6e69b4134ba4157eb517f95`、policy digest
`d77e68152843dcc1f470d88c76fe8c249ef803854048f4a9d42ed5cc92cd54c2`、required
`GKD Verify=success`、outcome `success`、reason `ALL_REQUIRED_CHECKS_SUCCESSFUL`。

此前两次 monitor 调用分别错误传入 GitHub CLI 简写 repository 和绝对 policy path；都在
本地参数校验阶段以 `REPOSITORY_INVALID`、`POLICY_PATH_UNSUPPORTED` 终止，零次 GitHub
observation、没有 PR 写入。纠正为 policy 中的 canonical repository 与固定相对 policy
path 后才执行上述唯一有效监控。

## 合并与后续边界

PR #24 使用 `--match-head-commit` 精确 squash merge；GitHub 返回 merged，PR head 保持
上述 fixed candidate，merge commit 为 `f6374221d1996a9ecd5d84921660b6e45432d859`。trusted
main 已 fast-forward 到该 merge。

本次没有创建 tag、Release、生产安装、AIO 修改、GitHub 设置、Secrets 或付费 runner。
已发布且生产安装的 `v0.1.1` 仍绑定其原 bundle
`68188dcaeb98d93902b435c98784e242090ed18828e9d96a8dee735244f7d1ef`；AIO 不得消费本次
未发布源码。下一步必须先独立规划并验收 M2-K 后的版本提升、release gate 与隔离 restage，
再继续 AIO adoption。
