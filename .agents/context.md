# Context

## Current state

- GKD 将需求澄清、方案确认、隔离执行、持续验证、独立验收和授权交付组织成完整项目开发工作流；需求问答、项目适配和 CI 优化是服务主流程的附属能力。
- GKD 保留 Git、独立 worktree 与 Markdown 交接：main 维护目标项目 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`，执行 session 使用 worktree 内 `.gkd/execution.md` 并更新 `.gkd/progress.md`；已批准 delegated 成功后必须归档到目标项目 `.gkd/archive/`。写入型执行 session 默认由用户手动启动，用户明确选择自动模式后 main 才可用命名 `agent_type=gkd_execute` 自动启动。
- 项目 `.codex/agents/` 已定义 `gkd_execute`、`gkd_ci_monitor`、`gkd_accept` 三个角色；执行/验收固定为 `gpt-6-astra` / `xhigh`，CI 监控固定为 `gpt-5.6-terra` / `medium`，并固定 sandbox、提示词和禁止嵌套边界。main 启动执行时必须使用命名 `agent_type=gkd_execute`，不能退回泛化默认子代理。
- PLAN 由 main 写清实现思路、技术栈、文件/符号和验证方式；伪代码只在复杂分支确有帮助时使用。施工发现材料性偏差时，执行 session 在 `.gkd/progress.md` 说明，main 结合判断更新计划与 execution 交接，不建立形式化状态机或门禁。
- GitHub CI、Actions 和等待中的发布流程将使用随 `gkd-ci-monitor` Skill 安装的只读、无状态脚本监控；它不创建、取消、重跑或发布 GitHub 资源。
- `plan-only` 只允许调查、问答和写 PLAN；只有用户明确批准“按此 PLAN 开始执行”后，main 才能创建 worktree/分支、启动角色或写代码。需要等待 CI 时必须由 `gkd_ci_monitor` 单目标显式调用已安装 `gkd-ci-monitor` Skill 目录中的 `scripts/gkd-github-watch --interval 30 --timeout 3600`；改变 interval 或 timeout 任一参数须有 PLAN 授权，目标项目不需要提供同名脚本，main 一次性等待终态。
- delegated 执行完成后才可由 `gkd_accept` 独立验收；main 审查通过后路由到 `gkd-closeout` Skill，完成脱敏归档、按授权 cleanup commit、审查/合并、清理已确认合并的本轮任务分支、恢复干净 `main` 和详细报告；失败、未授权或远端状态不明时保留现场。临时 `gkd-legacy-cleanup` 只按明确老项目和逐项授权盘点/清理旧活动机制，不触碰普通业务、历史归档或生产用户目录。
- 旧 automatic route、机器生命周期实现、合同、测试和证据已从当前工作树删除，Git 历史是唯一追溯方式；新能力不是这些运行时的兼容入口。
- 早期 r10 草案及被后续 revision 取代的审查只作为 superseded 历史背景；当前流程以最新已批准 PLAN、execution 交接、progress 和 review 结论为准。

## Boundaries

- `v0.1.5`、生产用户级安装、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 保持不变，除非用户另行授权。
- 不重建旧生命周期或机器状态；提交、推送、合并、创建 release 和实际发布始终保留明确授权边界。
