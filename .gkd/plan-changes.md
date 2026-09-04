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
| 2026-09-03-r9 | T6 独立验收发现首轮示例在 main 审查前创建，`review.md`/`summary.md` 仍是“等待审查”状态。 | 把归档拆为执行阶段准备材料、main 验收后生成最终快照；最终 `review.md` 和 `summary.md` 必须反映验收结论，旧目录不得覆盖。 | 无新增外部授权；归档仍不自动提交或发布。 | T6 execution 更新为 r9；本轮主收口新建带 r9 标识的最终归档目录，保留首轮材料，不让执行 session 伪造验收结论。 |
| 2026-09-04-r10 | 复盘 session `01a0689d-d152-7f60-a4a6-a23fddf1fbc0`：CI 阶段未使用 CI 子代理；主代理把“拟 PLAN”误解为施工授权；缺少老项目旧 Skill 的一次性清理能力；完成后缺少详细用户报告和干净 main 收尾。 | 新增 CI 专用约束 Skill 与角色调用/等待规则；把 `plan-only` 与执行授权分离；新增临时 `gkd-legacy-cleanup`；强制详细收尾报告、归档后清理 worktree/本地分支并恢复干净 `main`。明确不设计兼容模式。 | 本 revision 只授权继续规划和文档设计；不授权目标项目施工、代理启动、CI/发布或删除动作。 | 待用户继续讨论和确认；确认前不生成 execution、不创建施工 worktree。 |
| 2026-09-04-r10.1 | 用户明确“归档后即完成清理”：当前草案只写了归档和 worktree/分支清理，未删除项目活动 PLAN 文件。 | 收尾新增“确认归档完整后删除本轮活动 `plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`，仅保留 `.gkd/archive/`”；若记录混有其他任务则先拆分或停止。 | 仍只授权规划；不授权当前执行或删除。 | 待用户继续确认；删除动作必须在未来任务 PLAN 中明确执行。 |
| 2026-09-04-r10.2 | 用户确认采用最小审查版本方案，避免旧结论与当前事实混淆，同时降低模型更新文档的操作复杂度。 | `review.md` 顶部保留唯一当前审查块（PLAN/execution/head/status）；旧审查只追加一行 superseded 标记；不新增状态机、JSON 或额外历史文件。 | 仍只授权规划；不授权当前执行或文档实现。 | 待用户继续讨论后，在未来 execution 中同步模板和规则。 |
| 2026-09-04-r10.3 | PLAN 自检发现顶部“已完成”与 r10“待确认”冲突，且收尾顺序遗漏已有的 `gkd_accept` 独立验收角色。 | 将顶部状态改为“r10 草案待确认”，并把 `gkd_accept` -> main `review.md` 纳入收尾必经顺序和验收标准；不改变任务范围或授权。 | 仍只授权规划；不授权当前执行。 | 未来 execution 沿用修订后的收尾和验收顺序。 |
| 2026-09-04-r10.4 | PLAN 自检发现把 `gkd_accept` 写成所有任务的必经步骤会给 `direct-main` 增加不必要的代理成本。 | 将独立验收限定为 `delegated` 任务；`direct-main` 由 main 做同等范围的轻量审查，并分别定义收尾顺序和成功标准。 | 仍只授权规划；不授权当前执行。 | 未来 execution 按任务路由选择对应收尾路径。 |
| 2026-09-04-r10.5 | PLAN 自检发现历史 T1-T6 与当前 r10 草案共存，缺少当前施工范围指针，可能使执行者误读历史内容。 | 在文件状态区明确本轮只执行 r10（含 r10.1-r10.4），T1-T6 仅作历史基线。 | 仍只授权规划；不授权当前执行。 | 未来 execution 只从 r10 草案提炼施工范围。 |
| 2026-09-04-r10.6 | 用户明确批准按 r10 开始施工，并选择自动/子代理执行；同时明确要求施工完成后清理本地任务分支与远端任务分支。 | 将 r10 状态切换为已批准、执行中；本轮施工范围包含本授权记录，收尾在验收、归档和合并条件满足后处理本轮本地及远端任务分支。 | 已授权 `delegated/automatic` 施工，以及完成条件满足后的本轮任务分支清理；未额外授权发布或其他 GitHub 写操作。 | 新建 execution revision r10.6，明确执行代理边界和主代理收尾责任。 |
