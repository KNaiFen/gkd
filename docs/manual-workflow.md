# Manual-first 工作流

这是 GKD 唯一的 manual-first 协作方式。它只约定协作材料和工作顺序，不是机器状态机，也不要求填写 JSON、digest、CAS 或专用命令参数。执行 session 默认由用户手动启动；用户明确选择后，main 可以用当前 Codex 已配置的角色启动一个普通子代理。

## 路径选择

1. `direct-main`：简单、低风险任务由 main 直接完成，不创建执行 session。
2. `delegated/manual`：需要执行 session 时的默认路径。main 创建 worktree 和计划，向用户发送启动提示；用户在声明 worktree 中手动启动执行 session。
3. `delegated/automatic`：仅在用户明确选择自动模式时使用。main 读取当前 Codex 已配置且可用的执行角色或 agent type，再通过原生 `spawn_agent` 启动一个执行子代理，并传入 `fork_turns=none`。

自动启动只替代“用户打开一个新 session”这个动作。它不恢复旧 GKD automatic route、机器生命周期或自动验收，也不改变用户对路径选择和审查结论的控制。

## 三个输入

每个任务开始时，主代理只需要确定：

1. **工作目标**：要完成什么，以及完成到什么程度。
2. **工作目录**：执行代理使用的 Git worktree 路径。
3. **行为约束**：允许修改的范围、不能触碰的内容、需要遵守的项目规则。

其他路径、分支名、提交编号和命令行参数由主代理按普通 Git 操作处理，不作为执行代理的协议输入。

## 三份记录

可直接复制的模板位于 `docs/templates/manual/`。

### `plan.md`

由主代理创建和维护。除目标、工作目录和行为约束外，施工前计划必须达到“实现就绪”：写出现状证据、目标行为、范围/非目标、文件与符号级变更表、接口和配置、角色写入边界、正常与失败路径伪代码、逐项验证命令及预期结果、`progress.md` 更新点、停止条件和剩余用户决策。

伪代码必须让执行代理无需重新设计：输入来源、分支条件、调用对象、错误分类和停止动作都要明确；“补齐”“处理异常”“调用脚本”等抽象描述不算完成。任何材料性事项仍是 TBD、验收标准不可复现或无法说明具体改动文件时，main 必须停在规划阶段并向用户确认。施工中若目标行为、文件边界、角色职责、授权范围或主流程发生变化，执行代理先更新 `progress.md` 并停止，main 修改计划并重新取得必要确认。

### `progress.md`

由执行代理持续更新，使用自然语言记录已经完成的工作、当前判断、遇到的问题、未完成事项和下一步。它是交接材料，不是机器状态。

### `review.md`

由主代理在查看 diff 后记录审查结论。通过时写明通过；不通过时写明问题、优先级和下一步。机器事实不需要抄写到这里，直接引用 Git diff、测试输出或文件路径即可。

## 标准顺序

```text
main 选择 direct-main，或为 delegated 路径写 plan.md 并创建独立 Git worktree
delegated/manual：main 交接给用户；delegated/automatic：main 读取已配置角色并启动一个子代理
执行 session 读取 plan.md 并开始工作
执行代理持续更新 progress.md
执行代理完成后通知主代理
主代理查看 diff、plan.md、progress.md
主代理通过，或修改 plan.md/review.md 并在同一 worktree 开始下一轮
```

创建 worktree 和启动执行 session 之间，必须先通过上述 PLAN readiness gate；不能用“先启动再边做边补计划”替代。

## 用户手动启动提示

```text
读取当前 worktree 中的 plan.md 和适用的 AGENTS.md。
只阅读完成目标所需的代码，并在声明的 worktree 中工作。
把重要进展、判断、阻塞和实际运行的验证结果写入 progress.md。
不要修改计划中声明的非目标范围。
完成后停止并通知主代理，由主代理审查 diff。
```

main 将以上提示与声明的 worktree 交给用户；未获用户明确选择自动模式时，main 到此为止，不启动子代理。

## main 自动启动提示

用户明确选择自动模式后，main 先读取当前 Codex 配置中可用的执行角色或 agent type。main 使用当前原生 agents API 的对应配置字段调用一次 `spawn_agent`，传入已读取的角色、`fork_turns=none`、声明的 worktree 和下列提示。角色、模型与权限由当前配置决定，不在本协议中写死。

```text
读取声明 worktree 中的 plan.md 和适用的 AGENTS.md。
只在该 worktree 中施工；不要修改声明的非目标。
在重要判断、里程碑、阻塞和验证结果影响交接时更新 progress.md。
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

通过后按普通 Git 流程合并或保留分支；不通过时修改计划或审查意见，并在同一 worktree 启动下一轮执行 session。后一轮可以是用户手动启动或用户再次明确选择的自动启动，但不得与前一轮并行写入。

## 中断与恢复

新的执行 session 先读取同一个 worktree 的 `plan.md` 和 `progress.md`，再查看未提交 diff 与最近提交。报告不完整时以代码和 Git 历史为准，并把新的判断补回 `progress.md`；不依赖旧对话线程。

## 边界

本协议是唯一正常人工工作流。执行代理不读取无关历史材料，也不调用其他 GKD 自动化入口。自动启动失败不会隐式降级为 `direct-main` 或伪装成手动交接成功。生产 `~/.codex`、AIO、GitHub settings、Secrets、付费 runner 和既有 release 资产不在本协议范围内。
