# AGENTS.md

## 项目定位

- 本仓库采用 manual-first Agent 工作流：main 维护 `plan.md`、`plan-changes.md`、`review.md`，worktree 内执行 session 使用 `execution.md` 并更新 `progress.md`；任务完成后可将这些人类可读记录归档到目标项目的 `.gkd/archive/` 子目录。
- 旧 bundle、automatic route、固定 head 验收和发布验证已从当前工作树移除；需要追溯时查看 Git 历史，不恢复迁移流程。用户明确选择时，main 可用当前 Codex 已配置的角色启动普通执行 session；这不是旧自动化流程的恢复。

## 工作规则

- 材料性规划、架构或流程变更前必须完整阅读并遵守 [VISION.md](VISION.md)。
- 普通任务先阅读适用的 `AGENTS.md`；只有会改变 GKD 架构、流程、发布状态或授权边界时，才读取 `.agents/` 中的持久记录。
- 保持变更小而明确，禁止写死仓库、用户名或本机绝对路径。
- 人工任务的持久交接使用上述 Markdown 文件；不要为普通任务新增机器合同或状态副本。项目归档仅保存脱敏后的 Markdown 事实和摘要，不承担运行时状态。
- 只有 GKD 架构、流程、发布状态或授权边界变化时，才同步更新 `.agents/context.md`、`.agents/decisions.md` 和 `.agents/open-items.md`；普通任务不要求更新这三个文件。
