# ADR-002: Manual-first agent workflow

## Status

Accepted

## Date

2026-09-01

## Context

GKD 的当前默认路径把人工协作、自动 executor 路由、固定 head 验收、发布自验证和历史兼容放在同一套工作流中。结果是一次普通任务需要准备大量机器参数、状态记录、JSON 工件和专用脚本。`gkd-main` 已经能够推导其中一部分事实，但仍然要求操作者理解并穿越完整的 task/claim/delivery/acceptance 状态机。

用户实际需要的是一个由主代理和执行代理共同完成的人工闭环：主代理写计划并创建 worktree，执行代理按计划工作并持续落盘进度，主代理查看 diff 和报告后通过或修改计划要求返工。Git worktree、计划和进度报告已经足以支持这个闭环。

## Decision

GKD 的新默认形态改为 manual-first：

- 人类只向正常工作流提供工作目标、工作目录和行为约束。
- 每个任务使用 `plan.md`、`progress.md` 和 `review.md` 三类 Markdown 文件。
- 主代理拥有计划和审查结论；执行代理拥有进度报告；Git worktree 是代码事实源。
- 中断恢复依靠 worktree、计划和进度报告，不依靠 runtime attachment、receipt、journal 或自动 reclaim。
- 返工通过主代理修改计划或审查意见后继续执行，不创建新的 offer/claim/activation 生命周期。
- 自动 route、fixed-head acceptance、机器事实 renderer、默认 CI monitor 和大规模合同验证只读保留为历史材料，不再进入普通任务路径。

`v0.1.5` 发行物、旧任务记录和 AIO 证据保持只读；新 manual-first 实现不提供旧生产安装、角色迁移或兼容恢复入口，也不修改既有发布资产。

## Alternatives

### 继续优化现有 automatic workflow

可以继续减少 CLI 参数并复用结果，但仍会保留 task state、CAS、receipt、bridge、acceptance 和大量隐式状态。这解决的是输入摩擦，不解决工作流模型过度自动化的问题，因此拒绝作为默认方向。

### 完全删除 Git 和持久报告

这会让中断后的恢复依赖对话上下文，无法审查代码变更，也无法把返工要求交给新的 session。保留 Git worktree 和三份 Markdown 是人工流程的最低必要记录，因此拒绝。

### 同时保留两套默认工作流

双默认会继续制造入口选择和上下文负担。manual-first 作为唯一正常入口，旧 automatic 能力只作为历史材料读取，不再作为路由或迁移面。

## Consequences

正面结果：普通任务不再要求机器 JSON、CAS、digest、runtime root、PR/head 参数或专用验收脚本；主代理可直接审查 diff，执行代理可通过报告恢复；流程与人的实际工作方式一致。

代价：自动化防漂移、固定证据和跨进程恢复不再是普通任务保证；旧 bundle、旧任务记录和旧发布流程只读保留；现有 tests、Skills、CLI 和文档按历史价值分批归档。

重新评估条件：如果未来重新需要无人值守执行、跨机器自动恢复或可审计发布，必须另立 ADR，不得把这些要求偷偷塞回 manual-first 默认路径。
