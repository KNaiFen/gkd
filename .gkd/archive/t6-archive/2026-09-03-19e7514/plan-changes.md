# Plan changes

本文件由 main 追加维护，记录方案为什么变化，以及变化如何传递给执行交接；不覆盖历史条目。

## Revision log

| Revision | Reason / evidence | Plan change | Authorization impact | execution.md update |
| --- | --- | --- | --- | --- |
| 2026-09-03-r1 | 用户明确要求 PLAN 先讲清实现方式、技术栈和思路，而非为每项工作堆伪代码。 | 把固定伪代码/章节门槛改为以实现方案为主的建议结构；只在复杂控制流时写伪代码。 | 无新增外部授权。 | 后续 delegated 任务从方案提炼文件/符号级执行步骤。 |
| 2026-09-03-r2 | 用户要求 main 方案与执行 session 交接隔离，验收返工不能隐式改动执行中的任务。 | 明确 `plan.md`、`plan-changes.md`、`review.md` 由 main 维护；新增 worktree 内 `execution.md`。 | 无新增外部授权。 | 执行 session 只读取 `execution.md`；main 更新 PLAN 后显式更新 execution revision。 |
| 2026-09-03-r3 | 用户要求目标项目保留施工历史，又不希望恢复旧状态机或合同。 | 增加项目级 `.gkd/archive/` 归档任务和摘要模板。 | 归档是否随目标项目提交由任务 PLAN 和用户授权决定。 | 完成或停止的任务可归档当前 execution/progress/review 与摘要。 |
| 2026-09-03-r4 | 用户补充：活动交接文档也应放在项目 `.gkd/`，并强调不要用门禁/状态机替代模型判断。 | 将活动 `plan.md`、`plan-changes.md`、`review.md`、`execution.md`、`progress.md` 统一放入 `.gkd/`；把 PLAN 要求改为实现思路和技术栈优先，伪代码按需。 | 无新增外部授权。 | execution 交接路径统一为 `.gkd/execution.md`，返工通过显式 revision 传递。 |
| 2026-09-03-r5 | T2 需要可复用 GitHub 监控工具，且外部命令编排是实现关键。 | 明确 Python 3 标准库 + `gh api` 只读方案、目标参数、统一报告、退出码和 fake `gh` 测试覆盖。 | 仍只读；不新增 GitHub 写操作。 | T2 execution 将包含 CLI 参数、查询端点、测试夹具和超时行为。 |
| 2026-09-03-r6 | T2 独立验收发现显式 repo 仍依赖 origin，单次 API timeout 可能超过全局 timeout，且非有限浮点参数未约束。 | 明确显式 repo 可脱离 origin；为 interval/timeout 增加有限值校验；每次 gh 调用 timeout 取全局剩余时间上限；补充对应测试。 | 仍只读；不新增 GitHub 写操作。 | T2 execution 更新为 r6，增加边界修正和测试夹具。 |
| 2026-09-03-r7 | T4 验收发现 CI 优化 Skill 对资料不足只写报告事实缺口，未明确少量提问策略。 | 要求 `gkd-optimize-ci` 只询问会改变优化方向的少量事实，并将其余不确定性列为证据缺口。 | 无新增外部授权。 | T4 execution 更新为 r7，补充该措辞和静态核对。 |
| 2026-09-03-r8 | 用户补充施工交接材料也应属于目标项目长期记录，不能只停留在活动 `.gkd/` 文件。 | T6 明确以目标项目 `.gkd/archive/<task-id>/<date>-<revision>/` 保存本轮关键 Markdown 快照和 `summary.md`；归档目录不引入状态机、索引服务或机器路径。 | 归档是否随功能提交仍由任务 PLAN 和用户授权决定；本仓库本轮创建示例归档不涉及外部发布。 | T6 execution 增加归档目录、快照清单、脱敏规则和本地验证。 |
