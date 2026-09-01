# Manual-first 工作流

这是 GKD 迁移后的默认人工协作方式。当前处于施工期；它只约定协作材料和工作顺序，不是新的机器状态机，也不要求填写 JSON、digest、CAS 或专用命令参数。

## 三个输入

每个任务开始时，主代理只需要确定：

1. **工作目标**：要完成什么，以及完成到什么程度。
2. **工作目录**：执行代理使用的 Git worktree 路径。
3. **行为约束**：允许修改的范围、不能触碰的内容、需要遵守的项目规则。

其他路径、分支名、提交编号和命令行参数由主代理按普通 Git 操作处理，不作为执行代理的协议输入。

## 三份记录

### `plan.md`

由主代理创建和维护，至少说明目标、工作目录、行为约束、范围、非目标和完成条件。计划可以在返工时直接修改，不要求固定 schema。

### `progress.md`

由执行代理持续更新，使用自然语言记录已经完成的工作、当前判断、遇到的问题、未完成事项和下一步。它是交接材料，不是机器状态。

### `review.md`

由主代理在查看 diff 后记录审查结论。通过时写明通过；不通过时写明问题、优先级和下一步。机器事实不需要抄写到这里，直接引用 Git diff、测试输出或文件路径即可。

## 标准顺序

```text
主代理写 plan.md
主代理创建独立 Git worktree
执行代理读取 plan.md 并开始工作
执行代理持续更新 progress.md
执行代理完成后通知主代理
主代理查看 diff、plan.md、progress.md
主代理通过，或修改 plan.md/review.md 要求返工
```

## 执行代理启动提示词

```text
读取当前 worktree 中的 plan.md。
按照其中的目标、范围和行为约束工作。
把重要进展、判断、阻塞和下一步写入 progress.md。
不要修改计划中声明的非目标范围。
完成后停止并通知主代理，由主代理审查 diff。
```

## 主代理审查

主代理只需检查：

- diff 是否完成目标并保持在范围内；
- 是否违反行为约束或项目规则；
- progress.md 是否说明了实际完成情况和剩余风险；
- 必要的局部测试或手工验证是否足够。

主代理不需要重建 offer、claim、activation、receipt、delivery manifest 或 fixed-head acceptance。通过后按普通 Git 流程合并或保留分支；不通过时修改计划并让执行代理继续。

## 中断与恢复

新的执行 session 先读取同一个 worktree 的 `plan.md` 和 `progress.md`，再查看未提交 diff 与最近提交。报告不完整时以代码和 Git 历史为准，并把新的判断补回 `progress.md`。不要求恢复旧的 runtime、锁、nonce 或对话线程。

## 边界

本协议是正常人工工作流。`canonical/`、`gkd-task`、`gkd-role`、watcher、release 和旧验证材料在迁移完成前作为 legacy 保留；它们不应被新的执行代理 prompt 主动调用。生产 `~/.codex`、AIO、GitHub settings、Secrets、付费 runner 和既有 release 资产仍不在本协议范围内。
