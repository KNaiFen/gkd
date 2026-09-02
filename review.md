# 当前项目审查

## 结论

当前仓库指导方向与实现状态一致：manual-first 是普通任务唯一入口，兼容实现和旧自动化能力是显式 legacy/optional 面。

## 已审查

- 默认入口只围绕目标、worktree、行为约束，以及三份 Markdown 交接记录。
- 最近兼容修正没有增加普通任务所需的机器参数、合同、CAS、receipt 或 fixed-head acceptance。
- 当前生产 GKD managed surface 已记录为 development bundle `0.0.0-dev.1`，但该版本仍未发布、未接入 AIO。

## 后续

若要删除或继续归档 legacy 实现，应另立计划并单独审查；不要把 legacy 维护步骤加入普通 manual-first 任务。
