# Manual-first 工作流

GKD 将需求对齐、具体方案、隔离执行、CI 监控、独立验收和授权交付串成一套完整工作流。本文规定其中默认的 manual-first 协作方式；它只约定协作材料和工作顺序，不是机器状态机，也不要求填写 JSON、digest、CAS 或专用命令参数。目标项目的活动交接文档统一放在 `.gkd/`；执行 session 默认由用户手动启动，用户明确选择后，main 可以用当前 Codex 已配置的角色启动一个普通子代理。

## 路径选择

1. `direct-main`：简单、低风险且用户未指定子代理的任务由 main 直接完成，不创建执行 session；用户明确要求子代理时，以用户选择覆盖复杂度判断。
2. `delegated/manual`：需要执行 session 时的默认路径。main 在目标项目 `.gkd/` 维护 `plan.md` 并在 worktree 生成 `.gkd/execution.md`，向用户发送启动提示；用户在声明 worktree 中手动启动执行 session。
3. `delegated/automatic`：仅在用户明确选择自动模式时使用。main 先生成或更新 worktree 内 `.gkd/execution.md`，再读取当前 Codex 已配置且可用的命名执行角色，通过原生 `spawn_agent` 启动一个执行子代理，并传入 `fork_turns=none`。

自动启动只替代“用户打开一个新 session”这个动作。它不恢复旧 GKD automatic route、机器生命周期或自动验收，也不改变用户对路径选择和审查结论的控制。

## 三个输入

每个任务开始时，主代理只需要确定：

1. **工作目标**：要完成什么，以及完成到什么程度。
2. **工作目录**：执行代理使用的 Git worktree 路径。
3. **行为约束**：允许修改的范围、不能触碰的内容、需要遵守的项目规则。

其他路径、分支名、提交编号和命令行参数由主代理按普通 Git 操作处理，不作为执行代理的协议输入。

## 五份记录

可直接复制的模板位于 `docs/templates/manual/`。

### `plan.md`

由 main 在目标项目 `.gkd/` 创建和维护，是主方案、技术选型、实现思路、授权和审查依据。施工前计划应写出现状证据、目标行为、采用的技术栈/现有工具、关键实现步骤、范围/非目标、文件与符号级变更表、接口和配置、角色写入边界、逐项验证命令及预期结果、`progress.md` 更新点和仍需决定的事项。只有存在非显然分支、状态转换或外部命令编排时才写针对性伪代码。

`plan.md` 不是执行 session 的施工指令。施工中若目标行为、文件边界、角色职责、授权范围或主流程发生变化，执行代理先更新 `progress.md` 并停止，main 修改计划并重新取得必要确认。

### `execution.md`

由 main 从已批准的 `plan.md` 生成，必须位于目标 worktree 内，是执行 session 的唯一任务交接文档。它写明当前 revision、可修改文件/符号、实现步骤、技术约束、验证命令和本轮具体修改建议；执行 session 读取它和适用的 `AGENTS.md`，不把 `plan.md` 当作施工指令。

### `plan-changes.md`

由 main 追加维护，记录每次 PLAN 修订的原因、验收依据、影响、授权变化、旧思路与新思路，以及对应的 `execution.md` revision；不覆盖旧条目。

### `progress.md`

由执行代理持续更新，使用自然语言记录已经完成的工作、当前判断、遇到的问题、未完成事项和下一步。它是执行事实，不是机器状态；不承担 PLAN 变更历史。

### `review.md`

由 main 在查看 diff 后记录审查结论。通过时写明通过；不通过时先写问题、优先级和下一步，再修改 `plan.md`、追加 `plan-changes.md`，并更新 worktree 内 `execution.md` 的 revision 和具体修改建议。机器事实不需要抄写到这里，直接引用 Git diff、测试输出或文件路径即可。

## 项目归档

一轮 delegated 施工完成、用户决定停止或明确保留当前成果时，main 可在目标项目创建 `.gkd/archive/<task-id>/<date>-<revision>/`。其中保存该轮 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/execution.md`、`.gkd/progress.md`、`.gkd/review.md` 和 `summary.md`，让后续工作能理解目标、实现思路、实际结果和遗留风险。归档是普通 Markdown 与 Git 内容：不写本机绝对路径、令牌或运行时状态；不建立索引服务；简单 `direct-main` 任务只在确实有长期价值时归档。是否把归档随目标项目提交，仍由该任务的 PLAN 和用户授权决定。

## 标准顺序

```text
main 选择 direct-main，或在目标项目 `.gkd/` 写 plan.md 并创建独立 Git worktree
delegated 路径：main 在 worktree 的 `.gkd/` 写 execution.md；manual 交接给用户，automatic 在明确授权后启动一个命名执行角色
执行 session 读取 `.gkd/execution.md` 并开始工作
执行代理持续更新 `.gkd/progress.md`
执行代理完成后通知主代理
主代理查看 diff、`.gkd/plan.md`、`.gkd/execution.md`、`.gkd/progress.md`
主代理通过，或先写 `.gkd/review.md`，再修改 `.gkd/plan.md`/`.gkd/plan-changes.md` 和 `.gkd/execution.md`，并在同一 worktree 开始下一轮
主代理仅按 PLAN 中已获授权的动作提交、推送、合并或发版；未授权则停在交付前
```

创建 worktree 和启动执行 session 之间，main 应先把方案和执行交接写清楚；施工中发现新事实时可由 main 灵活调整文档，不把它当成机器门禁。

## 用户手动启动提示

```text
读取当前 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只阅读完成 execution.md 所需的代码，并在声明的 worktree 中工作。
把重要进展、判断、阻塞和实际运行的验证结果写入 .gkd/progress.md。
不要修改计划中声明的非目标范围。
完成后停止并通知主代理，由主代理审查 diff。
```

main 将以上提示与声明的 worktree 交给用户；未获用户明确选择自动模式时，main 到此为止，不启动子代理。

## main 自动启动提示

用户明确选择自动模式后，main 先读取当前 Codex 配置中可用的执行角色或 agent type。main 使用当前原生 agents API 的对应配置字段调用一次 `spawn_agent`，传入已读取的角色、`fork_turns=none`、声明的 worktree 和下列提示。角色、模型与权限由当前配置决定，不在本协议中写死。

```text
读取声明 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只在该 worktree 中施工；不要修改声明的非目标。
在重要判断、里程碑、阻塞和验证结果影响交接时更新 .gkd/progress.md。
完成后停止并通知 main。不要验收、合并、发布、清理 worktree 或启动其他施工代理。
```

同一 worktree 的同一施工轮次只允许这个子代理写实现文件。main 在其停止前不修改实现文件；若角色配置、spawn 调用或启动结果不可用，main 明确报告阻塞并保留 worktree，等待用户选择下一条路径。

## 主代理审查

主代理只需检查：

- diff 是否完成目标并保持在范围内；
- 施工前 PLAN 是否达到实现就绪，伪代码和文件级边界是否覆盖实际改动；
- 是否违反行为约束或项目规则；
- progress.md 是否说明了实际完成情况和剩余风险；
- 必要的局部测试或手工验证是否足够。

通过后按 PLAN 中已经获授权的普通 Git 流程提交、推送、合并或发版；未授权的动作停在交付前，不临时追加确认来替代计划。通过后也可以只保留分支。不通过时先记录 `review.md`，再修改 main 的 `plan.md`，追加 `plan-changes.md`，更新 worktree `execution.md` 并明确通知下一轮 session；旧 execution session 不受 PLAN 修改的隐式影响。后一轮可以是用户手动启动或用户再次明确选择的自动启动，但不得与前一轮并行写入。

## 中断与恢复

新的执行 session 先读取同一个 worktree 的 `.gkd/execution.md` 和 `.gkd/progress.md`，再查看未提交 diff 与最近提交。需要理解计划为何变化时，由 main 提供 `.gkd/plan-changes.md`；报告不完整时以代码和 Git 历史为准，并把新的判断补回 `.gkd/progress.md`；不依赖旧对话线程。

## 边界

本协议是唯一正常人工工作流。执行代理不读取无关历史材料，也不调用其他 GKD 自动化入口。自动启动失败不会隐式降级为 `direct-main` 或伪装成手动交接成功。生产 `~/.codex`、AIO、GitHub settings、Secrets、付费 runner 和既有 release 资产不在本协议范围内。
