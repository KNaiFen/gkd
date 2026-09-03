# Plan changes

本文件由 main 追加维护，记录方案为什么变化，以及变化如何传递给执行交接；不覆盖历史条目。

## Revision log

| Revision | Reason / evidence | Plan change | Authorization impact | execution.md update |
| --- | --- | --- | --- | --- |
| 2026-09-03-r1 | 用户明确要求 PLAN 先讲清实现方式、技术栈和思路，而非为每项工作堆伪代码。 | 把固定伪代码/章节门槛改为以实现方案为主的建议结构；只在复杂控制流时写伪代码。 | 无新增外部授权。 | 后续 delegated 任务从方案提炼文件/符号级执行步骤。 |
| 2026-09-03-r2 | 用户要求 main 方案与执行 session 交接隔离，验收返工不能隐式改动执行中的任务。 | 明确 `plan.md`、`plan-changes.md`、`review.md` 由 main 维护；新增 worktree 内 `execution.md`。 | 无新增外部授权。 | 执行 session 只读取 `execution.md`；main 更新 PLAN 后显式更新 execution revision。 |
| 2026-09-03-r3 | 用户要求目标项目保留施工历史，又不希望恢复旧状态机或合同。 | 增加项目级 `.gkd/archive/` 归档任务和摘要模板。 | 归档是否随目标项目提交由任务 PLAN 和用户授权决定。 | 完成或停止的任务可归档当前 execution/progress/review 与摘要。 |
| 2026-09-03-r4 | 用户补充：活动交接文档也应放在项目 `.gkd/`，并强调不要用门禁/状态机替代模型判断。 | 将活动 `plan.md`、`plan-changes.md`、`review.md`、`execution.md`、`progress.md` 统一放入 `.gkd/`；把 PLAN 要求改为实现思路和技术栈优先，伪代码按需。 | 无新增外部授权。 | execution 交接路径统一为 `.gkd/execution.md`，返工通过显式 revision 传递。 |
