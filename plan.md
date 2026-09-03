# Task plan

## Goal

在当前 manual-first、Markdown 交接和单一 `gkd-main` Skill 架构上，补回旧工作流的执行 session 启动能力。执行 session 仍只在独立 sibling worktree 中施工，由 main 审查结果；启动方式分为两种：

1. **手动启动（默认）**：main 写好 `plan.md` 并创建 worktree，向用户提供交接提示；用户手动打开执行 session。
2. **自动启动（可选）**：用户明确选择自动模式后，main 使用 Codex 中已配置的角色启动子代理执行 session。

同时保留旧流程中的 `direct-main`：简单、低风险任务可以由 main 连续完成，不创建执行 session。

## Worktree

实现 worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/subagent-session-capability`。main 已从当前 `main` 创建该 sibling Git worktree；执行 session 只能在此路径中工作。

## Historical alignment

Git 历史中的实际流程是：main 规划并创建 worktree -> 交接 `plan.md` -> 执行 session 施工并更新进度 -> 执行 session 停止 -> main 查看 diff 和报告 -> 通过或写返工意见 -> 在同一 worktree 开始下一轮。2026-09-01 的真实试运行还验证了自动入口：main 调用 `agents.spawn_agent`，传入 `agent_type=worker` 和 `fork_turns=none`，等待子代理结束后再审查；返工时重新启动下一轮。

旧 AIO 规则同时规定：简单低风险任务可由 main 直接做；委派、并行、长流程、范围较大或风险较高的任务才使用 sibling worktree。这个路由判断和当前 Markdown 交接应保留。

## Target behavior

| 路径 | 启动者 | 默认 | main 的动作 | 执行 session |
|---|---|---:|---|---|
| `direct-main` | main | 仅简单低风险任务 | 直接在允许的 checkout/分支施工 | 不存在 |
| `delegated/manual` | 用户 | 是 | 创建 sibling worktree，写 `plan.md`，发送启动提示并等待 | 用户在声明 worktree 手动启动，按计划施工 |
| `delegated/automatic` | main | 否 | 创建 sibling worktree，读取已配置角色并调用 `spawn_agent`，传入 worktree 和执行提示 | 被启动的角色只施工并更新 `progress.md` |

三条路径都使用同一套 `plan.md`、`progress.md`、`review.md` 和 Git diff。自动启动不是旧的 GKD automatic route；它只是把“用户新开执行 session”替换成“main 通过原生 agents 工具新开执行 session”。

## Behavior constraints

- `delegated/manual` 是默认执行 session 入口；没有明确的自动选择时，main 只交接，不调用 `spawn_agent`。
- `delegated/automatic` 只有在用户选择自动模式后才启用。main 必须读取并使用当前 Codex 已配置的角色/agent type；不可把未配置的角色名、模型或权限写死在 GKD 文档里。
- 自动入口保持历史调用语义：启动一个直接执行子代理并使用 `fork_turns=none`。这里的“一个”是同一 worktree、同一施工轮次的唯一实现写者；下一轮返工可以重新启动，验收阶段的只读审查代理不受此限制。
- 无论手动还是自动，执行 session 都是普通 Codex session：只读计划和适用规则，在声明 worktree 中修改，更新 `progress.md`，完成后停止；不得验收、合并、发布、清理或启动其他施工代理。
- 执行 session 活动期间，main 不修改该 worktree 的实现文件。session 停止后，main 读取 diff、计划和进度，写 `review.md`，通过则按普通 Git 操作合并，不通过则修改计划/审查意见后启动下一轮。
- 自动 spawn 不可用、角色配置缺失或调用返回不完整时，main 报告阻塞并保留 worktree；不得悄悄改成 direct-main 或伪装成手动交接成功。是否切换路径由用户明确决定。
- 不新增任务状态 JSON、offer/claim/receipt、CAS、runtime bridge、固定 head 验收、专用生命周期 CLI、CI watcher 或第二个通用 GKD Skill。

## Scope

1. 更新 `.agents/skills/gkd-main/SKILL.md`：加入三条路径的判定、默认手动入口、自动入口的角色读取和 `spawn_agent` 交接、执行 session 边界、等待、返工和失败处理。
2. 更新 `docs/manual-workflow.md` 和 `docs/templates/manual/plan.md`：恢复旧版的规划、worktree、交接、执行、暂停、审查顺序，并分别提供用户手动启动提示和 main 自动启动提示。
3. 更新 `README.md`、`AGENTS.md`、`VISION.md`、`docs/adr/002-manual-first-workflow.md` 及 `.agents/` 持久记录：说明“可自动启动执行 session”与已删除的旧 automatic route/机器生命周期不是同一件事。
4. 检查用户级 `gkd-main` 安装副本和已知项目级重复 skill，消除冲突描述；仓库改动完成后，另行执行明确授权的用户级安装同步。
5. 不新增重量级单元测试；用低风险临时任务做手工验证，保存 main/child session 事件、worktree、diff 和 Markdown 记录作为证据。

## Non-goals

- 不恢复 `gkd-task`、`gkd-role`、`TrustedMainRuntimeBridge` 或历史 canonical bundle。
- 不恢复旧的 route 门禁、activation/claim/receipt 状态机、fixed-head acceptance、自动 CI 监控或发布流程。
- 不把所有任务强制派发；`direct-main` 和默认 `delegated/manual` 都必须继续可用。
- 不允许两个施工 session 同时写同一 worktree；这不限制后续返工轮次或只读审查代理。
- 不修改目标项目业务代码。

## Completion conditions

- `gkd-main` 能根据任务形态和用户选择，明确落到 `direct-main`、`delegated/manual` 或 `delegated/automatic`；未选择自动时默认是手动启动。
- 手动验收能证明：main 创建并记录 worktree/plan，用户启动执行 session，执行 session 修改正确 worktree 并更新 `progress.md`。
- 自动验收能证明：main 使用实际配置的角色调用 `spawn_agent`，事件中存在子代理 session，子代理在相同声明 worktree 中施工并更新 `progress.md`。
- 两种执行 session 都能在完成后回到 main 审查；返工在原 worktree 通过新轮次继续，不发生并行写入。
- 自动入口失败时能看到明确阻塞，且没有隐藏的 direct-main 兜底或假交接。
- 文档、用户级安装副本和已知项目入口一致；旧机器生命周期入口没有重新出现。
- `progress.md` 记录真实手工验收，`review.md` 记录 main 的通过/返工结论和剩余风险。
