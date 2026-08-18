# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1B` 新固定 head `98df6ba122d9fe8aed230094ed806010e7002aa7` 已通过独立终验，并由 PR #2 squash merge 为 `1d303456f2afcaa4e5fd0353232e30c5c6b63a33`；47项合同和确定性证据复验通过。当前结论仅为 `core_ready_for_live_gate`，`GKD-M-1C` 尚未开始，禁止宣称 `external_watcher_supported`。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
