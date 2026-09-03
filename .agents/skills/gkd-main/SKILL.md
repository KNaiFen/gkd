---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调 manual-first 编码任务，并可按用户明确选择启动执行子代理。
---

# GKD Main

这是普通任务唯一的 GKD 工作流 Skill。

1. 先判断路径。简单、低风险且无需执行 session 的任务使用 `direct-main`。修改代码使用 `delegated/manual` 或用户明确选择的 `delegated/automatic`；有明确 GitHub 目标的等待任务使用 `gkd_ci_monitor`；需要独立审查时使用 `gkd_accept`。写入型路径开始前，必须创建独立 sibling worktree，并在 `plan.md` 写明具体目标、worktree 和行为约束；三项任一缺失或仍是模板占位时，不得开始执行。
2. `plan.md` 必须先达到“实现就绪”再启动执行。至少包含：现状证据、目标行为、范围/非目标、文件与符号级变更表、接口和配置、角色写入边界、正常与失败路径伪代码、逐项验证命令及预期结果、progress 更新点、停止条件和剩余用户决策。伪代码必须明确输入来源、分支条件、调用对象、错误分类和停止动作；“补齐”“处理异常”“调用脚本”等抽象描述不算完成。任何材料性事项仍写成 TBD、缺少可复现验收标准或无法说明具体改哪些文件时，主代理必须停在规划阶段并向用户确认。
3. 对需要执行 session 的任务，默认使用 `delegated/manual`：main 向用户发送下面的启动提示，保留 worktree 并等待用户手动打开执行 session。没有用户明确选择自动模式时，不得调用 `spawn_agent`。

   ```text
   读取 plan.md 和适用的 AGENTS.md，只在声明的 worktree 中工作。
   只读取完成计划目标所需的代码；不要检查无关历史或工作流材料。
   在判断、里程碑、阻塞或验证结果会影响交接时更新 progress.md。
   不修改声明的非目标。完成请求的工作后停止并通知主代理。
   ```

4. 只有用户明确选择自动模式时，使用 `delegated/automatic`：main 以 `agent_type=gkd_execute` 调用一次原生 `spawn_agent`，并传入声明的 worktree、上面的执行提示和 `fork_turns=none`。`gkd_execute` 的提示词、`gpt-5.6-sol`、`xhigh` 与 sandbox 只在 `.codex/agents/gkd_execute.toml` 定义；不得用泛化默认子代理替代它。
5. `gkd_ci_monitor` 只在父代理提供明确 GitHub 目标时启动；其模型和强度由 `.codex/agents/gkd_ci_monitor.toml` 固定为 `gpt-5.6-terra / high`。`gkd_accept` 只在已有 worktree、计划和交接材料时启动，固定为 `gpt-5.6-sol / xhigh`。两者均为只读角色，可由 main 自动衔接，但不得取代用户对代码修改、提交、推送、合并或发版的授权。
6. 自动启动只允许同一 worktree、同一施工轮次的一名实现写者。main 等待该执行 session 停止后才读取结果并审查；执行期间 main 不修改该 worktree 的实现文件。角色配置、`agent_type` 调用或启动结果不可用时，main 明确向用户报告阻塞并保留 worktree；不得悄悄切为 `direct-main` 或泛化子代理。
7. 手动或自动启动的执行 session 都不得验收、合并、发布、清理 worktree 或启动其他施工任务。只运行与变更行为直接相关的检查；将实际运行的检查、结果和有意未验证范围写入 `progress.md`，完成后停止并通知 main。
8. main 审查 diff、`plan.md`、`progress.md` 和必要验证，在 `review.md` 记录通过或具体返工要求及剩余风险。通过后只按 PLAN 中已获授权的动作使用普通 Git 流程提交、推送、合并或发版；未授权动作停在交付前。返工时更新计划或审查意见，并在同一 worktree 启动新的执行轮次，仍不得并行写入。
9. 恢复 session 时读取 `plan.md`、`progress.md`、当前 diff 和最近提交。报告不完整时以 Git 事实为准，并把新的判断补回 `progress.md`。

自动启动只是由 main 替代用户打开普通执行 session，不是旧 GKD automatic route。不得引入任务状态、JSON 合同、生命周期命令、fixed-head 验收或旧 watcher；`gkd_ci_monitor` 是项目内按需调用的只读角色，而非旧自动化平台。施工代理发现材料性偏差时必须先更新 `progress.md` 并停止，主代理更新 `plan.md`、重新取得必要确认后才能继续。
