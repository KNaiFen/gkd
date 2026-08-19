# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；`GKD-M2-A` 已由独立 GPT-5.6 Sol / xhigh 人工顶层 session 交付到 PR #6，但固定头验收拒绝，当前回到人工返工。候选 worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-role-routing-core`、branch `task/m2-role-routing-core`，最新返工记录 head 为 `c4a737fd08c2dadd48c6107296ed40a5e6d3b0a8`（实现 fixed head `cd8c89899039070c29b2c5209e7c5afaefba0616` 的 findings commit），当前未合并。M2 拆为 M2-A 确定性角色/路由核心与 M2-B fresh-runtime 一小时 live gate；M2-A 不运行真实一小时等待。development version 仍为 `0.0.0-dev.0`，当前已验收 M1 content digest 为 `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`。F-001 至 F-003 的迁移恢复、activation provider 信任根/新鲜度、deadline 终止合同，以及 F-004 的可信 custom-role handshake 尚未通过；auto route、M2-B、生产安装与 AIO 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
