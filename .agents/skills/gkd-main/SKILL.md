---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调一项 manual-first 编码任务。
---

# GKD Main

这是普通任务唯一的 GKD 工作流 Skill。

1. 主代理创建独立 Git worktree，并在 `plan.md` 写明具体目标、worktree 和行为约束。三项任一缺失或仍是模板占位时，不得开始执行。
2. 用下面的提示词启动普通执行 session：

   ```text
   读取 plan.md 和适用的 AGENTS.md，只在声明的 worktree 中工作。
   只读取完成计划目标所需的代码；不要检查无关历史或工作流材料。
   在判断、里程碑、阻塞或验证结果会影响交接时更新 progress.md。
   不修改声明的非目标。完成请求的工作后停止并通知主代理。
   ```

3. 执行代理不得验收、合并、发布或启动其他任务。只运行与变更行为直接相关的检查；将实际运行的检查、结果和有意未验证范围写入 `progress.md`。
4. 主代理审查 diff、`plan.md`、`progress.md` 和必要验证，在 `review.md` 记录通过或具体返工要求及剩余风险。通过后使用普通 Git 操作保留或合并工作。
5. 恢复 session 时读取 `plan.md`、`progress.md`、当前 diff 和最近提交。报告不完整时以 Git 事实为准，并把新的判断补回 `progress.md`。

不得引入或调用任务状态、JSON 合同、生命周期命令、固定 head 验收、CI 监控或其他旧工作流 Skill。
