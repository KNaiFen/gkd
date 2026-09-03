# ADR-002: Manual-first agent workflow

## Status

Accepted

## Date

2026-09-01

## Context

GKD 曾把人工协作、自动路由、固定验收、发布自验证和历史兼容放在同一套工作流中。结果是一次普通任务需要准备大量机器参数、状态记录、JSON 工件和专用脚本。

用户实际需要的是一个由主代理和执行代理共同完成的人工闭环：主代理写计划并创建 worktree，执行代理按计划工作并持续落盘进度，主代理查看 diff 和报告后通过或修改计划要求返工。Git worktree、计划和进度报告已经足以支持这个闭环。

## Decision

GKD 的新默认形态改为 manual-first：

- 人类只向正常工作流提供工作目标、工作目录和行为约束。
- 每个 delegated 任务使用 main 维护的 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`，以及 worktree 内执行代理使用的 `.gkd/execution.md`、`.gkd/progress.md` 五类 Markdown 文件。
- main 拥有计划、计划变更历史和审查结论；执行代理拥有 execution 交接和进度报告；Git worktree 是代码事实源。执行 session 不把 `.gkd/plan.md` 当作施工指令。
- 中断恢复依靠 worktree、计划和进度报告，不依靠 runtime attachment、receipt、journal 或自动 reclaim。
- 返工通过主代理先记录 `.gkd/review.md`，再修改计划、追加 `.gkd/plan-changes.md` 并更新 `.gkd/execution.md` 交接后继续执行，不创建新的 offer/claim/activation 生命周期；旧 execution session 不受计划修改的隐式影响。
- 需要执行 session 的委派任务默认由用户手动启动；用户明确选择自动模式时，main 可以读取当前 Codex 已配置角色并通过原生 agents API 启动一个普通执行子代理。两种入口都使用同一 worktree 的 `.gkd/execution.md` / `.gkd/progress.md` 交接，完成后仍由 main 审查。
- 旧 automatic route、fixed-head acceptance、机器事实 renderer、默认 CI monitor 和大规模合同验证不再位于当前工作树；需要追溯时使用 Git 历史。原生子代理启动不提供旧路由、状态机或验收兼容入口。

`v0.1.5` 发行物和既有发布资产保持不变；新 manual-first 实现不提供旧生产安装、角色迁移或兼容恢复入口。

## Alternatives

### 继续优化现有 automatic workflow

可以继续减少 CLI 参数并复用结果，但仍会保留 task state、CAS、receipt、bridge、acceptance 和大量隐式状态。这解决的是输入摩擦，不解决工作流模型过度自动化的问题，因此拒绝作为默认方向。

### 完全删除 Git 和持久报告

这会让中断后的恢复依赖对话上下文，无法审查代码变更，也无法把返工要求交给新的 session。保留 Git worktree、main 计划和 worktree 执行交接及报告，是人工流程的最低必要记录，因此拒绝。

### 同时保留两套默认工作流

双默认会继续制造入口选择和上下文负担。manual-first 是唯一正常入口，`delegated/manual` 是默认委派入口；用户明确选择的原生自动启动只是同一入口的可选启动方式。已移除的旧能力只能从 Git 历史追溯。

## Consequences

正面结果：普通任务不再要求机器 JSON、CAS、digest、runtime root、PR/head 参数或专用验收脚本；主代理可直接审查 diff，执行代理可通过报告恢复；当用户明确选择时，无需用户手动新开 session 也能保持同一交接边界。

代价：自动化防漂移、固定证据和跨进程恢复不再是普通任务保证；旧流程由 Git 历史保存。

重新评估条件：如果未来重新需要无人值守执行、跨机器自动恢复或可审计发布，必须另立 ADR，不得把这些要求偷偷塞回 manual-first 默认路径。
