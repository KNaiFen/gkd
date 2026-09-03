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
