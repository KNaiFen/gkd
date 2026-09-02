# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

## 默认：manual-first

普通任务只需要三项人工输入：工作目标、执行代理使用的 Git worktree，以及允许修改/必须遵守的行为约束。主代理把它们写入 `plan.md`，执行代理在同一 worktree 中工作并持续更新 `progress.md`，主代理查看代码 diff、计划和报告后，在 `review.md` 中通过或提出返工要求。

每个任务使用三份 Markdown 记录：

- `plan.md`：目标、工作目录和行为约束由主代理维护；范围、非目标和完成条件按任务需要补充；
- `progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `review.md`：主代理的审查结论，记录通过或可执行的返工意见。

标准顺序是：主代理创建计划和 worktree，执行代理按计划工作并更新进度，完成后通知主代理；主代理检查 diff、`plan.md`、`progress.md` 和必要的局部验证，随后通过，或修改计划/审查意见后继续执行。中断恢复时，新 session 先读取同一 worktree 的计划和进度，再以 Git diff 与历史为准。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## 历史材料

已发布的 `v0.1.5`、旧任务记录、automatic/fixed-head/release 证据和 Codex 版本观察记录只读保留，用于理解历史决策和核对回归。它们不属于当前入口，仓库不再提供旧生产安装、角色迁移或兼容恢复流程。

当前 development bundle 只承担 foundation 与 `gkd-main` Skill；普通任务不需要 `gkd-task`、`gkd-role`、旧 executor/acceptor/CI Skills 或机器合同。旧源码和测试只读保留，不应被新任务路由调用。
