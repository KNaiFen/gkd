# AGENTS.md

## 项目定位

- 本仓库正在迁移到 manual-first Agent 工作流：目标、工作目录、行为约束，以及 `plan.md`、`progress.md`、`review.md`。
- 迁移完成前，原有 `v0.1.5` bundle、自动路由、固定 head 验收和发布验证仍作为 legacy 实现保留。

## 工作规则

- 材料性规划前必须完整阅读并遵守 [VISION.md](VISION.md)。
- 修改前阅读最近的 `AGENTS.md` 以及 `.agents/` 中的持久记录。
- 保持变更小而明确，禁止写死仓库、用户名或本机绝对路径。
- 人工任务的持久交接使用 `plan.md`、`progress.md`、`review.md`；不要为普通任务新增机器合同或状态副本。
- 项目状态变化时同步更新 `.agents/context.md`、`.agents/decisions.md` 和 `.agents/open-items.md`。
- 完成任务前运行与变更范围相称的最小验证，并记录可复核证据。
- 每个完成的任务单独提交，使用简短、具体的中文提交说明。

## 当前门禁

- 本次 manual-first 重构已获用户授权，但先按阶段施工；旧 automatic workflow 不再作为新任务入口。
- `v0.1.5`、生产 `~/.codex`、AIO、付费 runner、Secrets、既有 tag/Release 和计划外 GitHub 设置保持不变，除非另有明确授权。
