# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M1-A` 确定性任务核心的 v1 requirements/plan/execution 已在固定 base `1335ac6a9a4dbb5c63570f5a02ba9e713705eebd` 上建立；branch `task/m1-deterministic-task-core`，planning head `b1e8b8d9f00ad53b68162c240134c3cd740d937a`，Draft PR `KNaiFen/gkd#5`。任务等待用户以 GPT-5.6 Sol / xhigh 开启独立人工顶层 execution session；当前 main 不实现任务代码。development version 仍为 `0.0.0-dev.0`，content digest 仍为 `0b8b2487640ff2c78360a18e7f24304f72a8e8c8b5cbd1317ef833c323726228`。旧 D2 外部 watcher 路线保持 `unsupported`；连续一小时 `wait_agent` 尚未通过 fresh runtime 实际门禁，因此 auto route 继续禁用。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
