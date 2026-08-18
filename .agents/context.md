# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M1-A` fixed head `f0b339c0d52ae9325137e9f188b710645c2e2e80` 已通过独立终验，并以 squash commit `5eb3bd34ef389361be2ba22df899ad088ef22da1` 进入 main；里程碑 1 完成，结论仅为 `deterministic_task_core_ready`。development version 仍为 `0.0.0-dev.0`，content digest 为 `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`，evidence digest 为 `3f119831c41a18536318b621f21f13d8d18d115fce77e3fb97870a0148395569`；独立复验 task-core 104 项两次、foundation 53 项、watcher core 47 项和 watcher live-negative 15 项均通过。GitHub 无 configured checks 或 main branch protection，保持 `required_checks_not_configured_bootstrap`。下一步在清理 M1 worktree/分支后规划里程碑 2；固定角色、runtime evidence provider 与连续一小时 `wait_agent` 门尚未通过，因此 auto route 继续禁用，仍须人工顶层 session。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
