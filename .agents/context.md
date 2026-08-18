# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1C` 已由 GPT-5.6 Sol / xhigh 人工顶层 execution session 完成，outcome 固定为 `unsupported`。PR `KNaiFen/gkd#3` 交付外部 watcher live probe、脱敏证据和明确失败边界；Gate 1-8 fail，Gate 9 pass，auto route 保持禁用，manual handoff 继续可用。不得开始里程碑 0。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
