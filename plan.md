# GKD 原生角色工作流补齐计划

## 状态

进行中。本文件是当前施工的唯一总计划。它只定义 GKD 本体如何补齐能力；本轮先完善计划和施工合同，不开始实现脚本、Skill 或生产安装。

## 目标与边界

GKD 的产品主旨是成为用户使用 Codex 修改项目的统一入口：用户提出需求，GKD 调查并补齐需求，写出实现就绪的 PLAN；用户确认后，GKD 调用合适的执行角色在 worktree 中施工，衔接 CI 监控和验收，最后按授权完成提交、发版或停在边界。CI 优化、项目适配和逐项问答都是服务这条主流程的附属能力。

在 Git、Markdown、Git worktree 和 Skills 这一简洁架构上，补齐：

1. main 入口先澄清需求，再根据需求选择直接处理、手动执行、明确自动执行、CI 监控、验收或项目适配路径。
2. 执行、CI 监控、验收使用预先配置的角色：执行和验收为 `gpt-5.6-sol / xhigh`，CI 监控为 `gpt-5.6-terra / high`。
3. 手动启动执行 session 是默认；只有用户明确选择自动执行时，main 才能用命名角色启动一个执行代理，并让其在指定 worktree 中修改。
4. GitHub 长流程由可复用的只读监控脚本处理，CI 监控代理不临时拼装轮询命令。
5. 提供需求问答、项目 GKD 适配和 CI 优化能力。
6. 不恢复旧的机器合同、状态机、断点恢复、watcher、固定 head 验收、bundle 安装器或自动发布平台。

提交、推送、合并、创建 release 和实际发布不因路由自动获得授权；它们必须在计划中明确列为允许动作，并由用户授权。

## 施工前 PLAN 硬性合同

任何 delegated 任务在创建 worktree 或启动执行角色前，main 必须先生成该任务自己的 `plan.md`。只有满足以下“实现就绪”检查，才能进入施工：

- 目标、成功标准、非目标和工作目录已确定；没有“后续再决定”的材料性事项。
- 已列出受影响的文件、目录、符号或配置键，并说明每项是新增、修改还是删除。
- 已写出现状证据（文件路径、符号名、必要时行号）以及目标行为；不能只写“补齐”“优化”“接入”。
- 已给出控制流/数据流和关键接口的伪代码，至少覆盖正常路径、权限拒绝、配置缺失、外部命令失败、超时和用户介入。
- 已明确每个角色、脚本和 Skill 的输入、输出、可写范围、禁止动作及停止条件。
- 已把用户可见行为、外部副作用和需要用户决定的事项单独列出，并标明授权时点。
- 已列出逐项验证命令、预期结果、不能运行的检查及原因；验证对象必须对应实际改动。
- 已定义交接材料如何更新：何时写 `progress.md`，完成时报告什么，阻塞时停止在哪里。
- 计划中的每条验收标准都能通过 diff、文件内容、命令结果或手工操作复现；不存在仅凭“看起来正确”的标准。

### 任务 PLAN 的固定结构

每个施工任务的 `plan.md` 必须按下列顺序写，不得省略章节；不适用时写明“不适用及原因”：

```text
1. 任务目标与用户可见结果
2. 范围、非目标、授权动作和停止条件
3. 现状证据（文件/符号/配置/调用关系）
4. 目标设计（组件、数据流、控制流）
5. 文件级变更表（新增/修改/删除、责任和原因）
6. 接口与配置（输入、输出、错误、兼容性）
7. 关键路径伪代码（正常、失败、超时、拒绝、恢复）
8. 角色协作与 worktree 写入边界
9. 验证矩阵（命令、夹具、预期结果、未验证项）
10. 交接格式与 progress.md 更新点
11. 风险、取舍和仍需用户确认的事项
```

伪代码要求达到“施工代理无需重新设计”的程度：变量和输入来源明确，分支条件可判断，调用的角色/脚本名称明确，错误结果和停止动作明确。伪代码不是实现代码，但不能用抽象句替代，例如“调用 CI 脚本”“处理异常”必须展开为目标解析、命令调用、终态分类和返回内容。

施工期间若发现必须改变目标行为、文件边界、角色职责、授权范围或伪代码主流程，执行代理必须停止修改，先在 `progress.md` 记录偏差；main 更新 `plan.md` 并重新取得用户确认后才能继续。纯内部实现细节可以由执行代理选择，但必须写入 `progress.md`。

## 目标工作流

```text
用户需求
  -> main 判断信息是否足够
  -> 不足：gkd-intake 逐项提问并更新计划草案
  -> 足够：展示实现就绪的 PLAN，等待用户批准
  -> 路由：direct-main / delegated-manual / delegated-automatic / project-adapt
  -> 执行角色在指定 worktree 修改并更新 progress.md
  -> 长 GitHub 流程：gkd_ci_monitor 调用复用脚本并报告终态
  -> gkd_accept 独立检查 diff、计划和 progress.md
  -> main 写 review.md，决定通过或返工
  -> 按 PLAN 中已获授权的交付动作提交、推送、合并或发版；未授权则停在交付前
```

默认路由是 `delegated-manual`。`delegated-automatic` 只有用户明确说出自动执行意图时可用，且只能调用 `gkd_execute`；角色不存在、配置不符或 spawn 失败时报告阻塞，不降级为默认 worker。

## 角色预设

角色文件位于项目 `.codex/agents/`，每个文件固定提示词、模型、推理强度、sandbox 和禁止嵌套边界。main 启动前必须读取并核对配置，启动后将 worktree 和任务 PLAN 作为唯一施工输入。

| 角色 | 模型 | sandbox | 责任 | 禁止 |
| --- | --- | --- | --- | --- |
| `gkd_execute` | `gpt-5.6-sol / xhigh` | `workspace-write` | 在声明 worktree 内按 PLAN 修改、验证、更新 progress | 扩大需求、验收、合并、发布、清理、启动子代理 |
| `gkd_ci_monitor` | `gpt-5.6-terra / high` | `read-only` | 调用复用脚本监控一个明确 GitHub 目标并报告终态 | 修改代码、临时拼命令、重跑/取消流程、合并、发布、验收 |
| `gkd_accept` | `gpt-5.6-sol / xhigh` | `read-only` | 独立检查 diff、PLAN、progress 和验证结果 | 修改实现、改写报告、合并、发布、启动子代理 |

## 分阶段施工任务

### T1：main 路由与角色启动

**目标**：实现需求分类、方案确认和手动/自动执行分流，不改变 Git/Markdown 事实源。

**文件范围**：

- 修改 `.agents/skills/gkd-main/SKILL.md`：增加路由判定、PLAN readiness gate、自动启动约束和偏差处理。
- 修改 `.codex/agents/gkd_execute.toml`、`gkd_ci_monitor.toml`、`gkd_accept.toml`：固化本计划中的模型和职责。
- 修改 `docs/manual-workflow.md`：同步用户手动和 main 自动路径。
- 不修改 `~/.codex` 生产安装，不新增运行时状态文件。

**实现伪代码**：

```text
handle_request(request):
  facts = inspect_request(request)
  if facts.missing_material_input:
    invoke gkd-intake
    return waiting_for_answers
  draft = build_plan(facts)
  require plan_readiness(draft) == ready
  present draft and await user approval
  if approval != implementation_authorized:
    return plan_approved_only
  route = explicit_auto_requested(request) ? delegated-automatic : delegated-manual
  if route == delegated-manual:
    create worktree and write task plan
    return handoff prompt
  role = load_named_agent("gkd_execute")
  require role.model == sol and role.effort == xhigh
  spawn exactly one role with fork_turns=none and declared worktree
  if spawn fails or role check fails:
    report blocked; preserve worktree; do not fallback
  otherwise remain within the waiting contract and await completion
```

**验收**：用四组输入分别复现信息不足、普通实施、明确自动实施和直接回答；确认自动路径只启动 `gkd_execute`，手动路径不启动子代理，PLAN 未 ready 时不能 spawn。

### T2：GitHub 长流程只读监控

**目标**：提供一个可复用、无状态、只读的脚本，供 CI 监控角色监控 PR、workflow run、commit 或 release。

**文件范围**：

- 新增 `scripts/gkd-github-watch` 及其最小测试/fixture。
- 修改 `.codex/agents/gkd_ci_monitor.toml` 和 `docs/manual-workflow.md` 的调用约束。
- 脚本只从参数和当前 Git remote 获取目标，不写死仓库、路径或 check 名称。

**实现伪代码**：

```text
watch(target, interval, deadline):
  identity = resolve_explicit_target(target)
  require identity.repo matches current remote when a worktree is supplied
  repeat until deadline:
    result = run gh/API with per-command timeout
    if auth_error or target_missing or unsupported_response:
      return blocked(reason, target, url)
    state = classify(result)  # queued, in_progress, success, failure, cancelled, timeout
    if state is terminal:
      return report(identity, state, failed_checks, url)
    sleep(interval)
  return report(identity, timeout, last_state, url)
```

**验收**：使用 fake GitHub 响应覆盖目标解析、运行中、成功、失败、认证失败、仓库不一致和超时；确认脚本没有写文件、重跑、取消或修改 GitHub 资源。

### T3：需求问答 Skill

**目标**：只在材料性信息不足时提问，并把答案整理进 PLAN，不机械制造确认轮次。

**文件范围**：新增 `.agents/skills/gkd-intake/SKILL.md` 和按需 reference；更新 `.agents/skills/gkd-main/SKILL.md` 的触发条件。

**实现伪代码**：

```text
intake(request, current_plan):
  missing = ordered_missing_facts(request, current_plan)
  if missing is empty:
    return ready
  ask one question for the first dependency-critical fact
  record answer in plan draft
  repeat only when the next missing fact changes scope, behavior, risk or authorization
  return ready when success criteria, non-goals, worktree and authorization are explicit
```

**验收**：模糊需求逐个提问；已有完整目标时零提问；用户只回答部分问题时保留未决项，不把默认值伪装成批准。

### T4：项目适配与 CI 优化 Skills

**目标**：让 GKD 能针对任意 GitHub 项目形成适配方案，而不是把 AIO 经验写死。

**文件范围**：

- 新增 `.agents/skills/gkd-project-adapt/SKILL.md`。
- 新增或恢复 `.agents/skills/gkd-optimize-ci/SKILL.md`。
- references 只记录通用原则；项目差异写入目标项目自己的 policy 或 PLAN，不写进全局 Skill。

**实现伪代码**：

```text
adapt(repo):
  inspect language, package manager, tests, CI workflows, release steps, runner and local constraints
  evidence = cite files, workflow jobs and recent run facts
  if evidence is insufficient:
    report gaps and ask only material questions
  choose presets from detected facts:
    resource_constrained_local -> local-light/cloud-heavy
    public_standard_runner -> speed-first, subject to artifact/cache limits
  produce current workflow, proposed workflow, file changes, risks, rollback and verification
  stop at user approval; do not edit repo

optimize_ci(repo):
  parse workflow structurally
  build job DAG and required-check map
  identify serial bottlenecks, fail-fast masking, duplicate builds, cache/artifact issues
  return prioritized recommendations and an implementation-ready PLAN
```

**验收**：用一个 Rust/Actions 项目和一个非 Rust 项目验证；确认不会引用 AIO 固定路径，能主动识别本机资源限制，并在信息不足时给出方向而不是猜测。

### T5：文档同步与端到端验收

**目标**：让规则、角色、计划粒度和用户操作在各文档中一致。

**文件范围**：`VISION.md` 仅在长期原则发生变化时更新；常规同步修改 `AGENTS.md`、`docs/manual-workflow.md`、模板 `docs/templates/manual/plan.md`、`.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md`、`progress.md`、`review.md`。

**验收顺序**：

1. 静态检查角色配置、文档交叉引用和 PLAN readiness 清单。
2. 手动执行路径演练：worktree、plan、progress、review。
3. 明确自动路径演练：只启动命名执行角色，验证 worktree 隔离和失败不降级。
4. CI 监控路径演练：脚本覆盖运行中、终态和错误。
5. 项目适配/需求问答路径演练：确认先问答/规划，批准前不修改目标项目。
6. 消融审查：删除没有调用方的旧描述、重复约束和不必要抽象。

## 统一停止条件

- PLAN 未达到实现就绪标准；
- 用户尚未批准材料性方案或实施动作；
- 角色配置缺失、模型/强度不符、sandbox 不符或 agent type 不可用；
- worktree 不明确、已被其他写入 session 占用或出现未解释的外部修改；
- 脚本目标无法唯一解析、认证失败或外部 API 返回未知结构；
- 实施发现需要扩大范围或改变用户可见行为。

## 非目标

- 不恢复旧 `gkd_task`、CAS、offer/claim、断点恢复、队列、watcher MCP、bundle/manifest/lock 安装系统或生产迁移工具。
- 不把监控脚本变成常驻服务。
- 不让 main 在自动模式下自行扩大需求或把普通 worker 当执行角色。
- 不把 CI reviewer 的只读职责扩展为修改、重跑、取消、合并或发布。

## 实施记录

- 2026-09-03：根据历史会话和当前需求建立初版计划与项目角色预设。
- 2026-09-03：按用户修订 CI reviewer 为 `gpt-5.6-terra / high`；新增 PLAN 实现就绪合同、固定章节、伪代码要求、偏差停工规则和 T1-T5 具体任务边界。
