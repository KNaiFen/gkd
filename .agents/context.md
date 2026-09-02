# Context

## Current state

- GKD 只保留 manual-first 协作：目标、Git worktree、行为约束，以及 `plan.md`、`progress.md`、`review.md`。
- 唯一项目 Skill 是 `.agents/skills/gkd-main/SKILL.md`；执行 session 不加载其他 GKD Skill。
- 旧自动化实现、合同、测试、证据和路由已从当前工作树删除，Git 历史是唯一追溯方式。

## Boundaries

- `v0.1.5`、生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、tag 和 Release 保持不变，除非用户另行授权。
- 新任务只在独立 worktree 中创建三份 Markdown 记录；不重建旧生命周期或机器状态。
