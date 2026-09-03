# GKD

GKD 将需求澄清、方案确认、隔离执行、持续验证、独立验收和授权交付组织成一套完整的项目开发工作流。它先形成实现就绪的 PLAN，再调用配置好的角色在 Git worktree 中执行；manual-first 是默认执行路线。

## 默认：manual-first

GKD 先调查项目和需求；信息不足时通过问答补齐，信息充分后写出具体的 `plan.md`，等待用户确认。简单低风险任务可由 main 直接完成；其余任务默认由用户手动启动执行 session，用户明确选择自动模式后，main 才读取已配置角色并启动一个执行子代理。执行完成后，GKD 可按授权衔接 CI 监控、验收以及提交、发版等交付动作。

每个 delegated 任务在目标项目 `.gkd/` 中使用五份 Markdown 记录：

- `.gkd/plan.md`：main 的方案、技术栈、实现思路、范围和授权；
- `.gkd/execution.md`：目标 worktree 内当前轮次的执行交接，执行 session 只读取它；
- `.gkd/progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `.gkd/plan-changes.md`：main 对方案调整的追加式思路记录；
- `.gkd/review.md`：main 的独立验收结论和返工意见。

标准顺序是：main 选择 direct-main，或在目标项目 `.gkd/` 创建计划和 worktree；委派任务默认由用户手动启动执行 session，只有用户明确选择才由 main 自动启动；main 生成 `.gkd/execution.md`，执行 session 按它工作并更新进度，完成后通知 main；main 检查 diff、五份记录和必要的局部验证，随后通过，或记录 review、修改 plan、追加 plan-changes、更新 execution 后继续执行。任务完成后可把记录摘要归档到 `.gkd/archive/`。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## 当前边界

当前主入口 Skill 是 [gkd-main](.agents/skills/gkd-main/SKILL.md)。需求问答、项目适配和 CI 优化是围绕主流程按需调用的附属能力；它们不能绕过 PLAN、用户确认、worktree 执行和主代理审查。旧 automatic route、机器生命周期合同和脚本不在当前工作树中，需要追溯时查看 Git 历史。既有 `v0.1.5`、生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 均不属于本仓库的日常流程。
