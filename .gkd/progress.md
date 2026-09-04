# 进度报告

## 当前状态

已完成历史调查、计划落盘和三种项目级角色预设；T1-T6 已完成施工、独立验收和主分支收口，首轮材料与最终归档均已写入项目 `.gkd/archive/`。

## 已完成

- 对比当前工作树、旧发布版本、移除提交和真实历史 session，确认旧执行 session 的 worktree 交接模式可在当前 Markdown 架构中保留。
- 确认旧自动路由依赖的状态机、合同与 watcher 不属于本次恢复范围。
- 确认 Git 历史没有独立的需求问答或项目总体适配 Skill；旧 CI 优化能力仅为建议型分析。
- 根据当前要求重写 `plan.md`：执行和验收固定为 `gpt-5.6-sol` / `xhigh`，CI 监控固定为 `gpt-5.6-terra` / `high`，并规划可复用的 GitHub 长流程监控脚本。
- 新增 `.codex/agents/gkd_execute.toml`、`gkd_ci_monitor.toml`、`gkd_accept.toml`，将角色提示词、模型、推理强度和 sandbox 绑定到项目预设；三个角色均禁止再启动子代理。
- 更新 `gkd-main`：自动执行只可用 `agent_type=gkd_execute` 启动，监控和验收只可调用各自命名预设；不再读取或退回到泛化默认子代理。
- 更新 `gkd-main`、`docs/manual-workflow.md`：PLAN 需把技术栈、实现思路、文件/符号和验证写清；复杂分支才使用伪代码，交接不采用 readiness gate 或状态机。
- 更新 `VISION.md`、`README.md` 和工作流说明：明确“需求对齐 → PLAN → 角色执行 → CI/验收 → 按授权交付”是主流程，辅助 Skills 只服务于该流程。
- 新增 `execution.md`、`plan-changes.md` 和归档摘要模板：main 方案、worktree 执行交接、计划变更历史和项目长期记录分离。

## 当前边界

- 默认仍由用户手动启动写入型执行 session；main 自动启动执行角色必须由用户明确选择。
- CI 监控和验收保持只读；提交、推送、合并、创建 release 和实际发布均不因路由自动发生。
- 本轮已修改项目 Skill 和项目级 agent 配置；未修改脚本或用户级安装副本。

## 验证证据

- 已完整阅读 `VISION.md`，并以其 Git/Markdown/用户控制边界约束计划。
- 计划中的历史结论来自 Git 历史、旧真实 session 和现有工作树，不依赖对已删除运行时的臆测。
- `codex --strict-config --version` 已通过，确认当前 CLI 可读取项目配置而不报未知字段；实际 `agent_type` 启动和 worktree 隔离验证尚未执行。
- 已静态核对三个角色配置：执行/验收为 Sol/xhigh，CI 监控为 Terra/high；尚未做实际 role spawn 验证。

## 下一步

T1-T6 已完成并合入主分支；后续只有真实 role spawn、GitHub API 和跨项目归档体验等环境级可选验证。

## T1 主分支收尾（2026-09-03）

- T1 的独立验收已通过，执行角色只依赖 worktree 内 `.gkd/execution.md`；main 方案、变更记录和审查记录保持独立。
- T1 提交 `094724b` 已由 main 合入为 `a47627b`；本轮自动分阶段委派来自用户明确要求。

## T2 主分支收尾（2026-09-03）

- T2 独立验收已通过，提交 `0e37f89` 已由 main 合入为 `de88920`。
- 监控脚本使用 Python 3 标准库和只读 `gh api`；11 项 fake git/gh 测试、帮助输出和 `git diff --check` 均通过。
- 真实 GitHub 凭据/API 轮询未执行，保留为后续环境风险；未新增 GitHub 写操作。

## 下一步（更新）

开始 T3：在新 worktree 生成 `.gkd/execution.md`，自动启动需求问答 Skill 施工角色。

## T3 主分支收尾（2026-09-03）

- T3 独立验收通过，提交 `dd58611` 已由 main 合入为 `1953074`。
- `gkd-intake` 只处理材料性缺口，完整请求零提问，拒答/矛盾交回 main；没有新增问答状态文件或运行时 API。

## 下一步（更新）

开始 T4：在新 worktree 生成 `.gkd/execution.md`，自动启动项目适配与 CI 优化 Skills 施工角色。

## T4 主分支收尾（2026-09-03）

- T4 独立验收通过，提交 `6a99220` 已由 main 合入为 `1f35553`。
- `gkd-project-adapt` 和 `gkd-optimize-ci` 均只读调查并输出建议，不直接修改目标项目；资料不足时只询问影响方案的少量事实。

## 下一步（更新）

开始 T5：同步文档并进行路由、执行、监控、问答、适配和验收的端到端静态/手工演练。

## T1 执行记录（2026-09-03）

### 已完成

- 收敛 `.agents/skills/gkd-main/SKILL.md`：明确 `direct-main`、`delegated/manual`、用户明确选择的 `delegated/automatic`、CI 监控和独立验收路径；明确用户指定子代理可覆盖简单任务判断，并将自动启动约束为命名 `agent_type=gkd_execute` 与 `fork_turns=none`。
- 明确 main 维护目标项目 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`，执行 session 只读取 worktree `.gkd/execution.md` 并更新 `.gkd/progress.md`；验收返工由 main 先记录 review，再同步计划、变更记录和 execution revision。
- 同步 `docs/manual-workflow.md` 及 manual 模板的 `.gkd/` 路径、执行交接和归档记录说明。
- 在 `.agents/open-items.md` 记录当前路由和交接约定；同步 `.codex/agents/gkd_execute.toml`、`.codex/agents/gkd_accept.toml` 的角色提示词，CI 监控预设保持原配置。

### 验证证据

- `git diff --check`：通过。
- `rg -n 'direct-main|delegated/manual|delegated/automatic|gkd_execute|gkd_ci_monitor|gkd_accept|execution\\.md|plan-changes|\\.gkd/archive' .agents/skills/gkd-main/SKILL.md docs/manual-workflow.md docs/templates/manual`：通过，关键路径和角色/记录引用均存在。
- `rg -n 'readiness gate|JSON contract|CAS|fixed-head|状态机' .agents/skills/gkd-main/SKILL.md docs/manual-workflow.md .codex/agents/*.toml`：仅命中“不得恢复旧机制”的边界说明；未发现旧门禁、合同或状态机流程。
- 静态核对 `.codex/agents/gkd_execute.toml`、`gkd_ci_monitor.toml`、`gkd_accept.toml`：模型/推理强度分别为 Sol/xhigh、Terra/high、Sol/xhigh，sandbox 分别为 workspace-write、read-only、read-only。
- `codex --strict-config --version`：通过，输出 `codex-cli 0.153.0`。

### 未验证范围与风险

- 尚未实际调用 `agent_type` 启动角色，也未执行 worktree 隔离演练；这些需要 main 在验收或端到端演练阶段完成。
- 本轮只修改声明式 Markdown/Skill 文档，未新增运行时代码或测试夹具。

### 交接

本轮施工已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T1 执行记录（重做，2026-09-03）

### 本轮变更

- `.agents/skills/gkd-main/SKILL.md`：将计划变更、审查、execution 和 progress 的记录路径统一写成 `.gkd/` 前缀。
- `docs/manual-workflow.md`：自动 delegated 路径明确读取 `.codex/agents/gkd_execute.toml`，以 `agent_type=gkd_execute` 启动，并同步自动启动提示。
- `.codex/agents/gkd_accept.toml`：验收角色读取父代理 worktree 内适用的 `AGENTS.md` 与 `.gkd/` 记录，保持只读和按实际 diff 检查。

### 验证证据

- `git diff --check`：通过。
- 按 execution 要求执行路由/路径关键词 `rg`：通过，`direct-main`、`delegated/manual`、`delegated/automatic`、`gkd_execute`、`gkd_ci_monitor`、`gkd_accept`、`.gkd/execution.md`、`.gkd/plan-changes.md` 和 `.gkd/archive` 均有对应说明。
- 按 execution 要求执行旧机制关键词 `rg`：未发现旧门禁或状态机文案；仅保留“不得恢复旧机制”的边界说明。
- 额外检查 `.codex/agents/*.toml`：未发现裸 `plan.md`/`progress.md`/`review.md` 路径或 readiness gate、JSON contract、CAS、fixed-head、状态机要求。

### 未验证范围与剩余风险

- 未实际调用 `agent_type` 启动角色，也未执行 worktree 隔离演练；需由 main 在验收或端到端演练阶段完成。
- 本轮仍只修改声明式 Markdown 与角色提示词，未新增运行时代码或测试夹具。

### 交接

本轮施工已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T1 main 方案修订（2026-09-03-r4）

- 独立验收指出 T1 文件范围与实际 diff 不一致。main 已修改 `.gkd/plan.md`，并在 `.gkd/plan-changes.md` 追加 r4：execute/accept 角色预设、归档模板、open-items 和本进度记录属于 T1，CI 预设只核对。
- `.gkd/execution.md` 已同步 r4；执行目标和允许修改内容不变。

## T2 执行记录（2026-09-03）

### 本轮变更

- 新增 `scripts/gkd-github-watch`，使用 Python 3 标准库和 `gh api` 只读查询 PR、workflow run、commit status、release tag。
- 支持 `--pr`、`--run`、`--commit`、`--release` 互斥目标，以及 `--repo`、`--interval`、`--timeout`；未显式提供仓库时解析 `git remote get-url origin`，并校验显式仓库一致性。
- 统一输出目标、仓库、URL、状态、失败检查摘要和 UTC 查询时间；退出码 `0` 成功、`1` 失败/取消、`2` 超时、`3` 调用/认证/目标错误。
- 新增标准库 fake `git`/`gh` 测试，验证只调用 `gh api`、四类目标 endpoint、SSH remote 规范化、运行中到成功、失败摘要、未知结构、认证/目标不存在、仓库不一致、超时和工作目录无新增文件。
- 更新 `gkd_ci_monitor` 角色提示和 `docs/manual-workflow.md`，要求只调用该入口。

### 验证证据

- `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v`：通过（9 项）。
- `python3 scripts/gkd-github-watch --help`：通过，显示四种互斥目标及轮询参数。
- `git diff --check`：通过。

### 未验证范围与剩余风险

当前环境未使用真实 GitHub 凭据，未执行实际 API 轮询；fake `gh` 已证明脚本不调用重跑、取消或写 API。

### 交接

本轮施工已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T2 修正记录（2026-09-03）

### 本轮变更

- `scripts/gkd-github-watch`：显式 `--repo` 时允许当前 worktree 没有 `origin`；若 origin 可读则继续校验仓库一致性，未显式 repo 时仍要求解析 origin。
- `scripts/gkd-github-watch`：`--interval` 和 `--timeout` 拒绝 NaN、Infinity 及负数；每次 `gh api` 的 subprocess timeout 取轮询上限与全局 deadline 剩余时间的较小值，达到该 deadline 时输出 timeout 报告。
- `scripts/tests/test_gkd_github_watch.py`：fake `git` 覆盖无 origin，fake `gh` 支持延迟响应；新增显式仓库无 origin、全局 timeout 和非有限/负数参数测试。

### 验证证据

- `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v`：通过（11 项）。
- `python3 scripts/gkd-github-watch --help`：通过。
- `git diff --check`：通过。

### 未验证范围与剩余风险

当前环境未使用真实 GitHub 凭据，未执行实际 API 轮询；fake `gh` 仅验证 `api` 只读调用、deadline 超时和错误退出路径。

## T3 执行记录（2026-09-03）

### 本轮变更

- 新增 `.agents/skills/gkd-intake/SKILL.md`：定义目标、范围、验收、行为约束、工作目录和授权六类材料性缺口，按顺序一次只问一个问题；答案整理回 `.gkd/plan.md` 草案并保留未决事项。
- 明确完整请求直接返回“无需问答”，拒答或矛盾答案交回 `gkd-main`，不把默认值当作批准，不引入 JSON schema、问答状态文件或运行时 API。
- 同步 `.agents/skills/gkd-main/SKILL.md` 的触发说明，仅保留与 `gkd-intake` 的关系。

### 验证证据

- `git diff --check`：通过。
- 静态 `rg`：确认 `gkd-intake`、六类材料性检查、“一个问题”“无需问答”“未决”和“授权”均在预期 Skill/主流程文件中；未发现旧合同、状态机或机器状态描述。
- 手工核对示例：目标缺失时只问目标；目标完整但验收缺失时只问验收；目标、范围、验收、约束和授权均明确且工作目录已知时返回“无需问答”。

### 未验证范围与剩余风险

- 本轮只修改声明式 Markdown，未新增运行时代码或测试夹具；实际 session 路由和跨 worktree 行为仍由 main 在验收阶段核对。

### 交接

本轮施工已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T4 执行记录（2026-09-03）

### 本轮变更

- 新增 `.agents/skills/gkd-project-adapt/SKILL.md`：定义项目根目录、工作流约束和本机限制等输入；按技术栈、包管理器、测试/构建命令、CI、发布、runner 和资源清单调查；要求以 `path:line`、命令摘要或运行链接引用证据，并输出适配选项、推荐方案、实现就绪 PLAN 草案和停止条件。
- 新增 `.agents/skills/gkd-optimize-ci/SKILL.md`：定义 workflow YAML、复用 workflow、运行事实、required checks、runner 和约束输入；分析 job DAG、矩阵与 fail-fast、缓存、重复构建、并发和排队/执行时间；按 P0/P1/P2 排序建议并报告未知结构和证据缺口。
- 更新 `.agents/skills/gkd-main/SKILL.md`：增加两个 Skill 的触发关系和只读边界，明确建议必须回到 PLAN、用户确认与 main 审查，不复制附属 Skill 的完整指令。
- 两个 Skill 均明确不直接修改目标项目、不执行 CI 写操作、不恢复旧 AIO、状态机、机器合同、固定 head 验收或常驻 watcher。

### 静态示例核对

- Rust 示例：假设 Cargo workspace 有 `Cargo.toml`、测试与 Actions workflow。适配 Skill 可从实际 `cargo test`/`cargo clippy`/构建命令和 runner 资源形成建议；CI Skill 可沿 `needs` 识别重复编译与缓存 key，并要求用运行样本确认时延，不把 Cargo 或 Actions 默认行为写死。
- 非 Rust/Actions 示例：假设 Python 项目使用 `pyproject.toml` 与 GitLab CI。适配 Skill 仍能调查包管理器、测试和发布约束；CI Skill 在没有 `.github/workflows` 或 GitHub required-check 事实时只报告 CI 平台证据缺口并询问影响排序的问题，不猜测 DAG 或分支保护。

### 验证证据

- `git diff --check`：通过。
- 静态 `rg`：确认 `project-adapt`、`optimize-ci`、工作流/CI、job DAG、required checks、AIO、不直接修改和用户确认等关键词出现在预期 Skill、`gkd-main` 与本进度文件中。
- 新增 Skill 逐文件尾随空白与固定路径扫描：通过；未发现 `/Users/`、`/home/`、`~/.codex`、`/tmp/` 或 AIO 固定路径引用。
- 未修改任何目标项目代码、脚本、角色 TOML 或生产用户目录；未执行 CI 写操作、发布或外部 API 轮询。

### 未验证范围与剩余风险

- 本轮仅修改声明式 Markdown，未在真实 Rust、Python/GitLab 或其他项目上运行 Skill；实际项目资料、runner 设置和分支保护仍需由 main 或用户提供并核对。
- 两个 Skill 的建议质量依赖可读取的 workflow 与运行事实；缺失时会停在证据缺口和用户确认前，不自动补全。

### 交接

本轮施工已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T4 修正记录（2026-09-03-r7）

### 本轮修正

- `.agents/skills/gkd-optimize-ci/SKILL.md`：明确资料不足时只询问会改变优化方向的少量事实，其余不确定性列为证据缺口；输出章节同步保留同一停止规则。

### 静态验证

- `git diff --check`：通过。
- `rg -n '资料不足|改变优化方向|证据缺口|用户确认|不直接编辑目标项目' .agents/skills/gkd-optimize-ci/SKILL.md .gkd/progress.md`：通过，命中修正措辞及既有停止边界。

### 未验证范围与剩余风险

- 仅完成 Markdown 静态修正，未在真实项目 workflow 或运行事实环境中执行 Skill；建议排序仍依赖用户提供的 CI 证据。

### 交接

本轮修正已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T5 执行记录（2026-09-03）

### T5 主分支收口

- T5 独立验收已通过；README、手工工作流和 ADR 的活动记录路径已统一为目标项目 `.gkd/`，并保留 manual-first、明确选择后自动启动和只读监控边界。
- T5 提交 `bd9bd93` 已由 main 合入为 `42b4e7d`；11 项监控测试、文档交叉引用和角色配置静态核对均通过。
- T6 归档尚待施工；真实 role spawn、GitHub API 和跨项目归档仍是环境级未验证风险。

### 本轮同步

- README、手工工作流和 ADR-002 中面向用户的协作记录引用统一为 `.gkd/plan.md`、`.gkd/execution.md`、`.gkd/progress.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`，明确执行交接与进度报告均位于目标 worktree 的 `.gkd/`。
- 保持 manual-first 默认、用户明确选择才可自动启动、CI 监控与验收只读、活动记录使用 Markdown、归档位于目标项目 `.gkd/archive/`；未新增状态机、门禁、机器合同或运行时状态。

### 验证证据

- `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v`：11 项测试全部通过，覆盖四类目标 endpoint、只读调用、运行中到成功、失败摘要、认证/目标错误、仓库不一致和超时。
- `python3 scripts/gkd-github-watch --help`：通过，显示 `--pr`、`--run`、`--commit`、`--release` 互斥目标及轮询参数。
- `git diff --check`：通过。
- `rg -n '\.gkd/(plan|execution|progress|plan-changes|review)|\.gkd/archive|direct-main|delegated/manual|delegated/automatic|gkd-intake|gkd-project-adapt|gkd-optimize-ci|gkd_accept|gkd_ci_monitor' README.md AGENTS.md VISION.md docs .agents .codex`：关键路径、路由、附属 Skill 和角色引用均命中；旧门禁/状态机仅保留明确的“不恢复”边界说明。
- `codex --strict-config --version`：通过，输出 `codex-cli 0.153.0`。逐文件静态核对 `.codex/agents/*.toml`：`gkd_execute` 为 Sol/xhigh、workspace-write；`gkd_accept` 为 Sol/xhigh、read-only；`gkd_ci_monitor` 为 Terra/high、read-only。
- `git worktree list --porcelain`：确认 `t5-final` worktree 与 `task/t5-final` 分支存在，未产生额外 worktree 或状态文件。

### 手工流程演练

- 简单、低风险且未指定子代理的请求走 `direct-main`，不创建执行 session；用户明确要求子代理时，按用户选择进入 delegated 路径。
- 委派任务默认走 `delegated/manual`：main 在目标项目 `.gkd/` 写计划并在 worktree 生成 `.gkd/execution.md`，用户手动启动后由执行 session 更新 `.gkd/progress.md`。只有用户明确选择自动模式时，才读取 `gkd_execute` 预设并以命名 `agent_type` 启动；失败保留 worktree，不降级为其他角色或 `direct-main`。
- 目标、范围、验收、行为约束、工作目录或授权缺失时，先由 `gkd-intake` 按顺序一次提一个问题；完整请求返回“无需问答”，拒答或矛盾答案交回 main，不开始施工。
- `gkd-project-adapt` 与 `gkd-optimize-ci` 仅读取项目事实并输出带证据的适配/优化建议；资料不足时询问会改变方向的少量事实，其余列为证据缺口，用户确认前不编辑目标项目或 CI。
- delegated 轮次经 main 审查后，可将五份记录和摘要保存到目标项目 `.gkd/archive/<task-id>/<date>-<revision>/`；本轮没有独立示例项目和归档授权，因此未创建归档目录。

### 未验证范围与剩余风险

- 未实际调用 `agent_type` 角色或验证跨进程 worktree 隔离；按执行角色边界仅完成配置与文档静态核对，实际 spawn 由 main 在验收/端到端环境决定。
- 未使用真实 GitHub 凭据执行 API 轮询；监控脚本行为由 fake `gh` 单测覆盖。真实远程状态、分支保护和发布设置仍需有权限环境验证。
- `.agents/` 持久记录中的部分文件名保留上下文内的相对简称；它们不在本轮 execution 允许修改范围内，且不改变 `.gkd/` 事实源语义。

### 交接

本轮文档同步、静态检查和文档级手工演练已完成，等待 main 审查 diff；不提交、不合并、不发布、不清理 worktree。

## T6 执行记录（2026-09-03）

### T6 主分支收口

- T6 独立验收首轮发现归档快照早于 main 审查；main 已将该 finding 写入 `.gkd/review.md`，并按 `2026-09-03-r9` 修订归档时序。
- T6 文档改动和归档材料提交 `3af7c12` 已由 main 合入为 `b67f2ab`；随后 main 在独立审查结论确定后刷新六份最终快照。
- 首轮材料保留在 `.gkd/archive/t6-archive/2026-09-03-19e7514/`；最终归档目录为 `.gkd/archive/t6-archive/2026-09-03-r9-final/`，包含 `summary.md`、`plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`；`summary.md` 和 `review.md` 均记录 T6 通过，未引入自动提交或发布。

### 本轮变更

- `.agents/skills/gkd-main/SKILL.md`：补充归档时机、来源、目录结构、脱敏要求和 `direct-main` 的长期价值取舍；明确归档不反向修改活动记录，也不自动提交或发布。
- `docs/manual-workflow.md`：写清 main 审查后从执行 worktree 与目标项目 `.gkd/` 汇总五份记录、填写摘要、脱敏检查和进度记录的顺序。
- `README.md`：增加简洁的归档用途和授权边界说明。
- `docs/templates/manual/archive-summary.md`：增加任务标识、来源 revision、用户可见结果和未验证风险字段，并提醒不记录本机路径、凭据或运行时状态。
- 创建首轮 `.gkd/archive/t6-archive/2026-09-03-19e7514/` 和最终 `.gkd/archive/t6-archive/2026-09-03-r9-final/`，各包含六份 Markdown 快照；最终快照中的实际本机路径和凭据已脱敏。

### 验证证据

- `git diff --check`：通过。
- `find .gkd/archive/t6-archive -mindepth 2 -maxdepth 2 -type f -print | sort`：通过，首轮和最终目录各有六份归档文件。
- 归档敏感信息扫描：未发现实际本机路径、凭据或令牌；规则中的 `~/.codex`、`token`、`secret` 仅出现在不恢复/脱敏说明和扫描命令自描述中。
- `rg -n '\.gkd/archive|execution\.md|progress\.md|summary\.md' .agents/skills/gkd-main/SKILL.md docs/manual-workflow.md README.md docs/templates/manual/archive-summary.md`：通过，规则、来源和模板字段相互引用。
- 首轮材料与最终快照均已按本轮 PLAN 作为目标项目文档变更纳入主分支收口，未触发自动提交、推送、合并或发布动作。

### 未验证范围与剩余风险

- 未进行真实跨项目复制、角色启动、跨进程 worktree 隔离或 GitHub API 验证；这些不在本轮施工范围内。

### 交接

归档示例和规则文档已完成，验证结果已记录，通知 main 审查；不提交、不合并、不发布、不清理 worktree。

## r10.6 执行交接（2026-09-04）

- 主代理已按用户明确授权选择 `delegated/automatic`，本 worktree 只承载 r10.6 文件范围。
- 执行代理不得删除本轮 `.gkd` 活动记录；验收、审查、归档、合并及本地/远端任务分支清理由 main 按收尾顺序负责。
