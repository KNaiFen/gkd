# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M-1C` fixed head `4332cea7aecc7540640add626ddca6b9b3d8cbad` 已通过独立验收，并由 PR #3 squash merge 为 `afacf490aee948a0e70910304976da6c667375fa`；outcome 固定为 `unsupported`，Gate 1-8 fail、Gate 9 pass。D2 auto route 保持禁用，后续里程碑继续使用人工顶层 session；下一步建立 `GKD-M0-A` canonical 基础与章程任务。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
