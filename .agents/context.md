# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1B` 外部watcher core人工执行交接已建立。base `9aec60a40572b7c0705049dbce3199d004049c81`，branch `task/m-1-external-watcher-core`，worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-external-watcher-core`，draft PR `KNaiFen/gkd#2`；等待用户以GPT-5.6 Sol/xhigh开启顶层执行session。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
