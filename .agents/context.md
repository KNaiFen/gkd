# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M3-A` 已通过 accepted automatic route 的 exact claim 实现并推送至 PR #8。候选提供 strict `.gkd/policy.json`、GitHub origin/base 一致性、installed fixed-head terminal monitor、标准 `GKD Verify` Actions job 与统一 `scripts/gkd-verify`；candidate output bundle digest 为 `92e218e9809e6147f3b04ec7f8fed79231c6e8b3a94480729b52b6fcdbafafe8`，与 accepted execution bundle `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad` 分离。333 项版本化本地验证通过；27 项 M3-A 双 evidence 逐字节一致，evidence digest/file SHA-256 为 `3476aabb597f8c257737ae47c5fca943517ed2642d17349e5c5d9fc288c855a4` / `4b2d7ad2f0b08b30fe28e4f957b9f7372644c0552ab7c39caf9ae3982c93d18f`，生产与 AIO 保护面不变。等待最终 delivery head 的 policy-backed CI 终态与 trusted-main 独立验收；M3-B/M3-C、生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
