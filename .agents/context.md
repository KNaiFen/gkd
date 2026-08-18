# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1C` live gate 人工执行交接已建立。base `c438855961760707c119cb172be97ae9030a4508`，branch `task/m-1-external-watcher-live-gate`，worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-external-watcher-live-gate`，Draft PR `KNaiFen/gkd#3`；等待用户以 GPT-5.6 Sol / xhigh 开启独立顶层执行 session。当前结论仍仅为 `core_ready_for_live_gate`。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
