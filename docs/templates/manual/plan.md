# Task plan

<!-- main 在目标项目 `.gkd/plan.md` 维护本文件；它是方案和授权记录，不是执行 session 的施工指令。 -->

## 1. Goal and user-visible result

<!-- 写明完成后用户能看到或使用什么，不要只写“优化/补齐”。 -->

## 2. Worktree and route

<!-- 写明 worktree、分支和 delegated/manual 或用户明确选择的 delegated/automatic。自动执行只能使用命名 agent_type=gkd_execute。简单任务默认 direct-main；用户明确要求子代理时，以用户选择覆盖复杂度判断。 -->

## 3. Scope, non-goals, authorization and open questions

<!-- 分别写允许修改、明确不改、需要用户授权的外部动作、停止条件，以及仍需 main 或用户判断的事项。标明当前是 plan-only（只拟方案）还是已明确批准“按此 PLAN 开始执行”；前者禁止创建 worktree/代理、代码写入、提交、推送、合并、发布和清理。 -->

## 4. Current evidence

<!-- 列出相关文件、符号、配置键、调用关系和必要行号；只读完成目标所需内容。 -->

## 5. Target design and flow

<!-- 写清需求如何实现：技术栈/现有工具、组件边界、数据流、控制流、关键步骤，以及与现有行为的差异。只有非显然分支、状态转换或外部命令编排才写针对性伪代码。 -->

## 6. File-level change table

| Action | File / symbol | Change | Reason |
| --- | --- | --- | --- |
| add / modify / delete |  |  |  |

## 7. Interfaces and configuration

<!-- 写明输入来源、输出格式、错误分类、配置键、兼容性和默认值。若需要等待 CI，写明唯一目标（--pr/--run/--commit/--release）、仓库，并要求 gkd_ci_monitor 每次显式传入 --interval 30 --timeout 3600；改变任一参数须有 PLAN 授权，且仅由该角色调用 scripts/gkd-github-watch。 -->

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

<!-- 补充 CI/PR/release 终态、计划偏差和清理条件的验证；记录实际未运行项和原因。 -->

## 11. Handoff and progress updates

<!-- 说明 main 如何从本计划生成 worktree 内 `.gkd/execution.md`，执行 session 何时更新 `.gkd/progress.md`，以及如何在验收返工时追加 `.gkd/plan-changes.md`、更新 execution 并通知下一轮 session。写明已批准 delegated 执行完成后才由 gkd_accept 验收，再 review、归档、按授权 cleanup commit、审查/合并、活动记录和已确认合并分支清理、恢复干净 main 的顺序。 -->

### Deviation and closeout

<!-- 记录实现与 PLAN 的一致/偏差、偏差原因和新增授权；写明归档位置、summary.md、归档后 cleanup commit 及 main 审查/合并条件、活动记录删除条件、worktree/本地与远端分支清理结果和用户详细报告。远端仅删除已确认合并本轮任务的分支，状态不明时保留现场并报告阻塞。 -->

## 12. Risks, trade-offs and open decisions

<!-- 只有真正需要用户决定的材料性事项留在这里；未清零前不得启动施工。 -->
