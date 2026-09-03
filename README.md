# GKD

GKD 将需求澄清、方案确认、隔离执行、持续验证、独立验收和授权交付组织成一套完整的项目开发工作流。它先形成实现就绪的 PLAN，再调用配置好的角色在 Git worktree 中执行；manual-first 是默认执行路线。

## 默认：manual-first

GKD 先调查项目和需求；信息不足时通过问答补齐，信息充分后写出实现就绪的 `plan.md`，等待用户确认。简单低风险任务可由 main 直接完成；其余任务默认由用户手动启动执行 session，用户明确选择自动模式后，main 才读取已配置角色并启动一个执行子代理。执行完成后，GKD 可按授权衔接 CI 监控、验收以及提交、发版等交付动作。

每个任务使用三份 Markdown 记录：

- `plan.md`：需求对齐后的实现就绪计划，由主代理维护；包含目标、工作目录、范围、伪代码、验证和行为约束；
- `progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `review.md`：主代理的审查结论，记录通过或可执行的返工意见。

标准顺序是：main 选择 direct-main，或创建计划和 worktree；委派任务默认由用户手动启动执行 session，只有用户明确选择才由 main 自动启动；执行 session 按计划工作并更新进度，完成后通知 main；main 检查 diff、`plan.md`、`progress.md` 和必要的局部验证，随后通过，或修改计划/审查意见后继续执行。中断恢复时，新 session 先读取同一 worktree 的计划和进度，再以 Git diff 与历史为准。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## 当前边界

当前主入口 Skill 是 [gkd-main](.agents/skills/gkd-main/SKILL.md)。需求问答、项目适配和 CI 优化是围绕主流程按需调用的附属能力；它们不能绕过 PLAN、用户确认、worktree 执行和主代理审查。旧 automatic route、机器生命周期合同和脚本不在当前工作树中，需要追溯时查看 Git 历史。既有 `v0.1.5`、生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 均不属于本仓库的日常流程。
