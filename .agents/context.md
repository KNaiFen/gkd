# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M1-A` 独立人工顶层 execution session 已实现确定性任务核心；implementation/evidence commit 为 `1798b0f2c32571c803c399179c27090f94d21c0a`，候选 outcome 仅为 `deterministic_task_core_ready`，等待 PR #5 新 fixed head 的独立验收。development version 仍为 `0.0.0-dev.0`，content digest 为 `f29a594cd138a1b4e039b1411b953a6795f9b21a27b6086fdd540479c408faeb`，evidence digest 为 `164ab691af9fa1af9137386da2169aba3cd065793366815d53077557f69b3774`；95项task-core、53项foundation、47项watcher core和15项watcher live-negative通过。GitHub仍无configured checks或main branch protection，必须记为bootstrap缺口而非CI成功。旧 D2外部watcher路线保持历史`unsupported`；连续一小时 `wait_agent` 尚未通过fresh runtime实际门禁，因此auto route继续禁用。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
