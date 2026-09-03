# Task plan

## 1. Goal and user-visible result

<!-- 写明完成后用户能看到或使用什么，不要只写“优化/补齐”。 -->

## 2. Worktree and route

<!-- 写明 worktree、分支和 delegated/manual 或用户明确选择的 delegated/automatic。简单任务默认 direct-main；用户明确要求子代理时，以用户选择覆盖复杂度判断。 -->

## 3. Scope, non-goals, authorization and open questions

<!-- 分别写允许修改、明确不改、需要用户授权的外部动作，以及仍需 main 或用户判断的事项。 -->

## 4. Current evidence

<!-- 列出相关文件、符号、配置键、调用关系和必要行号；只读完成目标所需内容。 -->

## 5. Target design and flow

<!-- 写清需求如何实现：技术栈/现有工具、组件边界、数据流、控制流、关键步骤，以及与现有行为的差异。只有非显然分支、状态转换或外部命令编排才写针对性伪代码。 -->

## 6. File-level change table

| Action | File / symbol | Change | Reason |
| --- | --- | --- | --- |
| add / modify / delete |  |  |  |

## 7. Interfaces and configuration

<!-- 写明输入来源、输出格式、错误分类、配置键、兼容性和默认值。 -->

## 8. Key-path pseudocode (when needed)

<!-- 仅在确有复杂分支时填写；写清该分支的关键输入、调用、结果和需要交回 main 判断的情形。 -->

```text
input = ...
if ...:
    ...
else:
    ...
```

## 9. Role and write boundaries

<!-- 写明 main、执行、CI 监控、验收各自可读/可写范围和禁止动作。 -->

## 10. Verification matrix

| Check | Command / fixture | Expected result | Not run / reason |
| --- | --- | --- | --- |
|  |  |  |  |

## 11. Handoff and progress updates

<!-- 说明 main 如何从本计划生成 worktree 内 execution.md，何时更新 progress.md，以及如何在验收返工时追加 plan-changes.md、更新 execution.md 并通知下一轮 session。 -->

## 12. Risks, trade-offs and open decisions

<!-- 只有真正需要用户决定的材料性事项留在这里；未清零前不得启动施工。 -->
