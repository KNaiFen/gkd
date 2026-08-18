# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1B` implementation/evidence head `b441562f02c069bbcca7aaff25c6d79eaf1fae63` 已完成版本绑定的外部 app-server watcher core、窄 MCP adapter 与 37 项 hermetic/subprocess 合同测试，结论为 `core_ready_for_live_gate`。这不代表 `external_watcher_supported`；下一步只能由独立 `GKD-M-1C` fresh-session live gate 验证真实 Codex/MCP 接线与唤醒行为。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
