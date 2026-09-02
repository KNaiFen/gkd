# GKD

GKD 的 manual-first 协作规范。

## 默认：manual-first

普通任务只需要三项人工输入：工作目标、执行代理使用的 Git worktree，以及允许修改/必须遵守的行为约束。主代理把它们写入 `plan.md`，执行代理在同一 worktree 中工作并持续更新 `progress.md`，主代理查看代码 diff、计划和报告后，在 `review.md` 中通过或提出返工要求。

每个任务使用三份 Markdown 记录：

- `plan.md`：目标、工作目录和行为约束由主代理维护；范围、非目标和完成条件按任务需要补充；
- `progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `review.md`：主代理的审查结论，记录通过或可执行的返工意见。

标准顺序是：主代理创建计划和 worktree，执行代理按计划工作并更新进度，完成后通知主代理；主代理检查 diff、`plan.md`、`progress.md` 和必要的局部验证，随后通过，或修改计划/审查意见后继续执行。中断恢复时，新 session 先读取同一 worktree 的计划和进度，再以 Git diff 与历史为准。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## 当前边界

唯一 GKD Skill 是 [gkd-main](.agents/skills/gkd-main/SKILL.md)。它只协调计划、worktree、进度和审查；执行 session 不加载其他 GKD Skill。旧自动化合同和脚本不在当前工作树中，需要追溯时查看 Git 历史。既有 `v0.1.5`、生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 均不属于本仓库的日常流程。
