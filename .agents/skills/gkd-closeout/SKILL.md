---
name: gkd-closeout
description: 在 GKD main 审查通过后，按授权完成 delegated 或 direct-main 任务的归档、现场清理和收尾报告。
---

# GKD Closeout

这是 main 审查通过后的收尾能力。它承接归档、活动记录清理、worktree/分支清理和收尾报告的具体步骤；main 仍拥有审查结论、授权判断和是否宣称成功的决定权。

## 入口条件

- delegated 任务必须已经完成已批准的执行 session，`gkd_accept` 已独立验收通过，main 已在 `.gkd/review.md` 写下当前通过结论。
- direct-main 任务必须已经完成 main 审查，并明确任务 route。
- 归档、cleanup commit、提交/合并、远端分支删除和其他外部动作分别检查 PLAN 授权；不能从“开始执行”授权推断后续所有动作。
- 执行 session 已停止。发现未提交改动、共享活动记录、验收未通过或审查状态不明确时立即停止并保留现场。

## 收尾流程

1. 确认目标项目主工作树、任务逻辑 ID、日期、PLAN/execution/review revision 和本轮 Git 标识；归档中不写本机绝对路径。
2. delegated 成功路径从执行 worktree 读取 `.gkd/execution.md`、`.gkd/progress.md`，从主工作树读取 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`，创建 `.gkd/archive/<task-id>/<date>-<revision>/` 和 `summary.md`。
3. 删除归档快照中的本机绝对路径、令牌、账号、机密值和运行时状态，检查归档能独立说明目标、取舍、结果和风险。用户停止任务或确认阻塞时可以创建临时归档，但必须标记“未验收”或“阻塞中”。
4. 确认归档完整且活动记录只属于当前任务后，只有 PLAN 已授权时才创建包含活动记录删除的 cleanup commit。归档保留，活动 `plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md` 按授权清理。
5. main 审查 cleanup commit；只有已有提交/推送/合并授权时才执行相应 GitHub 或 Git 写操作。任何授权缺失都停在当前可恢复现场并报告。
6. 只有 cleanup commit 已确认合并、执行 session 已停止且 worktree 无未提交改动时，才删除本地任务 worktree 和本地任务分支。远端只删除已确认合并本轮任务的分支，状态不明时保留。
7. 将可信主 checkout 切回 `main`，确认 `git status --short` 为空且跟踪关系清晰。
8. 向用户输出详细收尾报告，包含目标、实际修改、PLAN 偏差、验证和 CI/PR/release 结果、提交标识、归档位置、清理结果及未验证风险。

direct-main 跳过 `gkd_accept` 和 worktree/任务分支删除，但仍执行 main 审查、按需归档、干净 `main` 检查和详细报告。

## 停止条件

验收失败、审查返工、归档脱敏检查失败、活动记录属于多个任务、未提交改动、cleanup commit 或合并未获授权、远端状态不明、主 checkout 无法确认或任何清理条件不满足时，不删除现场，不声称完成，并把阻塞事实交回 main。

本 Skill 不负责本次 GKD 自身的提交、发版或安装到 `~/.codex`；那些是改造完成后的独立交付动作。
