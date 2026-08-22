# GKD-M2-K 交付

## 结果

- Outcome: `host_acknowledgement_bridge_ready`
- Fixed base: `d093113f2252a322956cc4f9dae2067be51d33a2`
- Bootstrap planning/authorized head: `26fa20e11622f9774896295a4bb94e24764b2379`
- Implementation/evidence commit: `12026c6f164a50cb05c6708d553daf6d896b8080`
- Candidate output bundle: `883528f72ce915f089643f8f249fbdda471fc50a4bf87006703c5bbb0d54a2b3`
- Evidence digest/file SHA-256: `6ea2a927b28a42b15603878aecd4783b7d567a8096a31b0f8ce270a6c110ce04` /
  `08f9ca00d8fd9b009926161e348f51be43a2cfdbba4e9259c62a3c004a209a38`

本交付只修订 automatic bridge 的信任合同：当前宿主的 direct spawn acknowledgement
与返回的 exact task name 是唯一新的 host-observed 输入。bundle/catalog 中的 model、
reasoning effort、sandbox 和 runtime 是已验证的 configured expectations，不再被描述为
宿主已确认的 effective runtime settings。

## Bootstrap Exception

M2-K 是修复先前 host receipt 假设的 bootstrap 任务。它保持 `planning`，没有
claim、activation、receipt 或 task delivery machine state；本 session 没有调用
`gkd-task claim`、`gkd-task deliver`、公开 automatic CLI 或私有 host/session 接口。
本交付文档仅是 independent acceptance 的固定头输入，不能被解释为该任务已被
automatic route 执行。

## 实现

- 新增 `host-spawn-acknowledgement-v1`：`prepare` 将它绑定到 v3 offer/envelope，
  `claim` 只接受一次成功 direct `gkd_executor` spawn、prepared exact task name、
  `forkTurns=none` 和无 fallback 的 trusted-main acknowledgement。
- 新 activation schema 使用 `executorTaskName` 与由 task/offer/envelope/task name/
  bundle/route 派生的 `executorAttemptDigest`；不持久化 raw agent ID、thread digest
  或 host-effective runtime setting。旧 activation/claim/terminal records 仍按 v1
  校验，不被升级或重解释。
- fresh acknowledgement attempt 的 wait state 与 fixed-head acceptance 绑定同一
  deterministic attempt handle。没有 host-bindable terminal identity 时，automatic
  reclaim 固定拒绝，terminal/error/deadline 只能进入 blocked/manual recovery。
- 保持 candidate-facing claim/reclaim 与公开 automatic CLI fail-closed；offer window、
  route decision、execution bundle、CAS、receipt 和 fixed-head delivery binding 未放宽。
- 更新严格 schema、main Skill、README、focused positive/negative/mutation/migration
  coverage、canonical lock 与路径最小化 evidence summary。

## 验证

已按 `gkd-local-verify` 运行唯一版本化 verifier：

`PYTHONDONTWRITEBYTECODE=1 PATH=/opt/homebrew/bin:$PATH scripts/gkd-verify --base-sha d093113f2252a322956cc4f9dae2067be51d33a2`

终态 `pass`，共 `417/417`：foundation 53、M3 CI 29、resource 14、review 11、
M4 9、M5 13、P1 6、role-routing 71、runtime-bridge 35、task-core 129、watcher 47。
没有安装依赖、没有重跑历史 custom-role probe 或真实一小时实验。

runtime bridge evidence 在两个互不相交的临时根各运行 35/35，输出逐字节一致；
production 与 AIO protected snapshot 均未改变。候选 bundle 还在独立临时根完成
install/verify：version `0.1.1`、103 files、content digest 与上文一致；该临时根已清理。

验证使用 bundle 已声明的 Python 3.11+ 运行时。当前 shell 默认 `python3` 为不满足
该前提的 3.9，因此测试中的 direct subprocess 使用 test runner 的受支持解释器；没有
修改 production Python、Codex 或用户级配置。

## 停止边界

本文件单独提交后，candidate 停在 independent acceptance 前。trusted main 必须重新核对
完整 diff、requirements、两份 evidence、GitHub live fixed head 和 policy-backed CI；
无阻塞 finding 才能精确合并。不得在此过程中修改生产 `~/.codex`、AIO、GitHub 设置、
Secrets、runner、tag 或 Release，也不得把该 bootstrap 任务伪造成自动 claim/delivery。
