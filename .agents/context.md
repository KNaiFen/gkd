# Context

## Current state

- GKD 保留 Git、独立 worktree 与 `plan.md`、`progress.md`、`review.md` 交接；写入型执行 session 默认由用户手动启动，用户明确选择后 main 才可自动启动。
- 项目 `.codex/agents/` 已定义 `gkd_execute`、`gkd_ci_monitor`、`gkd_accept` 三个角色，并固定角色提示词、`gpt-5.6-sol` / `xhigh`、sandbox 和禁止嵌套边界。main 必须以命名 `agent_type` 调用它们，不能退回泛化默认子代理。
- GitHub CI、Actions 和等待中的发布流程将使用项目内只读、无状态的复用脚本监控；它不创建、取消、重跑或发布 GitHub 资源。
- 旧 automatic route、机器生命周期实现、合同、测试和证据已从当前工作树删除，Git 历史是唯一追溯方式；新能力不是这些运行时的兼容入口。

## Boundaries

- `v0.1.5`、生产用户级安装、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 保持不变，除非用户另行授权。
- 不重建旧生命周期或机器状态；提交、推送、合并、创建 release 和实际发布始终保留明确授权边界。
