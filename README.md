# GKD

GKD 将需求澄清、方案确认、隔离执行、持续验证、独立验收和授权交付组织成一套完整的项目开发工作流。它先形成实现就绪的 PLAN，再在用户明确批准后调用配置好的角色在 Git worktree 中执行；manual-first 是默认执行路线。

## 默认：manual-first

GKD 先调查项目和需求；信息不足时通过问答补齐，信息充分后写出具体的 `.gkd/plan.md`，等待用户明确说“按此 PLAN 开始执行”。只拟 PLAN 时不创建 worktree/分支、不写代码、不启动代理、不提交或清理。批准后，简单低风险任务可由 main 直接完成；其余任务默认由用户手动启动执行 session，用户明确选择自动模式后，main 才以 `agent_type=gkd_execute` 启动执行 session。需要等待 PR、workflow run、commit 或 release CI 时，必须由命名的 `gkd_ci_monitor` 只读子代理调用目标项目的 `scripts/gkd-github-watch`，每次显式传入 `--interval 30 --timeout 3600`；改变任一参数须有 PLAN 授权，main 一次性等待终态。执行完成后，GKD 可按授权衔接验收以及提交、发版等交付动作。

每个 delegated 任务在目标项目 `.gkd/` 中使用五份 Markdown 记录：

- `.gkd/plan.md`：main 的方案、技术栈、实现思路、范围和授权；
- `.gkd/execution.md`：目标 worktree 内当前轮次的执行交接，执行 session 只读取它；
- `.gkd/progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `.gkd/plan-changes.md`：main 对方案调整的追加式思路记录；
- `.gkd/review.md`：main 的独立验收结论和返工意见。

标准顺序是：main 先停在 plan-only 并等待明确批准；批准后选择 direct-main，或创建计划、worktree 和 `.gkd/execution.md`；委派任务默认由用户手动启动执行 session，只有用户明确选择才由 main 以 `agent_type=gkd_execute` 自动启动；执行 session 更新 `.gkd/progress.md`，需要 CI 等待时由 `gkd_ci_monitor` 返回一次终态；已批准的 delegated 执行完成后才由 `gkd_accept` 独立验收，main 再写 `.gkd/review.md`。delegated 成功必须先创建并检查脱敏归档，再按授权创建包含活动记录删除的 cleanup commit，经过 main 审查/合并后仅清理已确认合并的本轮本地/远端分支，恢复干净 `main` 并输出详细收尾报告；审查不通过、远端状态不明或清理条件不满足时保留现场并报告阻塞。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## 当前边界

当前主入口 Skill 是 [gkd-main](.agents/skills/gkd-main/SKILL.md)。需求问答、项目适配和 CI 优化是围绕主流程按需调用的附属能力；它们不能绕过 PLAN、用户确认、worktree 执行和主代理审查。旧 automatic route、机器生命周期合同和旧自动脚本不在当前工作树中；当前 `scripts/gkd-github-watch` 是保留的 CI 只读入口，不是旧 watcher 或自动路由的兼容层，需要追溯旧机制时查看 Git 历史。既有 `v0.1.5`、生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 均不属于本仓库的日常流程。
