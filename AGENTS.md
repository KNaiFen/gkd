# AGENTS.md

## 项目定位

- 本仓库采用 manual-first Agent 工作流：目标、工作目录、行为约束，以及 `plan.md`、`progress.md`、`review.md`。
- 旧 bundle、自动路由、固定 head 验收和发布验证已从当前工作树移除；需要追溯时查看 Git 历史，不恢复迁移流程。

## 工作规则

- 材料性规划、架构或流程变更前必须完整阅读并遵守 [VISION.md](VISION.md)。
- 普通任务先阅读适用的 `AGENTS.md`；只有会改变 GKD 架构、流程、发布状态或授权边界时，才读取 `.agents/` 中的持久记录。
- 保持变更小而明确，禁止写死仓库、用户名或本机绝对路径。
- 人工任务的持久交接使用 `plan.md`、`progress.md`、`review.md`；不要为普通任务新增机器合同或状态副本。
- 只有 GKD 架构、流程、发布状态或授权边界变化时，才同步更新 `.agents/context.md`、`.agents/decisions.md` 和 `.agents/open-items.md`；普通任务不要求更新这三个文件。
## 当前门禁

- 当前工作树只保留 manual-first 协作材料与 `.agents/skills/gkd-main/SKILL.md`；旧自动化合同、脚本、测试和路由已移除，历史仅从 Git 提交追溯。
- `v0.1.5`、生产 `~/.codex`、AIO、付费 runner、Secrets、既有 tag/Release 和计划外 GitHub 设置保持不变，除非另有明确授权。
