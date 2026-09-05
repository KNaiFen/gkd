# Open Items

已批准并待实施的任务见目标项目 `.gkd/plan.md`：

- 早期 r10 草案和旧审查结论均为 superseded 历史背景；不得把它们当作当前施工授权或规则来源，当前事实以最新 revision 的 PLAN、execution 和 review 为准。

- 当前路由：`direct-main` 处理简单且未指定子代理的任务；`delegated/manual` 是执行 session 默认入口；用户明确选择自动模式时才使用 `delegated/automatic`。用户明确要求子代理时，选择覆盖简单任务判断。
- 当前交接：main 维护 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`；执行 session 只读取 worktree 内 `.gkd/execution.md`，并更新 `.gkd/progress.md`。
- 当前授权闸门：`plan-only` 不创建 worktree/分支、代码或代理；只有用户明确批准“按此 PLAN 开始执行”后才进入 delegated/direct-main。材料性变更须追加 `plan-changes.md` 并重新确认。
- 当前 CI 约束：需要等待时由 `gkd_ci_monitor` 对单一目标显式调用已安装 `gkd-ci-monitor` Skill 目录中的 `scripts/gkd-github-watch --interval 30 --timeout 3600`；改变任一参数须有 PLAN 授权，目标项目不需要提供同名脚本，main 一次性等待终态，入口缺失/漂移/认证错误即阻塞。
- 当前收尾约束：已批准 delegated 执行完成后才由 `gkd_accept` 独立验收；main 审查通过后路由到 `gkd-closeout`，由其按授权完成脱敏归档、cleanup commit、审查/合并、已确认合并的本轮任务分支清理、恢复干净 `main` 和详细报告；异常或远端状态不明时保留现场。`gkd-legacy-cleanup` 仅按明确老项目和逐项授权使用。

- 当前已完成 T1-T6；后续待办仅是环境相关的可选验证：项目级角色的真实 `agent_type` 发现/调用与 worktree 隔离、真实 GitHub API 监控和其他项目 `.gkd/archive/` 归档演练。

写入型自动执行仍须用户明确选择；所有 GitHub 写操作须另行授权。
