# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

## 默认：manual-first

普通任务只需要三项人工输入：工作目标、执行代理使用的 Git worktree，以及允许修改/必须遵守的行为约束。主代理把它们写入 `plan.md`，执行代理在同一 worktree 中工作并持续更新 `progress.md`，主代理查看代码 diff、计划和报告后，在 `review.md` 中通过或提出返工要求。

每个任务使用三份 Markdown 记录：

- `plan.md`：目标、范围、非目标、行为约束和完成条件，由主代理维护；
- `progress.md`：已完成事项、判断、阻塞、风险和下一步，由执行代理维护；
- `review.md`：主代理的审查结论，记录通过或可执行的返工意见。

标准顺序是：主代理创建计划和 worktree，执行代理按计划工作并更新进度，完成后通知主代理；主代理检查 diff、`plan.md`、`progress.md` 和必要的局部验证，随后通过，或修改计划/审查意见后继续执行。中断恢复时，新 session 先读取同一 worktree 的计划和进度，再以 Git diff 与历史为准。详见 [Manual-first 工作流](docs/manual-workflow.md) 及 [VISION](VISION.md)。

## Legacy：旧自动工作流

迁移完成前，已发布的 `v0.1.5` legacy bundle 及其 `gkd-task`/`gkd-role`、automatic runtime bridge、watcher、fixed-head acceptance、release engine 和专属 verifier 仅作为 legacy/兼容能力保留；当前开发线为未发布的 `0.0.0-dev.1`，也不是普通任务入口。旧命令不应由新的执行代理 prompt 主动调用；既有发布资产、生产目录和 AIO 保持不变。

Legacy CLI、project staging 与 automatic runtime bridge 最低支持 Python 3.9。仓库 CI policy 位于 `.gkd/policy.json`；旧验证入口包括 `scripts/gkd-verify --base-sha <full-sha>`，以及必须显式指定的 `--lane historical`、`optional-ci-advice`、`optional-review-remediation` 和 `optional-packs` lane。结果复用可使用 `--results-dir <directory>` 与 `--canonical-results <directory>`；automatic delivery、historical evidence 和 host-capability probe 仍遵循各自旧参数和固定树约束。
