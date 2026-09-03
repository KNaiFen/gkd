# Open Items

已批准并待实施的任务见目标项目 `.gkd/plan.md`：

- 当前路由：`direct-main` 处理简单且未指定子代理的任务；`delegated/manual` 是执行 session 默认入口；用户明确选择自动模式时才使用 `delegated/automatic`。用户明确要求子代理时，选择覆盖简单任务判断。
- 当前交接：main 维护 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`；执行 session 只读取 worktree 内 `.gkd/execution.md`，并更新 `.gkd/progress.md`。

- 当前已完成 T1-T6；后续待办仅是环境相关的可选验证：项目级角色的真实 `agent_type` 发现/调用与 worktree 隔离、真实 GitHub API 监控和其他项目 `.gkd/archive/` 归档演练。

写入型自动执行仍须用户明确选择；所有 GitHub 写操作须另行授权。
