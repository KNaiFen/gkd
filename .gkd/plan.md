# GKD 原生角色工作流补齐计划

## 状态

已完成。本文件是本轮施工的总计划，由 main 维护和审查，位于项目 `.gkd/` 目录。每个 delegated 任务在目标 worktree 的 `.gkd/` 中维护 `execution.md` 和 `progress.md`，并用 `plan-changes.md`、`review.md` 记录方案演进与验收。

## 目标与边界

GKD 的产品主旨是把复杂项目开发组织成完整工作流：调查并澄清需求，形成实现就绪的 PLAN，经用户确认后在独立 worktree 中执行，持续跟踪 CI，独立验收，最后按授权完成提交、合并或发版。CI 优化、项目适配和逐项问答都是服务这条主流程的附属能力。

在 Git、Markdown、Git worktree 和 Skills 这一简洁架构上，补齐：

1. main 入口先澄清需求，再根据需求选择直接处理、手动执行、明确自动执行、CI 监控、验收或项目适配路径。
2. 执行、CI 监控、验收使用预先配置的角色：执行和验收为 `gpt-5.6-sol / xhigh`，CI 监控为 `gpt-5.6-terra / high`。
3. 手动启动执行 session 是默认；只有用户明确选择自动执行时，main 才能用命名角色启动一个执行代理，并让其在指定 worktree 中修改。
4. GitHub 长流程由可复用的只读监控脚本处理，CI 监控代理不临时拼装轮询命令。
5. 提供需求问答、项目 GKD 适配和 CI 优化能力。
6. 每轮施工完成后，把该项目的关键 Markdown 记录和简短摘要归档到项目自己的 `.gkd/archive/` 子目录，保留可读的长期上下文。
7. 不恢复旧的机器合同、状态机、断点恢复、watcher、固定 head 验收、bundle 安装器或自动发布平台。

提交、推送、合并、创建 release 和实际发布不因路由自动获得授权；它们必须在计划中明确列为允许动作，并由用户授权。

## 施工前 PLAN 编写要求

任何 delegated 任务在创建 worktree 或启动执行角色前，main 都应先写一份足够具体的 `plan.md`。它是给 main 自己和用户审阅的方案，不是机器门禁。计划至少应让读者知道：

- 要解决什么问题、成功后看到什么，以及哪些内容明确不做；
- 现状证据在哪里，准备采用什么技术栈或现有工具，需求如何落地，关键步骤如何衔接；
- 会改哪些文件、符号或配置，输入输出如何组织，如何验证结果；
- 哪些动作需要用户授权，执行、CI 监控和验收角色各自负责什么；
- 还有哪些真正需要用户决定的事项。

只有复杂分支、状态转换或外部命令编排难以用自然语言说清时，才补充针对性伪代码。计划可以根据新事实和验收意见随时调整，调整理由追加到 `plan-changes.md`，不把文档变成固定状态机。

### 计划与执行文档分工

- `.gkd/plan.md`：main 的权威方案和授权记录。它描述为什么做、如何实现、用什么技术、改哪些文件、如何验证，以及用户确认和后续审查依据；执行 session 不以它作为施工指令。
- `.gkd/execution.md`：main 根据已批准 PLAN 生成的 worktree 内执行交接。它只包含当前轮次可执行的文件/符号清单、实现步骤、命令、约束和变更建议，并标明对应 PLAN 修订号；执行 session 读取它和适用的 `AGENTS.md`，完成后更新 `.gkd/progress.md`。
- `.gkd/plan-changes.md`：main 维护的追加式变更记录。每次 PLAN 因用户决定、验收发现或事实变化而调整，都记录原因、影响、授权变化、PLAN 修订号和 `execution.md` 更新内容；不得覆盖旧思路。
- `.gkd/review.md`：main 记录独立验收结论。验收发现问题时，main 先写 review，再修改 PLAN，追加 `plan-changes.md`，更新 worktree 的 `execution.md`，然后才启动下一轮执行；旧 execution session 不会因 PLAN 修改而隐式改变。

### 任务 PLAN 的建议结构

为了让施工前的实现思路足够清楚，建议按下列顺序组织 `plan.md`；可根据任务删减不相关章节：

```text
1. 任务目标与用户可见结果
2. 范围、非目标、授权动作和停止条件
3. 现状证据（文件/符号/配置/调用关系）
4. 目标设计（组件、数据流、控制流）
5. 文件级变更表（新增/修改/删除、责任和原因）
6. 接口与配置（输入、输出、错误、兼容性）
7. 实现方案与关键路径伪代码（技术栈、实现步骤；仅对需要精确分支/编排的部分）
8. 角色协作与 worktree 写入边界
9. 验证矩阵（命令、夹具、预期结果、未验证项）
10. 交接格式与 progress.md 更新点
11. 风险、取舍和仍需用户确认的事项
```

实现方案要达到施工代理无需重新设计的程度：说明需求如何落地、使用什么技术或现有工具、改动哪些文件/符号、关键步骤和验证方式。伪代码不是实现方案本身，只用于表达非显然分支、状态转换或外部命令编排；变量、调用对象和停止动作在确有需要时写清。施工期间若发现目标、范围或授权需要变化，执行代理在 `progress.md` 说明事实，main 结合判断更新 `plan.md` 和 `execution.md`；只有会改变用户意图或造成明显冲突时才暂停并重新对齐。

## 目标工作流

```text
用户需求
  -> main 判断信息是否足够
  -> 不足：gkd-intake 逐项提问并更新计划草案
  -> 足够：展示实现就绪的 PLAN，等待用户批准
  -> 路由：direct-main / delegated-manual / delegated-automatic / project-adapt
  -> delegated 路径：main 生成 worktree/execution.md，执行角色只读 execution.md 并更新 progress.md
  -> 长 GitHub 流程：gkd_ci_monitor 调用复用脚本并报告终态
  -> gkd_accept 独立检查 diff、计划和 progress.md
  -> main 写 review.md，决定通过或返工
  -> 按 PLAN 中已获授权的交付动作提交、推送、合并或发版；未授权则停在交付前
  -> 施工结束：main 将本轮记录摘要归档到目标项目 `.gkd/archive/<task>/`
```

默认路由是 `delegated-manual`。简单、低风险且无需执行 session 的任务使用 `direct-main`；如果用户明确要求使用子代理，即使任务本身简单，也按用户指定的 delegated 路径执行。`delegated-automatic` 只有用户明确说出自动执行意图时可用，且只能调用 `gkd_execute`；角色不存在、配置不符或 spawn 失败时报告阻塞，不降级为默认 worker。

## 角色预设

角色文件位于项目 `.codex/agents/`，每个文件固定提示词、模型、推理强度、sandbox 和禁止嵌套边界。main 启动前必须读取并核对配置，启动后将 worktree 和任务 PLAN 作为唯一施工输入。

| 角色 | 模型 | sandbox | 责任 | 禁止 |
| --- | --- | --- | --- | --- |
| `gkd_execute` | `gpt-5.6-sol / xhigh` | `workspace-write` | 在声明 worktree 内按 PLAN 修改、验证、更新 progress | 扩大需求、验收、合并、发布、清理、启动子代理 |
| `gkd_ci_monitor` | `gpt-5.6-terra / high` | `read-only` | 调用复用脚本监控一个明确 GitHub 目标并报告终态 | 修改代码、临时拼命令、重跑/取消流程、合并、发布、验收 |
| `gkd_accept` | `gpt-5.6-sol / xhigh` | `read-only` | 独立检查 diff、PLAN、progress 和验证结果 | 修改实现、改写报告、合并、发布、启动子代理 |

## 分阶段施工任务

### T1：main 路由与角色启动

**目标**：实现需求分类、方案确认和手动/自动执行分流，不改变 Git/Markdown 事实源；让执行 session 通过独立 `execution.md` 获得施工指令。

**文件范围**：

- 修改 `.agents/skills/gkd-main/SKILL.md`：增加路由判定、计划与执行文档交接、自动启动约束和灵活偏差处理。
- 修改 `.codex/agents/gkd_execute.toml`、`gkd_accept.toml`：将角色提示词同步到 `.gkd/` 交接；核对 `gkd_ci_monitor.toml` 保持 Terra/high。
- 修改 `docs/manual-workflow.md`：同步用户手动和 main 自动路径。
- 修改 `docs/templates/manual/plan.md`、`execution.md`、`plan-changes.md`、`archive-summary.md` 模板：明确 main 计划、执行交接、变更追溯和归档摘要的分工。
- 修改 `.agents/open-items.md` 和 `.gkd/progress.md`：同步本轮路由、角色和交接事实。
- `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md` 由 main 维护；执行代理不修改它们。main 因验收修订这些记录时，必须在 `plan-changes.md` 追加原因并同步 execution revision。
- 不修改 `~/.codex` 生产安装，不新增运行时状态文件。

**实现方案与技术栈**：

- 技术栈：Markdown 规范、Git worktree、项目 `.codex/agents/*.toml` 角色预设和 Codex 原生 agents API；不新增运行时状态机或机器合同。
- main 在确认 PLAN 后生成 `execution.md`，内容来自 PLAN 的已批准实现步骤；执行角色提示词改为只读取 `execution.md` 和适用规则。main 的 `plan-changes.md` 采用追加式 Markdown 表格/条目，记录 revision、原因、影响和 execution 更新。
- 验收返工时，`review.md` 先记录 finding，main 增加 PLAN revision 并同步 execution 文档；下一轮 session 只按最新 execution 文档施工，从而隔离 PLAN 调整与旧 session。

**关键路由控制流伪代码**（仅描述需要精确分支的部分）：

```text
handle_request(request):
  facts = inspect_request(request)
  if facts.missing_material_input:
    invoke gkd-intake
    return waiting_for_answers
  draft = build_plan(facts)  # 包含技术栈、文件/符号、实现步骤和验证方案
  if plan_missing_material_implementation_detail(draft):
    clarify_with_user_or_investigate(draft)
  present draft and await user approval
  if approval != implementation_authorized:
    return plan_approved_only
  route = explicit_auto_requested(request) ? delegated-automatic : delegated-manual
  if route == delegated-manual:
    create worktree and write execution.md from approved draft
    return handoff prompt
  role = load_named_agent("gkd_execute")
  if role.model != sol or role.effort != xhigh:
    explain_role_mismatch_and_wait_for_main_decision()
  spawn exactly one role with fork_turns=none and declared worktree/execution.md
  if spawn fails or role check fails:
    report blocked; preserve worktree; do not fallback
  otherwise remain within the waiting contract and await completion
```

**验收**：简单直接回答不启动子代理；用户明确要求子代理时即使任务简单也遵循指定 delegated 路径；另用信息不足、普通实施、明确自动实施复现路由；确认执行角色读取 `.gkd/execution.md` 而非把 `.gkd/plan.md` 当施工指令，计划缺少关键实现信息时 main 会先补充或与用户对齐。静态验证至少运行 `git diff --check`、路由/路径关键词 `rg`、旧门禁关键词 `rg`（含 `.codex/agents/*.toml`）和 `codex --strict-config --version`，逐项记录实际结果。

### T2：GitHub 长流程只读监控

**目标**：提供一个可复用、无状态、只读的脚本，供 CI 监控角色监控 PR、workflow run、commit 或 release。

**文件范围**：

- 新增可执行入口 `scripts/gkd-github-watch`，实现目标解析、只读查询、轮询和终态报告。
- 新增 `scripts/tests/test_gkd_github_watch.py` 及 fake `gh` fixture，覆盖正常、错误和超时。
- 修改 `.codex/agents/gkd_ci_monitor.toml` 和 `docs/manual-workflow.md` 的调用约束，明确只调用该入口。
- 脚本只从参数和当前 Git remote 获取目标，不写死仓库、路径或 check 名称，不写本地状态文件。

**实现方案与技术栈**：

- Python 3 标准库（`argparse`、`json`、`subprocess`、`time`、`urllib.parse`）；外部依赖只使用 GitHub 官方 `gh` CLI 的只读 `api` 子命令。
- 目标参数采用显式形式：`--pr <number>`、`--run <id>`、`--commit <sha>` 或 `--release <tag>`，可选 `--repo owner/name`、`--interval seconds`、`--timeout seconds`；未指定 repo 时从 `git remote get-url origin` 解析，显式 repo 在无 origin 的环境也可独立使用。
- 查询层把 GitHub JSON 正规化为统一报告字段：目标类型、仓库、编号/标识、URL、当前状态、失败检查摘要、查询时间；未知 JSON、认证失败和仓库不一致都直接形成可读错误报告。
- 轮询只在进程内保留最近一次结果，不落盘、不重跑、不取消、不修改 GitHub；interval/timeout 必须为有限非负数，单次 API 调用 timeout 不超过全局剩余时间。脚本退出码区分成功终态、失败终态、超时和调用错误，供 CI 监控角色报告。

**关键外部命令编排伪代码**：

```text
watch(args):
  identity = resolve_target(args, git_remote_origin() if args.repo is empty else None)
  while elapsed < args.timeout:
    remaining = args.timeout - elapsed
    payload = run_gh_api(identity, command_timeout=min(max(remaining, 0.1), 30))
    if command_failed(payload):
      return report_error(auth_or_target_reason(payload), identity)
    state = normalize_state(payload)
    if state in {success, failure, cancelled}:
      return report(identity, state, failed_checks(payload), url(payload))
    sleep(args.interval)
  return report(identity, timeout, last_state, last_url)
```

**验收**：使用 fake `gh` 响应覆盖四种目标解析、运行中、成功、失败、认证失败、目标不存在、仓库不一致和超时；用临时目录快照确认脚本没有写文件；检查命令参数只包含只读 `gh api`，没有重跑、取消或修改 GitHub 资源。

### T3：需求问答 Skill

**目标**：只在材料性信息不足时提问，并把答案整理进 PLAN，不机械制造确认轮次。

**文件范围**：新增 `.agents/skills/gkd-intake/SKILL.md` 和按需 reference；更新 `.agents/skills/gkd-main/SKILL.md` 的触发条件。

**技术栈与实现思路**：使用 Markdown Skill 指令和 main 的自然语言上下文，不新增问答数据库或状态文件。Skill 先从用户请求和已有 `.gkd/plan.md` 中整理目标、范围、验收、约束、工作目录和授权六类信息，只对会改变实现选择的首个缺口提一个问题；用户回答后将事实写回计划草案，继续判断是否还有材料性缺口。完整请求直接返回“无需问答”，不制造确认轮次。

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

**技术栈与实现思路**：两个 Skill 都使用 Markdown 指令、Git/CI 文件阅读和自然语言报告，不直接修改目标项目。`gkd-project-adapt` 先识别语言、包管理器、测试命令、workflow、发布步骤和本机限制，再输出适配建议；`gkd-optimize-ci` 结构化阅读 Actions YAML，整理 job DAG、required checks、缓存和重复构建，输出排序后的优化方案。只有用户确认后，main 才把建议转成目标项目的 PLAN。

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

**技术栈与实现思路**：以 Markdown 交叉引用、角色 TOML 静态读取、脚本单元测试和手工流程演练完成收口，不新增运行时组件。main 对照 VISION、AGENTS、README、manual workflow、模板和 Skills，清理旧根路径/门禁表述；再用 Git worktree 与 `.gkd/` 示例记录一轮从计划到验收的交接，最后将结果归档到 `.gkd/archive/`（如该示例项目授权归档）。

**文件范围**：`VISION.md` 仅在长期原则发生变化时更新；常规同步修改 `AGENTS.md`、`docs/manual-workflow.md`、模板 `docs/templates/manual/plan.md`、`.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md`、`progress.md`、`review.md`。

**验收顺序**：

1. 静态检查角色配置、文档交叉引用和计划/执行文档分工。
2. 手动执行路径演练：worktree、plan、progress、review。
3. 明确自动路径演练：只启动命名执行角色，验证 worktree 隔离和失败不降级。
4. CI 监控路径演练：脚本覆盖运行中、终态和错误。
5. 项目适配/需求问答路径演练：确认先问答/规划，批准前不修改目标项目。
6. 消融审查：删除没有调用方的旧描述、重复约束和不必要抽象。

### T6：项目级施工记录归档

**目标**：每轮施工结束后，让目标项目保留“做过什么、为什么做、结果如何”的可读记录，便于后续 GKD 或人工继续工作。

**技术栈与实现思路**：只使用目标项目内的 Git 和 Markdown。执行 session 负责在 worktree 准备规则文档和可供检查的归档材料；main 在独立验收结论确定后，才在目标项目主工作树按任务逻辑 ID 创建 `.gkd/archive/<task-id>/<date>-<short-revision>/`，从执行 worktree 和 main 的活动记录复制或整理 `plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md` 及一份包含最终验收结论的 `summary.md`。归档内容只保留逻辑 worktree、分支和变更摘要，不写入本机绝对路径、令牌或机器状态。目录命名和内容由 main 依据项目约定灵活选择，不新增常驻服务或索引数据库。

**触发与边界**：正常完成时在 main 的独立验收结论确定后创建最终归档；用户决定停止或明确阻塞时，main 写下当前审查结论后也可以归档一次，但摘要必须标注“未验收”或“阻塞中”，不得伪装成完成记录。简单 `direct-main` 任务只有在确实产生值得保留的项目知识时才归档。归档属于目标项目的普通文档改动，是否随功能提交由 PLAN 和用户授权决定；未授权时 main 只生成归档内容并停在交付前。

**验收**：在一个示例项目中完成一轮 delegated 任务并由 main 写下独立验收结论后，确认 `.gkd/archive/` 下的最终快照能独立读懂目标、思路、实际变更、验收结论和后续建议；归档快照不得在验收前宣称最终完成；重复归档不会覆盖旧目录；内容无绝对机器路径和敏感值；没有额外状态文件或后台进程。

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
- 2026-09-03：按用户修订 CI reviewer 为 `gpt-5.6-terra / high`；补充 PLAN 的实现思路要求、execution 交接、计划变更记录和项目级归档，并移除机器化门禁/状态机倾向。
- 2026-09-03：T1-T6 完成施工、独立验收和主分支收口；首轮材料保留在 `.gkd/archive/t6-archive/2026-09-03-19e7514/`，最终归档快照写入 `.gkd/archive/t6-archive/2026-09-03-r9-final/`。

## 后续修订草案 r10（2026-09-04）

### 状态与本轮边界

本节是针对 session `01a0689d-d152-7f60-a4a6-a23fddf1fbc0` 暴露问题的修订草案。状态为“待用户继续讨论和确认”，本节只授权规划和文档设计，不授权修改目标项目、不创建施工 worktree、不启动执行/CI/验收代理、不提交、不推送、不合并、不发版。

本轮只处理以下四个流程问题：

1. 为 CI、Actions 和发布等待建立单独的约束 Skill，明确监控脚本、只读 CI 子代理、单目标、等待时长、超时和失败处理。
2. 把“只拟 PLAN”和“批准 PLAN 并开始执行”分成两个不可混淆的授权状态，限制主代理在前一状态下的行为。
3. 增加一次性、面向老项目的旧版 GKD Skill 清理 Skill；它不进入默认主流程，完成清理后可按用户指示删除。
4. 补齐任务收尾：主代理主动向用户输出详细报告，归档后清理 worktree/分支，并将可信主 checkout 恢复为干净的 `main`。

### 现状证据

- 当前主流程已经要求“展示 PLAN 并等待用户确认”，但 session 实际在用户授权技术方向后自行更新计划并开始施工，未形成独立确认节点；当前规则依据为 `README.md`、`VISION.md` 和 `.agents/skills/gkd-main/SKILL.md`。
- 当前已有 `.codex/agents/gkd_ci_monitor.toml` 和 `scripts/gkd-github-watch`，但缺少一份专门 Skill 统一约束“必须由何种子代理调用、只能调用哪个脚本、脚本缺失时如何停止、主代理如何等待”。
- 当前 `docs/templates/manual/archive-summary.md` 面向长期归档，不足以替代任务完成时给用户看的实现报告。
- 目标项目实战中出现了项目内旧版 `.agents/skills/gkd-main` 与当前用户级 GKD 规则并存的情况；本轮不设计兼容模式，目标是提供一次性清理工具。
- 当前已有归档、worktree 和角色边界说明，但没有把“归档后删除 worktree/分支、恢复干净 main、失败时保留现场”的收尾顺序写成强约束。

### 目标与可观察成功标准

#### A. CI 监控约束

- 任何需要等待的 PR、workflow run、commit 或 release CI，在 PLAN 已授权 CI 跟踪且目标明确后，必须启动命名的 `gkd_ci_monitor` 只读子代理；主代理不得自行承担持续轮询。
- 每次监控只接受一个明确目标（`--pr`、`--run`、`--commit` 或 `--release`），并固定仓库和目标标识；PR、主线候选和正式 release 是不同目标，必须分别记录和分别监控。
- `gkd_ci_monitor` 只能调用目标项目提供的 `scripts/gkd-github-watch`，不得调用 `gh pr checks --watch`、`gh run watch` 或临时拼装轮询。脚本缺失、目标无法唯一解析或认证不可用时，立即报告阻塞，不得静默降级。
- 标准脚本参数为 `--interval 30 --timeout 3600`；经 PLAN 明确批准可以改变 timeout，但主代理的等待时长必须与该目标一致，不得无限等待或短轮询。
- 主代理等待监控代理时使用一次 `wait_agent(timeout_ms=3600000)`；等待期间不读取仓库/CI、不补充分析、不重复启动监控。代理返回成功、失败、超时、错误或目标漂移时立即停止并向用户报告。
- 监控代理不得修改代码、重跑/取消 workflow、编辑 PR、合并、发布、验收或启动其他代理。CI 失败后的修复由 main 根据报告重新规划并重新取得必要授权。

成功标准：静态检查能证明角色配置、CI Skill、手工流程和模板使用同一入口；手工演练能证明监控阶段实际由 `gkd_ci_monitor` 调用脚本并按固定等待/终态规则结束；没有直接 `gh ... --watch` 的流程性替代路径。

#### B. PLAN 确认与执行闸门

- “拟一个 PLAN”“先出方案”“按这个方向整理 PLAN”只进入 `plan-only` 状态，表示允许调查和写 PLAN，不表示允许施工。
- `plan-only` 状态禁止：创建执行 worktree 或任务分支、写目标项目代码、启动 `gkd_execute`/CI/验收代理、提交、推送、合并、创建 release、发布或清理现场。
- main 必须展示实现就绪 PLAN，明确目标、范围、非目标、技术方案、文件/符号、验证、角色边界、外部动作授权和风险，并等待用户明确批准“按此 PLAN 开始执行”。
- 用户只批准总体方向时，仍不能视为批准后来新增的文件范围、数据库/接口变更、桌面展示、发布或其他材料性动作；这些变化必须追加 `plan-changes.md` 并重新取得确认。
- 只有在确认后，main 才能按 `delegated/manual` 或用户明确选择的 `delegated/automatic` 创建 worktree 和生成 `execution.md`。确认不明确时继续停在 `plan-only`，不得按沉默或上下文推断批准。

成功标准：增加一个“只拟 PLAN”演练和一个“批准 PLAN 后执行”演练；前者无 worktree/代理/代码写入，后者才进入既定 delegated 路径。

#### C. 临时旧版 GKD Skill 清理

- 新增临时 `.agents/skills/gkd-legacy-cleanup/SKILL.md`，仅当 main 明确指定一个老项目根目录和清理任务时使用；不加入默认路由，不替代 `gkd-main`，不触碰生产 `~/.codex` 或当前 GKD 仓库自身的活动记录。
- Skill 第一阶段只读盘点目标项目内的旧 GKD 相关内容：项目 `.agents/skills`、`.codex/agents`、脚本、文档、模板、hooks、配置、CI 引用、任务状态/合同/队列/日志/receipt/offer/claim/activation/journal、旧 automatic route、fixed-head、watcher、bundle/manifest/lock 等标记，以及指向这些内容的 README/AGENTS/配置引用。
- 盘点结果按“当前有效规则、明确遗留、普通业务内容、证据不足”分类，逐项给出路径和引用；不以关键词命中为由直接删除业务代码或历史事实记录。
- 第二阶段只删除目标项目内已确认的旧 GKD 可执行入口、角色/Skill、状态文件、脚本和引用，并同步清理空目录与失效文档链接；不建立兼容模式、不迁移旧状态机、不恢复被删除入口。
- `.gkd/archive/` 中的历史 Markdown 默认作为事实记录保留；若其中包含可执行入口或用户明确要求彻底删除，才纳入清理范围，并在报告中区分“已删除的活动机制”和“保留的历史记录”。
- 清理完成后执行文件存在性检查、引用扫描、`git diff --check` 和必要的目标项目规则检查；仍有歧义的项目必须报告并停止，不静默扩大删除范围。
- 该 Skill 标记为临时能力；本轮只设计和加入它，后续由用户单独授权删除 Skill 及其文档引用。

成功标准：对老项目执行一次盘点后，所有活动旧 GKD Skill/入口/引用都有明确处理结果；目标项目不再有可执行的旧 GKD 路由或状态机制；清理报告列出保留的历史记录和未决证据缺口。

#### D. 收尾、报告与环境恢复

- main 在独立验收通过、计划中授权的交付动作完成后，必须主动向用户发送详细收尾报告，不能只说“完成”或只给提交号。
- 报告至少包含：任务目标和成功标准、实际修改的文件/符号、实现行为和数据流、与 PLAN 的一致/偏差及偏差原因和授权、验证命令与结果、CI/PR/release 结果、未验证风险、提交/合并/发布标识、归档位置、worktree/分支清理结果和后续建议。
- 同一份报告的脱敏摘要写入归档 `summary.md`；面向用户的报告保留足够细节，但不得包含完整对话、全量日志、令牌、账号、本机绝对路径或其他敏感值。
- 收尾顺序固定为：main 独立验收并写 `review.md` -> 创建并检查脱敏归档 -> 确认归档完整且本轮活动记录只属于当前任务 -> 删除目标项目中本轮已归档的活动 `plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`（保留 `.gkd/archive/`）-> 确认执行代理已停止且 worktree 无未提交改动 -> 删除已合并的本地任务 worktree 和本地任务分支 -> 按授权处理远端任务分支 -> 将可信主 checkout 切回 `main` 并确认 `git status --short` 为空且跟踪关系清晰 -> 输出详细报告。
- 如果活动记录与其他仍进行中的任务共用文件，必须先拆分或报告，不能按本轮完成直接删除；不能把删除归档前的唯一事实源当作清理动作。
- 如果任务被拒绝、阻塞、存在未提交改动或删除条件不满足，保留 worktree/分支和现场，报告“未完成/阻塞”，不得强行清理或宣称恢复成功。

成功标准：完成演练后目标项目只有可独立阅读的本轮归档而没有本轮活动 PLAN 文件残留，用户收到详细报告，任务 worktree/本地分支不存在，可信主 checkout 为干净 `main`；异常路径能保留现场并明确说明原因。

#### E. 审查记录的最小版本标识

- `review.md` 顶部必须只有一个当前审查块，写明 `PLAN revision`、`execution revision`、被审查的 Git head 和当前状态（通过、返工或阻塞）。该块是活动文件的唯一当前结论。
- 需要保留历史审查时，在旧审查块标题下只增加一行“状态：已被 rN 取代（superseded）”，不删除原文、不重新解释旧结论，也不为每条 finding 增加额外状态字段。
- 新一轮审查只做两步：把上一轮活动结论标记为 superseded，再在文件顶部追加当前审查块。普通错别字或不改变结论的排版修正不创建新 revision。
- 归档和 Git 历史负责保存完整旧版本；`review.md` 不引入 JSON、锁、状态机或额外历史数据库。若活动文件只保留当前审查，则不需要伪造 superseded 段落。

示例：

```markdown
## 当前审查（PLAN r10 / execution r10 / head abc1234）
状态：通过

## 历史审查（PLAN r9 / execution r9 / head def5678）
状态：已被 r10 取代（superseded）
```

成功标准：任何新 session 只看 `review.md` 顶部即可识别当前 revision 和结论；保留的旧结论均有明确 superseded 标记，且没有新增机器状态或重复文档操作。

### 计划范围与文件级变更表

| Action | File / symbol | Change | Reason |
| --- | --- | --- | --- |
| modify | `.agents/skills/gkd-main/SKILL.md` | 增加 `plan-only` 与“批准后执行”的明确分界、材料性 PLAN 变更重新确认、CI 监控角色调用和收尾顺序 | 防止主代理把拟 PLAN 误当施工授权 |
| add | `.agents/skills/gkd-ci-monitor/SKILL.md` | 建立 CI 专用约束 Skill：单目标、脚本入口、子代理边界、默认 interval/timeout、主代理等待、终态和阻塞处理 | 让 CI 行为有唯一规范来源 |
| modify | `.codex/agents/gkd_ci_monitor.toml` | 与 CI Skill 对齐提示词、脚本参数和失败/超时停止规则 | 确保命名角色实际执行约束 |
| add | `.agents/skills/gkd-legacy-cleanup/SKILL.md` | 提供老项目旧版 GKD 机制的盘点、分类、清理和验证流程，标记为临时能力 | 清理历史项目残留，且不引入兼容模式 |
| modify | `docs/manual-workflow.md` | 同步计划确认、CI 监控子代理、固定等待和收尾报告/清理顺序 | 让用户手动流程与 Skills 一致 |
| modify | `README.md`、`AGENTS.md` | 明确 plan-only 不授权执行、CI 监控入口和完成后恢复干净 main | 对用户和目标项目提供可见边界 |
| modify | `docs/templates/manual/plan.md`、`archive-summary.md` | 增加授权状态、CI 目标/等待、偏差和清理结果字段 | 让记录能支撑执行与复盘 |
| add | `docs/templates/manual/closeout-report.md` | 提供面向用户的详细收尾报告模板 | 保证完成后主动交付可审查信息 |
| modify | `.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md` | 记录 CI 监控约束、PLAN 授权闸门、临时清理 Skill 和收尾恢复规则 | 本轮会改变 GKD 流程、授权和交接边界 |
| modify | `.gkd/plan-changes.md`、`.gkd/review.md` | 记录本 revision 的来源、用户决定和后续验收结论；审查文件采用当前 revision 块和旧结论 superseded 标记 | 保留方案演进，避免历史审查被误读为当前事实 |

### 角色与写入边界

- `main`：调查、维护 PLAN/plan-changes/review、获取用户确认、创建/删除 worktree、启动命名角色、审查、归档、合并和最终报告；不得在 plan-only 状态执行施工或 CI 持续轮询。
- `gkd_execute`：仅在确认后的声明 worktree 内读取 `execution.md`、修改计划范围并更新 `progress.md`；不验收、不交付、不发布、不清理。
- `gkd_ci_monitor`：只读，只跟踪一个明确目标，只调用 `scripts/gkd-github-watch`，按批准的 interval/timeout 返回一次终态；不修改任何本地或 GitHub 内容。
- `gkd_accept`：只读，独立检查 diff、PLAN、execution、progress 和验证证据；不改报告、不合并、不发布。
- `gkd-legacy-cleanup`：只在明确目标项目和清理范围内工作；盘点结果先报告，删除动作须受本 PLAN/用户授权约束；不触碰生产用户级目录和无关业务文件。

### 关键流程伪代码

```text
handle_request(request):
  draft = investigate_and_write_plan(request)
  present(draft)
  if user_authorization is plan_only or unclear:
      stop_without_worktree_agent_or_code_write()
  if material_plan_changed_after_confirmation:
      append_plan_changes()
      return_to_user_for_confirmation()
  route = delegated_manual unless user_explicitly_selected_automatic
  create_worktree_and_execution(route)

monitor_ci(target):
  require_explicit_single_target(target)
  spawn_one_gkd_ci_monitor(fork_turns=none)
  wait_agent(timeout_ms=approved_timeout_ms)
  trust_only_terminal_result()
  stop_on_success_failure_timeout_error_or_drift()

closeout(task):
  main_accepts_and_writes_review()
  create_and_redact_archive()
  if clean_and_authorized:
      remove_worktree_and_merged_local_branch()
      switch_trusted_main_to_main_and_verify_clean()
  else:
      preserve_scene_and_report_blocked()
  send_detailed_user_report()
```

### 验证矩阵

| Check | Command / fixture | Expected result | Not run / reason |
| --- | --- | --- | --- |
| 规则一致性 | `rg` 检查 `gkd-main`、CI Skill、角色 TOML、README、manual workflow、模板 | plan-only、CI 子代理、脚本入口、等待和收尾规则无冲突 | 施工前不修改代码 |
| CI 入口 | 现有 `scripts/tests/test_gkd_github_watch.py` 加静态角色/调用约束检查 | 只允许单目标和只读脚本；脚本缺失/目标漂移/超时均停止 | 真实 GitHub 监控仍需环境授权 |
| PLAN 闸门 | 手工演练“只拟 PLAN”“批准 PLAN 后执行”“材料性变更后再确认” | 前者不创建 worktree/代理/写入，后两者按确认状态分流 | 不启动真实执行代理 |
| 清理 Skill | 临时 fixture 包含旧 Skill、入口、引用、状态文件和普通业务文件 | 旧活动机制全部盘点并按授权清理，普通业务和历史记录不误删 | 不对真实老项目执行删除 |
| 收尾 | 手工演练成功、阻塞、未提交改动三条路径 | 成功路径归档、报告、删除 worktree/分支并回到干净 main；异常路径保留现场 | 不删除当前项目现有 worktree |
| 审查版本 | 两轮 review fixture（rN -> rN+1） | 顶部当前审查块唯一指向当前结论，旧块只有一行 superseded 标记；普通修订不产生新 revision | 不引入机器状态或额外数据库 |
| 文档质量 | `git diff --check`、逐文件交叉引用核对 | 模板字段和角色边界完整，报告可由用户独立理解 | 最终验收待施工完成后进行 |

### 风险、取舍与待讨论事项

- CI “必须使用子代理”针对的是需要等待的持续监控；一次性读取单个状态是否也必须派生角色，待用户决定。当前草案默认：只要进入等待，就必须使用角色；一次性预检可由 main 只读执行。
- 远端任务分支删除属于 GitHub 写操作；本草案默认只自动删除已合并的本地 worktree/分支，远端删除仍以 PLAN 中的明确授权或平台自动删除事实为准。项目活动 PLAN 文件的删除仅限已归档且确认只属于本轮的文件。
- 临时清理 Skill 的删除时机和是否连同文档/测试一起删除，留待用户另行授权；本轮不预先删除。
- 详细报告的具体篇幅和是否同时输出机器可读摘要，留待用户后续补充；本草案默认用户报告以 Markdown 自然语言为主，归档只保存脱敏摘要。
- 审查记录采用“当前块 + 旧块一行 superseded 标记”的最小方案；不再把审查历史拆成额外文件。
- 未完成本 revision 的任何代码、Skill、文档或工作流修改；在用户继续追加问题并确认 PLAN 前，必须保持当前工作树不变。
