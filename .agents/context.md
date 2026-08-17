# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `codex-cli 0.147.0` 已用配置解析错误证明 `multi_agent_v2.max_wait_timeout_ms` 硬上限为3,600,000ms，原生单次12小时D2路线不成立。`GKD-M-1A` 将短时固化 `native_insufficient` 证据，不再运行65分钟探测；随后进入已批准的外部app-server watcher任务。branch/worktree/PR仍为 `task/m-1-native-d2-probe`、`/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-native-d2-probe`、`KNaiFen/gkd#1`。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
