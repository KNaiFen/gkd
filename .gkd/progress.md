# 进度报告

## 当前状态

已完成历史调查、计划落盘和三种项目级角色预设；本轮已补齐施工前 PLAN 合同和 T1-T5 任务边界，并明确 GKD 是完整的项目开发工作流。监控脚本、需求问答与项目适配尚未开始。

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

T1 已完成并合入主分支；下一步按更新后的 `.gkd/plan.md` 创建 T2 的 `.gkd/execution.md`，自动启动 CI 监控工具施工角色。

## T1 主分支收尾（2026-09-03）

- T1 的独立验收已通过，执行角色只依赖 worktree 内 `.gkd/execution.md`；main 方案、变更记录和审查记录保持独立。
- T1 提交 `094724b` 已由 main 合入为 `a47627b`；本轮自动分阶段委派来自用户明确要求。

## T2 主分支收尾（2026-09-03）

- T2 独立验收已通过，提交 `0e37f89` 已由 main 合入为 `de88920`。
- 监控脚本使用 Python 3 标准库和只读 `gh api`；11 项 fake git/gh 测试、帮助输出和 `git diff --check` 均通过。
- 真实 GitHub 凭据/API 轮询未执行，保留为后续环境风险；未新增 GitHub 写操作。

## 下一步（更新）

开始 T3：在新 worktree 生成 `.gkd/execution.md`，自动启动需求问答 Skill 施工角色。

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
