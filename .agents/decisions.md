# Decisions

- [2026-09-01] 采用 manual-first 作为唯一工作流。
  - Why: 普通编码任务只需要目标、工作目录、行为约束和可审查交接，不需要自动生命周期。
  - Impact: 主代理维护计划和审查，执行代理维护进度，Git worktree 是代码事实源。

- [2026-09-02] 移除旧自动化合同实现。
  - Why: 旧脚本、JSON 合同、角色路由和固定验收会扩大上下文和入口选择，却不服务当前人工闭环。
  - Impact: 当前工作树只保留 `gkd-main` 与 Markdown 协作材料；历史从 Git 提交追溯。

- [2026-09-02] 验证遵循最少必要原则。
  - Why: 为无关变更运行完整旧合同会增加时间和上下文成本。
  - Impact: 只运行与计划目标和改动直接相关的局部检查，并把实际结果或未验证范围写入交接记录。

- [2026-09-03] 恢复执行 session 的双启动入口。
  - Why: 用户仍需要保留手动交接作为默认，同时可明确选择由 main 启动已配置角色，减少新开 session 的操作。
  - Impact: `delegated/manual` 保持默认；`delegated/automatic` 只以原生 `spawn_agent` 打开一个普通执行 session，继续使用 worktree 和 Markdown 交接，不恢复旧 automatic route 或机器生命周期。
