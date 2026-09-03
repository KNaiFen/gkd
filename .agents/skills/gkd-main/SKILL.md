---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调 manual-first 编码任务，并可按用户明确选择启动执行子代理。
---

# GKD Main

这是普通任务的主流程 Skill。它用 Git worktree 和 Markdown 记录协调工作，保留 main 的判断，不把协作材料变成机器状态机。

## 路径选择

1. 简单、低风险且用户未指定子代理时，main 直接处理，使用 `direct-main`。
2. 用户明确要求使用子代理时，用户选择覆盖复杂度判断，进入 delegated 路径。
3. 需求缺少会改变目标、范围、验收、行为约束、工作目录或授权的材料性事实时，先使用 `gkd-intake` 逐项对齐；该 Skill 不可用则向用户说明缺口并继续沟通。
4. 需要执行 session 时默认使用 `delegated/manual`：main 创建 sibling worktree，在目标项目 `.gkd/` 维护方案并生成 worktree 内的 `.gkd/execution.md`，然后交给用户手动启动。
5. 只有用户明确选择自动执行时才使用 `delegated/automatic`：main 读取 `.codex/agents/gkd_execute.toml`，通过原生 `spawn_agent` 以 `agent_type=gkd_execute` 和 `fork_turns=none` 启动一个执行 session。角色不可用或配置不符时报告阻塞并保留 worktree，不切换到其他角色或 `direct-main`。
6. 父代理提供明确 GitHub 目标时可启动 `gkd_ci_monitor`；已有 worktree 和交接材料时可启动 `gkd_accept`。两者只读，提交、推送、合并和发版仍须按计划和用户授权执行。

## 计划和交接

main 维护目标项目 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`。开始施工前，方案应说明目标、成功标准、现状证据、技术栈或现有工具、实现思路、文件/符号范围、接口配置、验证方式、授权边界和仍需决定的事项。只有复杂分支、状态转换或外部命令编排难以用自然语言说清时才补充伪代码。

main 从已批准的方案生成 worktree 内 `.gkd/execution.md`。执行 session 只读取该交接和适用的 `AGENTS.md`，按其中的具体文件、步骤和验证要求工作，并更新 `.gkd/progress.md`；`.gkd/plan.md` 是 main 的方案与授权记录，不是执行指令。

`.gkd/plan-changes.md` 由 main 追加记录计划调整的原因、依据、影响和 execution 更新。验收发现问题时，main 先在 `.gkd/review.md` 记录 finding，再更新方案、追加变更记录和新的 execution revision，然后启动下一轮；旧 session 不会因方案文件变化而隐式改向。

## 角色边界

- `gkd_execute`（Sol/xhigh，workspace-write）：只在声明 worktree 内按 `.gkd/execution.md` 实现、验证并更新 `.gkd/progress.md`；不验收、不交付、不启动其他代理。
- `gkd_ci_monitor`（Terra/high，read-only）：只调用复用的监控工具跟踪一个明确目标并报告，不修改代码或 GitHub。
- `gkd_accept`（Sol/xhigh，read-only）：独立检查计划、execution、diff、progress 和验证证据，向 main 提出通过或返工意见。

同一 worktree 的同一轮只安排一个写入型执行 session。执行中发现事实与方案不符时，执行 session 在 `.gkd/progress.md` 说明并暂停，交回 main 判断是否需要调整计划和 execution。

## 执行提示

```text
读取声明 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只在声明范围内完成 `.gkd/execution.md` 的任务，按其中的技术方案和验证命令工作。
把重要判断、里程碑、阻塞和实际验证结果写入 `.gkd/progress.md`；完成后停止并通知 main。
不要验收、合并、发布、清理 worktree 或启动其他施工代理。
```

自动启动只是由 main 替代用户打开普通执行 session，不是旧 automatic route。不得引入旧状态机、JSON 合同、固定 head 验收或常驻 watcher。
