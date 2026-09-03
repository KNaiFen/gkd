---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调 manual-first 编码任务，并可按用户明确选择启动执行子代理。
---

# GKD Main

这是普通任务的主流程 Skill，强调清晰交接和主代理判断，不把协作材料变成机器状态机。

## 路径选择

1. 简单、低风险且用户未指定子代理时，main 直接处理，不启动执行 session。
2. 用户明确要求使用子代理时，按用户选择进入 delegated 路径，即使任务本身简单。
3. 需求信息不足时使用 `gkd-intake`；它不可用时直接向用户说明缺口并继续沟通，不临时伪造能力。
4. 需要执行 session 时默认 `delegated/manual`：main 创建 sibling worktree，维护 `plan.md`，并在 worktree 生成 `execution.md` 后交给用户手动启动。
5. 用户明确选择自动执行时使用 `delegated/automatic`：main 读取 `.codex/agents/gkd_execute.toml`，以 `agent_type=gkd_execute` 启动一个普通执行 session。角色不可用或配置不符时说明原因并停在当前 worktree，不悄悄换成其他角色。
6. 有明确 GitHub 目标的等待任务可启动 `gkd_ci_monitor`；需要独立审查时可启动 `gkd_accept`。两者只读，main 可以自动衔接；提交、推送、合并和发版仍按用户授权执行。

## 计划和交接

`plan.md` 是 main 的方案文件。施工前应写清目标、成功标准、现状证据、技术栈或现有工具、实现思路、文件/符号范围、验证方式、授权边界和仍需决定的事项。伪代码只在复杂分支、状态转换或外部命令编排确实能帮助理解时使用，不为形式完整而堆砌。

main 从批准的 `plan.md` 生成 worktree 内的 `execution.md`。执行 session 只读取 `execution.md` 和适用的 `AGENTS.md`，按其中的具体文件、步骤和验证要求工作，并更新 `progress.md`；它不把 `plan.md` 当施工指令。

`plan-changes.md` 由 main 追加记录每次计划调整的原因、依据、思路变化和对 execution 文档的影响。验收发现问题时，main 先写 `review.md`，再改 `plan.md`、追加 `plan-changes.md`、更新 `execution.md`，明确通知下一轮 session；旧 session 不会因计划文件变化而隐式改向。

## 角色边界

- `gkd_execute`（Sol/xhigh，workspace-write）：只在声明 worktree 内按 `execution.md` 实现和验证，更新 `progress.md`；不验收、不交付、不启动其他代理。
- `gkd_ci_monitor`（Terra/high，read-only）：调用复用的监控工具并报告，不修改代码或 GitHub。
- `gkd_accept`（Sol/xhigh，read-only）：独立检查计划、execution、diff、progress 和验证结果，向 main 提出通过或返工意见。

同一 worktree 的同一轮只安排一个写入型执行 session，避免相互覆盖；这是协作约定，不是状态机。发现事实与计划不符时，执行 session 在 `progress.md` 留下说明并暂停，main 依据判断调整计划和 execution 文档。

## 默认提示

```text
读取 worktree 内的 execution.md 和适用的 AGENTS.md；不要把 plan.md 当作施工指令。
只在声明范围内完成 execution.md 的任务，按其中的技术方案和验证命令工作。
把重要进展、判断、阻塞和验证结果写入 progress.md；完成后停止并通知 main。
```

自动启动只是替代用户打开普通执行 session，不是旧 automatic route。不要引入旧状态机、JSON 合同、固定 head 验收或常驻 watcher。
