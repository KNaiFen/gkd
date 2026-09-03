# Task plan

## Goal

在保留当前 manual-first、Markdown 交接和单一 `gkd-main` Skill 的前提下，补齐“main 启动执行 session”的实际能力：凡是包含代码修改的普通任务，main 完成计划和独立 worktree 后，必须调用 Codex 原生 `spawn_agent` 启动一个直接子代理；子代理只在该 worktree 中施工并更新 `progress.md`，main 等待结束后审查 diff，再决定合并或返工。

这不是恢复旧 GKD 自动路由，而是把当前文档已经描述的“执行代理”落实为一次明确的原生子代理调用。

## Worktree

本计划在当前仓库维护。实现本计划时，main 必须先创建新的独立 Git worktree，并把实际路径写入该 worktree 的 `plan.md`；未写明路径前不得启动执行子代理。

## Behavior constraints

- 仅对需要修改代码或项目文件的普通任务强制启动执行子代理；纯解释、审查、规划和只读调查不强制派发。
- 每个执行轮次只启动一个直接子代理，调用原生 `spawn_agent`，使用 `fork_turns=none`；不创建嵌套代理，不使用旧的 `gkd_executor` 角色合同。
- main 负责目标、worktree、约束、等待、审查和普通 Git 合并；子代理负责计划范围内的修改、局部验证和 `progress.md`。
- 子代理启动后，main 不得自行修改计划范围内的实现文件；只能读取交接材料、查看 diff、补充审查意见或返工要求。
- `spawn_agent` 不可用、被拒绝或返回不完整时，main 必须报告阻塞并停止，不得在同一 session 中自行完成实现。
- 子代理完成或阻塞后必须停止；返工通过更新 `plan.md`/`review.md` 后，在同一 worktree 启动新的执行轮次。
- 不新增任务状态 JSON、offer/claim/receipt、CAS、runtime bridge、固定 head 验收、专用生命周期 CLI、CI watcher 或第二个通用 GKD Skill。
- 不改变用户授权边界，不要求执行代理验收、合并、发布或启动其他任务。

## Scope

1. 更新 `.agents/skills/gkd-main/SKILL.md`，明确代码任务的强制触发条件、直接 `spawn_agent` 调用、`fork_turns=none`、main/子代理边界、失败时禁止兜底以及返工/恢复方式。
2. 更新 `docs/manual-workflow.md` 和 `docs/templates/manual/plan.md`，让标准顺序和计划字段明确包含“执行子代理使用的 worktree”以及“main 等待后审查”，并提供可直接使用的子代理启动提示词。
3. 更新 `README.md`、`AGENTS.md`、`VISION.md` 和 `docs/adr/002-manual-first-workflow.md` 中受影响的表述：保留 manual-first 和人工审查，说明原生子代理是执行载体；明确这不等于旧 automatic route 或机器生命周期。
4. 检查用户级 `gkd-main` 安装副本及已知项目级重复 skill 的内容一致性；实现完成后，在获得明确安装授权的步骤中同步用户级副本，避免仓库源文件和实际加载的 Skill 分叉。不要把生产 `~/.codex` 的修改伪装成仓库提交。
5. 不为文档性约束新增重量级单元测试；增加一项可复核的最小手工验收记录，覆盖正常派发、正确 worktree、main 不越界和 spawn 失败时不兜底。

## Non-goals

- 不恢复 `gkd-task`、`gkd-role`、`TrustedMainRuntimeBridge` 或历史 canonical bundle。
- 不恢复自动 route 门禁、activation/claim/receipt 状态机、fixed-head acceptance、自动 CI 监控或发布流程。
- 不把所有用户请求都强制派发；只约束实际需要施工的代码任务。
- 不通过提示词宣称“已启动子代理”来替代真实的 `spawn_agent` 调用。
- 不修改目标项目的业务代码。

## Completion conditions

- 当前唯一 `gkd-main` Skill 明确规定：代码任务在 main 自己修改实现前必须先成功调用一次直接 `spawn_agent`，并指定 `fork_turns=none`。
- 启动提示词明确传递当前 worktree、读取范围、`progress.md` 更新责任、停止条件和禁止越界事项。
- 文档、模板、项目规则和用户级安装副本对上述行为没有相互冲突的描述；旧自动化入口仍未被重新引入。
- 用一个临时、低风险的代码任务进行手工验收：session 事件中出现真实子代理；子代理在声明 worktree 中产生变更；main 在子代理终止前没有修改实现文件；最终由 main 审查并完成普通 Git 操作。
- 用一个模拟或受控的 spawn 失败场景验收 fail-closed 行为：main 报告阻塞且实现文件保持不变。
- `progress.md` 记录实际验收命令/观察结果，`review.md` 记录主代理审查结论和剩余风险。
