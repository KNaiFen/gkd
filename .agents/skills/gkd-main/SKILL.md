---
name: gkd-main
description: 通过计划、Git worktree、进度报告和主代理审查协调 manual-first 编码任务，并可按用户明确选择以 agent_type=gkd_execute 启动执行 session。
---

# GKD Main

这是普通任务的主流程 Skill。它用 Git worktree 和 Markdown 记录协调工作，保留 main 的判断，不把协作材料变成机器状态机。

## 计划授权闸门

`plan-only` 是“拟一个 PLAN”“先出方案”“按这个方向整理 PLAN”等请求的唯一含义：main 可以调查、询问材料性事实、写或更新目标项目 `.gkd/plan.md`，但不得创建执行 worktree 或任务分支、写目标项目代码、启动 `agent_type=gkd_execute`/CI/验收代理、提交、推送、合并、创建 release、发布或清理现场。

main 必须展示实现就绪 PLAN，写清目标、成功标准、范围/非目标、技术方案、文件/符号、验证、角色边界、外部动作授权和风险，然后等待用户明确批准“按此 PLAN 开始执行”。只批准总体方向不等于批准后来新增的文件范围、数据库或接口变更、展示、发布或其他材料性动作；此类变化须追加 `.gkd/plan-changes.md` 并重新取得确认。授权不明确时继续停在 `plan-only`，不得从沉默或上下文推断执行许可。

## 路径选择

1. 简单、低风险且用户未指定子代理时，main 直接处理，使用 `direct-main`；用户明确要求子代理时，用户选择覆盖复杂度判断。
2. 需求缺少会改变目标、范围、验收、行为约束、工作目录或授权的材料性事实时，先使用 `gkd-intake` 逐项对齐；该 Skill 不可用则向用户说明缺口并继续沟通。
3. 项目工作流不合适、过慢或受本机限制时，先调用 `gkd-project-adapt` 调查技术栈、测试、CI、发布和资源约束；CI 瓶颈明确时可调用 `gkd-optimize-ci` 分析 workflow、job DAG、required checks、缓存和重复构建。两者只读并返回建议或实现就绪 PLAN，不能绕过用户确认和 main 审查。
4. 只有用户明确批准按 PLAN 开始执行后，才进入 delegated 路径。默认使用 `delegated/manual`：main 创建 sibling worktree，在目标项目 `.gkd/` 维护方案并生成 worktree 内的 `.gkd/execution.md`，然后交给用户手动启动。
5. 只有用户明确选择自动执行时才使用 `delegated/automatic`：main 读取 `.codex/agents/gkd_execute.toml`，通过原生 `spawn_agent` 以 `agent_type=gkd_execute` 和 `fork_turns=none` 启动一个执行 session。角色不可用或配置不符时报告阻塞并保留 worktree，不切换到其他角色或 `direct-main`。
6. 需要等待明确的 PR、workflow run、提交或 release CI 时，必须启动命名的 `gkd_ci_monitor` 只读子代理，并遵守 [CI 监控 Skill](../gkd-ci-monitor/SKILL.md) 的单目标、脚本入口和等待规则；main 不自行持续轮询。只有已批准的 delegated 执行 session 完成后，main 才可启动 `gkd_accept` 做独立验收；验收和 main 审查通过后，路由到 [收尾 Skill](../gkd-closeout/SKILL.md)；这些角色只读，提交、推送、合并和发版仍须按计划和用户授权执行。

## 计划和交接

main 维护目标项目 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`。开始施工前，方案应说明目标、成功标准、现状证据、技术栈或现有工具、实现思路、文件/符号范围、接口配置、验证方式、授权边界和仍需决定的事项。只有复杂分支、状态转换或外部命令编排难以用自然语言说清时才补充伪代码。

main 从已批准的方案生成 worktree 内 `.gkd/execution.md`。执行 session 只读取该交接和适用的 `AGENTS.md`，按其中的具体文件、步骤和验证要求工作，并更新 `.gkd/progress.md`；`.gkd/plan.md` 是 main 的方案与授权记录，不是执行指令。

`.gkd/plan-changes.md` 由 main 追加记录计划调整的原因、依据、影响和 execution 更新。验收发现问题时，main 先在 `.gkd/review.md` 记录 finding，再更新方案、追加变更记录和新的 execution revision，然后启动下一轮；旧 session 不会因方案文件变化而隐式改向。

## 归档与长期记录

一轮 delegated 施工只有在已批准的执行 session 完成、`gkd_accept` 独立验收通过且 main 审查通过后，才可进入 [收尾 Skill](../gkd-closeout/SKILL.md)；成功路径必须创建并检查最终 `.gkd/archive/<task-id>/<date>-<revision>/`。若用户决定停止、保留当前成果或明确阻塞，也可以创建临时归档，但 `summary.md` 必须明确标为未验收或阻塞中的临时记录，不能宣称任务已完成。归档来源和脱敏规则由收尾 Skill 维护。

归档只保存脱敏后的 Markdown 事实：保留逻辑 worktree、分支和变更标识，移除本机绝对路径、令牌、账号、机密值和运行时状态。归档目录是长期可读记录，不是活动事实源、索引服务或状态机制，也不会因为归档自动提交、推送、合并或发布。简单 `direct-main` 任务只有在确实产生值得后续复用的项目知识时才归档；是否随目标项目提交仍由 PLAN 和用户授权决定。

## 角色边界

- `agent_type=gkd_execute`（`gpt-6-astra`/xhigh，workspace-write）：只在声明 worktree 内按 `.gkd/execution.md` 实现、验证并更新 `.gkd/progress.md`；不验收、不交付、不启动其他代理。
- `gkd_ci_monitor`（`gpt-5.6-terra`/medium，read-only）：只调用复用的监控工具跟踪一个明确目标并报告，不修改代码或 GitHub。
- `gkd_accept`（`gpt-6-astra`/xhigh，read-only）：仅在已批准的 delegated 执行 session 完成后，独立检查计划、execution、diff、progress 和验证证据，向 main 提出通过或返工意见。
- `gkd-legacy-cleanup`：临时、按需能力；只在 main 明确指定老项目和逐项授权后盘点/清理旧 GKD 活动机制，不进入默认路由，不触碰普通业务、历史归档或生产用户目录。

## 收尾路由

delegated 任务在 `gkd_accept` 通过且 main 写下通过审查后，加载 [收尾 Skill](../gkd-closeout/SKILL.md) 执行归档、授权清理和详细报告；direct-main 在 main 审查后按同一 Skill 的 direct-main 模式执行。main 保留最终通过、阻塞和是否宣称成功的决定权。

CI 监控代理返回成功、失败、超时、调用错误或目标漂移后立即停止，并把终态交给 main；失败后的修复须重新规划并取得必要授权。

## 审查 revision

`.gkd/review.md` 顶部只保留一个当前审查块，写明 PLAN revision、execution revision、被审查的 Git head 和当前状态（通过、返工或阻塞）。需要保留历史审查时，在旧审查块标题下只增加一行“状态：已被 rN 取代（superseded）”，不删除原文、不为每条 finding 增加额外状态字段；普通排版修正不创建新 revision。

同一 worktree 的同一轮只安排一个写入型执行 session。执行中发现事实与方案不符时，执行 session 在 `.gkd/progress.md` 说明并暂停，交回 main 判断是否需要调整计划和 execution。

项目适配和 CI 优化属于施工前的调查能力；它们的建议必须回到 `.gkd/plan.md`，不能直接编辑目标项目或替代 `gkd-intake`、执行、监控和验收角色。

## 执行提示

```text
读取声明 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只在声明范围内完成 `.gkd/execution.md` 的任务，按其中的技术方案和验证命令工作。
把重要判断、里程碑、阻塞和实际验证结果写入 `.gkd/progress.md`；完成后停止并通知 main。
不要验收、合并、发布、清理 worktree 或启动其他施工代理。
```

自动启动只是由 main 替代用户打开普通执行 session，不是旧 automatic route。不得引入旧状态机、JSON 合同、固定 head 验收或常驻 watcher。
