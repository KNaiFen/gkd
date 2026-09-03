# Task plan

## 1. Goal and user-visible result

<!-- 写明完成后用户能看到或使用什么，不要只写“优化/补齐”。 -->

## 2. Worktree and route

<!-- 写明 worktree、分支和 delegated/manual 或用户明确选择的 delegated/automatic。 -->

## 3. Scope, non-goals, authorization and stop conditions

<!-- 分别写允许修改、明确不改、需要用户授权的外部动作，以及何种情况必须停止。 -->

## 4. Current evidence

<!-- 列出相关文件、符号、配置键、调用关系和必要行号；只读完成目标所需内容。 -->

## 5. Target design and flow

<!-- 描述组件边界、数据流、控制流，以及与现有行为的差异。 -->

## 6. File-level change table

| Action | File / symbol | Change | Reason |
| --- | --- | --- | --- |
| add / modify / delete |  |  |  |

## 7. Interfaces and configuration

<!-- 写明输入来源、输出格式、错误分类、配置键、兼容性和默认值。 -->

## 8. Key-path pseudocode

<!-- 伪代码必须覆盖正常、拒绝、配置缺失、外部命令失败、超时、用户介入和停止动作。 -->

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

<!-- 说明何时更新 progress.md、完成时报告什么、阻塞时停在哪里。 -->

## 12. Risks, trade-offs and open decisions

<!-- 只有真正需要用户决定的材料性事项留在这里；未清零前不得启动施工。 -->
