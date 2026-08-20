# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Active task: `GKD-M3-A` 已在 PR #8 delivered head `735e704e1191d19343a6febdb0600fc2f555058f` 暴露 shallow checkout CI 失败与 policy schema/parser 不一致；下一步使用 M2-D accepted rework transition 返回 planning，并由同一 exact `gkd_executor` 产生 fresh automatic claim 进行窄修复。
- Current state: 里程碑 2 及其 delivered rework 补强已完成。`GKD-M2-D` fixed head `e8729934f567d74ee19e7583b8f8433dacb9ac60` 已通过独立验收并由 PR #9 squash merge 为 `0976b4900346e972bd8e03f6e8fa4ab761fe8952`；candidate/merge tree 均为 `a25603809da5b87ed814be0841217c372a92d8ee`，worktree 与本地/远端分支已清理。accepted execution bundle 已升级为 `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766` 并安装到隔离临时根；机器本地 project staging 的 role/config/project-config/inventory digest 为 `880e1855cfdeb50ba890a3023c818cde377b9c6a71c230360154b79ecc16d680`、`10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`、`9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`、`ce434766ef460d83d86bd8cdc6bae0822636f729086bf13031b18a32bf44500c`。M3 仍按 A policy/monitor、B resource/scanner、C review/Skills 顺序执行；生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
