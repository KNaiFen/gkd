# 当前项目审查

## 结论

当前仓库指导方向与实现状态一致：manual-first 是唯一入口，旧自动化实现仅是历史材料，不再形成兼容迁移面。

## 已审查

- 默认入口只围绕目标、worktree、行为约束，以及三份 Markdown 交接记录。
- 最近兼容修正没有增加普通任务所需的机器参数、合同、CAS、receipt 或 fixed-head acceptance。
- 当前生产 GKD managed surface 只保留 `gkd-main` Skill；development bundle `0.0.0-dev.1` 仍未发布、未接入 AIO。

## 后续

旧源码和历史证据继续只读保留；不要把它们的维护、迁移或验证步骤加入普通 manual-first 任务。
