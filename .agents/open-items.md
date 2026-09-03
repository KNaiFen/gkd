# Open Items

已批准并待实施的任务见目标项目 `.gkd/plan.md`：

- 当前路由：`direct-main` 处理简单且未指定子代理的任务；`delegated/manual` 是执行 session 默认入口；用户明确选择自动模式时才使用 `delegated/automatic`。用户明确要求子代理时，选择覆盖简单任务判断。
- 当前交接：main 维护 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`；执行 session 只读取 worktree 内 `.gkd/execution.md`，并更新 `.gkd/progress.md`。

- 验证项目级 `gkd_execute`、`gkd_ci_monitor`、`gkd_accept` 预设能被当前运行时以 `agent_type` 发现和调用；执行/验收为 Sol/xhigh，CI 监控为 Terra/high。
- 扩展 main 路由，新增需求问答、项目适配和 CI 优化 Skills。
- 新增只读、可复用的 GitHub 长流程监控脚本，并完成路由、执行、验收和归档的端到端演练。
- 在 T1 首次施工中验证 PLAN 能否明确表达实现思路，以及执行 session 是否只依赖 worktree 内 `execution.md`；按实际效果迭代文档，不引入门禁或状态机。

写入型自动执行仍须用户明确选择；所有 GitHub 写操作须另行授权。
