---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调 manual-first 编码任务，并可按用户明确选择启动执行子代理。
---

# GKD Main

这是普通任务唯一的 GKD 工作流 Skill。

1. 先判断路径。简单、低风险且无需执行 session 的任务使用 `direct-main`。其余任务创建独立 sibling worktree，并在 `plan.md` 写明具体目标、worktree 和行为约束；三项任一缺失或仍是模板占位时，不得开始执行。
2. 对需要执行 session 的任务，默认使用 `delegated/manual`：main 向用户发送下面的启动提示，保留 worktree 并等待用户手动打开执行 session。没有用户明确选择自动模式时，不得调用 `spawn_agent`。

   ```text
   读取 plan.md 和适用的 AGENTS.md，只在声明的 worktree 中工作。
   只读取完成计划目标所需的代码；不要检查无关历史或工作流材料。
   在判断、里程碑、阻塞或验证结果会影响交接时更新 progress.md。
   不修改声明的非目标。完成请求的工作后停止并通知主代理。
   ```

3. 只有用户明确选择自动模式时，使用 `delegated/automatic`：main 先读取当前 Codex 环境已配置且可用的执行角色或 agent type，再按当前原生 agents API 将该配置、声明的 worktree 与上面的执行提示交给一次 `spawn_agent` 调用，并传入 `fork_turns=none`。不得在本 Skill 中写死角色名、模型或权限。
4. 自动启动只允许同一 worktree、同一施工轮次的一名实现写者。main 等待该执行 session 停止后才读取结果并审查；执行期间 main 不修改该 worktree 的实现文件。自动 spawn 不可用、配置缺失或调用结果不完整时，main 明确向用户报告阻塞并保留 worktree；不得悄悄切为 `direct-main` 或假称已完成手动交接。
5. 手动或自动启动的执行 session 都不得验收、合并、发布、清理 worktree 或启动其他施工任务。只运行与变更行为直接相关的检查；将实际运行的检查、结果和有意未验证范围写入 `progress.md`，完成后停止并通知 main。
6. main 审查 diff、`plan.md`、`progress.md` 和必要验证，在 `review.md` 记录通过或具体返工要求及剩余风险。通过后使用普通 Git 操作保留或合并工作；返工时更新计划或审查意见，并在同一 worktree 启动新的执行轮次，仍不得并行写入。
7. 恢复 session 时读取 `plan.md`、`progress.md`、当前 diff 和最近提交。报告不完整时以 Git 事实为准，并把新的判断补回 `progress.md`。

自动启动只是由 main 替代用户打开普通执行 session，不是旧 GKD automatic route。不得引入或调用任务状态、JSON 合同、生命周期命令、fixed-head 验收、CI 监控或其他旧工作流 Skill。
