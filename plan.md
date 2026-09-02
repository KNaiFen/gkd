# 当前项目状态（非进行中任务）

本文件不是待执行的普通任务计划。当前仓库没有挂起的根目录任务；新的人工任务应在独立 worktree 中创建自己的 `plan.md`、`progress.md` 和 `review.md`。

## 当前方向

- 默认工作流是 manual-first：目标、工作目录和行为约束是唯一必需输入。
- 兼容修正已完成并保留在 legacy/historical lane，不恢复 automatic watcher 或旧验收链为普通入口。
- 当前 development bundle 为未发布的 `0.0.0-dev.1`；生产安装仅通过明确授权的 production migration 进行。

## 当前边界

- 已发布 `v0.1.5` 及 AIO、GitHub、Secrets、runner 和 release 资产继续按既有授权边界处理。
- 没有根目录 task 需要执行；后续变更先建立任务目录和对应 worktree。
