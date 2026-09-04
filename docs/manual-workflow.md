# Manual-first 工作流

GKD 将需求对齐、具体方案、隔离执行、CI 监控、独立验收和授权交付串成一套完整工作流。本文规定其中默认的 manual-first 协作方式；它只约定协作材料和工作顺序，不是机器状态机，也不要求填写 JSON、digest 或 CAS。需要等待 CI 时，按下文统一显式传入监控参数。目标项目的活动记录统一放在 `.gkd/`：main 维护 `.gkd/plan.md`、`.gkd/plan-changes.md` 和 `.gkd/review.md`，执行 session 使用 worktree 内的 `.gkd/execution.md` 并更新 `.gkd/progress.md`。执行 session 默认由用户手动启动；用户明确选择自动模式后，main 才可用 `agent_type=gkd_execute` 启动执行 session。仅拟 PLAN 与批准 PLAN 后开始执行是两个独立授权状态。

## 路径选择

1. `plan-only`：用户只要求拟 PLAN、先出方案或按方向整理时，main 只调查、问答和写目标项目 `.gkd/plan.md`。此状态禁止创建执行 worktree/任务分支、写目标项目代码、启动执行/CI/验收代理、提交、推送、合并、创建 release、发布或清理现场；授权不明确时继续停留在此状态。
2. `direct-main`：用户已明确批准执行且任务简单、低风险且未指定子代理时，由 main 直接完成，不创建执行 session；用户明确要求子代理时，以用户选择覆盖复杂度判断。
3. `delegated/manual`：用户明确批准按 PLAN 开始执行后，需要执行 session 时的默认路径。main 在目标项目 `.gkd/` 维护 `plan.md` 并在 worktree 生成 `.gkd/execution.md`，向用户发送启动提示；用户在声明 worktree 中手动启动执行 session。
4. `delegated/automatic`：仅在用户明确批准执行且选择自动模式时使用。main 先生成或更新 worktree 内 `.gkd/execution.md`，再读取 `.codex/agents/gkd_execute.toml`，通过原生 `spawn_agent` 以 `agent_type=gkd_execute` 启动执行 session，并传入 `fork_turns=none`。

自动启动只替代“用户打开一个新 session”这个动作。它不恢复旧 GKD automatic route、机器生命周期或自动验收，也不改变用户对路径选择和审查结论的控制。用户只批准总体方向时，后来新增的文件范围、接口/数据库、展示、发布等材料性变化必须追加 `plan-changes.md` 并重新确认，不能默认为已授权。

## CI 监控入口

需要等待的 PR、workflow run、commit 或 release CI，在 PLAN 已授权且目标唯一明确后，必须启动命名的 `gkd_ci_monitor` 只读子代理；main 不自行持续轮询。该角色只调用目标项目的 `scripts/gkd-github-watch` 可执行入口，并传入一个目标参数：`--pr <number>`、`--run <id>`、`--commit <sha>` 或 `--release <tag>`，且每次都显式传入 `--interval 30 --timeout 3600`。改变 interval 或 timeout 任一参数都必须先由 PLAN 明确授权，并同步父代理的一次性等待时长。可选 `--repo owner/name`；脚本只执行 `gh api` 只读查询，返回成功、失败、超时或调用错误退出码；角色应原样报告目标、URL、状态、失败检查摘要和后续建议，不得调用 GitHub CLI 的 watch 子命令，也不得临时拼接轮询、重跑或取消命令。脚本缺失、目标漂移、无法唯一解析或认证不可用时立即报告阻塞。

main 启动监控代理后只等待一次 `wait_agent(timeout_ms=3600000)`（或 PLAN 明确批准且与 timeout 一致的时长），等待期间不读取仓库/CI、不补充分析、不重复启动。代理返回成功、失败、取消、超时、调用错误或目标漂移后立即停止；失败后的修复重新规划并取得必要授权。

## 三个输入

每个任务开始时，主代理只需要确定：

1. **工作目标**：要完成什么，以及完成到什么程度。
2. **工作目录**：执行代理使用的 Git worktree 路径。
3. **行为约束**：允许修改的范围、不能触碰的内容、需要遵守的项目规则。

其他路径、分支名、提交编号和命令行参数由主代理按普通 Git 操作处理，不作为执行代理的协议输入。

## 五份记录

可直接复制的模板位于 `docs/templates/manual/`。

### `plan.md`

由 main 在目标项目 `.gkd/` 创建和维护，是主方案、技术选型、实现思路、授权和审查依据。施工前计划应写出现状证据、目标行为、采用的技术栈/现有工具、关键实现步骤、范围/非目标、文件与符号级变更表、接口和配置、角色写入边界、CI 目标和等待参数、逐项验证命令及预期结果、偏差处理、归档/清理授权、`.gkd/progress.md` 更新点、停止条件和仍需决定的事项。只有存在非显然分支、状态转换或外部命令编排时才写针对性伪代码。

`.gkd/plan.md` 不是执行 session 的施工指令。施工中若目标行为、文件边界、角色职责、授权范围或主流程发生变化，执行代理先更新 `.gkd/progress.md` 并停止，main 修改计划并重新取得必要确认。

### `execution.md`

由 main 从已批准的 `.gkd/plan.md` 生成，必须位于目标 worktree 内，是执行 session 的唯一任务交接文档。它写明当前 revision、可修改文件/符号、实现步骤、技术约束、验证命令和本轮具体修改建议；执行 session 读取它和适用的 `AGENTS.md`，不把 `.gkd/plan.md` 当作施工指令。

### `plan-changes.md`

由 main 在 `.gkd/` 追加维护，记录每次 PLAN 修订的原因、验收依据、影响、授权变化、旧思路与新思路，以及对应的 `.gkd/execution.md` revision；不覆盖旧条目。

### `progress.md`

由执行代理在 worktree 的 `.gkd/progress.md` 持续更新，使用自然语言记录已经完成的工作、当前判断、遇到的问题、未完成事项和下一步。它是执行事实，不是机器状态；不承担 PLAN 变更历史。

### `review.md`

由 main 在查看 diff 后记录审查结论。文件顶部只保留一个当前审查块，写明 PLAN revision、execution revision、被审查的 Git head 和当前状态（通过、返工或阻塞）。需要保留历史审查时，在旧审查块标题下只增加一行“状态：已被 rN 取代（superseded）”，不删除原文、不为每条 finding 增加额外状态字段；普通排版修正不创建新 revision。通过时写明通过；不通过时先写问题、优先级和下一步，再修改 `.gkd/plan.md`、追加 `.gkd/plan-changes.md`，并更新 worktree 内 `.gkd/execution.md` 的 revision 和具体修改建议。机器事实不需要抄写到这里，直接引用 Git diff、测试输出或文件路径即可。

示例：

```markdown
## 当前审查（PLAN r10 / execution r10 / head abc1234）
状态：通过

## 历史审查（PLAN r9 / execution r9 / head def5678）
状态：已被 r10 取代（superseded）
```

## 项目归档

一轮已批准的 delegated 执行 session 完成后，main 必须先由 `gkd_accept` 独立验收，再写下 `.gkd/review.md`；只有审查通过并完成计划授权的交付动作，才能宣称成功，且成功路径必须创建最终归档。用户决定停止、明确保留当前成果或确认阻塞时，也可先写下当前审查结论并创建临时归档，但 `summary.md` 必须标注“未验收”或“阻塞中”，不能把临时材料当成最终完成记录：

1. 确认目标项目主工作树、任务逻辑 ID、日期和来源 revision；不把本机绝对路径当作归档标识。
2. 从该轮执行 worktree 读取 `.gkd/execution.md`、`.gkd/progress.md`，从目标项目 `.gkd/` 读取 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`。
3. 创建 `.gkd/archive/<task-id>/<date>-<revision>/`，用普通文件复制或整理保存上述五份快照和按 `docs/templates/manual/archive-summary.md` 填写的 `summary.md`。
4. 删除或改写快照中的本机绝对路径、令牌、账号、机密值和运行时状态；只保留逻辑 worktree、分支和变更标识，并检查归档内容可独立读懂目标、取舍、结果和风险。
5. 在 `.gkd/progress.md` 记录归档目录、文件清单和实际验证；确认归档完整且活动记录只属于当前任务后，准备删除本轮已归档的活动 `plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`。
6. 仅在 PLAN 已授权时创建包含上述活动记录删除的 cleanup commit；main 审查该 commit，并仅在已有提交/合并授权时提交或合并。
7. 确认 cleanup commit 已合并、执行 session 已停止且 worktree 无未提交改动后，删除本地任务 worktree 和本地任务分支；远端只删除已确认合并本轮任务的分支，状态不明则保留现场。
8. 将可信主 checkout 切回 `main`，确认 `git status --short` 为空且跟踪关系清晰，再向用户发送详细收尾报告。任何审查失败、未提交改动、共享活动记录、cleanup commit/合并未获授权或删除条件不满足，都保留现场并报告未完成/阻塞。

归档是目标项目自己的普通 Markdown 长期记录，不是运行时事实源、索引服务或状态机制。delegated 成功必须归档；简单 `direct-main` 任务跳过代理验收和 worktree 删除，归档按需进行，但仍需 main 审查、恢复干净 `main` 并输出详细报告；是否把归档随目标项目提交，仍由该任务的 PLAN 和用户授权决定。

## 标准顺序

```text
main 处于 plan-only：调查、问答、写 PLAN 并等待用户明确“按此 PLAN 开始执行”
批准后选择 direct-main，或创建 worktree 并生成 `.gkd/execution.md`
delegated 路径：manual 交接给用户，automatic 在明确选择后启动 `agent_type=gkd_execute`
执行 session 读取 `.gkd/execution.md`，持续更新 `.gkd/progress.md`，完成后通知 main
需要等待 CI 时：启动一次 `gkd_ci_monitor`，只调用 `scripts/gkd-github-watch`，main 一次性等待并接收终态
delegated：已批准执行 session 完成后由 `gkd_accept` 独立验收，main 写 `.gkd/review.md`；direct-main：main 完成轻量审查
delegated 通过后创建脱敏归档，再按授权创建包含活动记录删除的 cleanup commit、审查/合并并清理已合并分支，恢复干净 `main` 并输出详细报告
不通过、阻塞、未提交改动或清理条件不满足时保留现场并报告未完成
```

创建 worktree 和启动执行 session 之间，main 应先把方案和执行交接写清楚；施工中发现新事实时可由 main 灵活调整文档，不把它当成机器门禁。

## 用户手动启动提示

```text
读取当前 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只阅读完成 `.gkd/execution.md` 所需的代码，并在声明的 worktree 中工作。
把重要进展、判断、阻塞和实际运行的验证结果写入 .gkd/progress.md。
不要修改计划中声明的非目标范围。
完成后停止并通知主代理，由主代理审查 diff。
```

main 将以上提示与声明的 worktree 交给用户；未获用户明确选择自动模式时，main 到此为止，不启动子代理。

## 详细收尾报告

审查通过且计划中授权的交付动作完成后，main 主动向用户输出详细报告，不能只说“完成”或只给提交号。报告至少包含：任务目标和成功标准、实际修改的文件/符号、实现行为和数据流、与 PLAN 的一致性或偏差及原因/授权、验证命令与结果、CI/PR/release 结果、未验证风险、提交/合并/发布标识、归档位置、worktree/分支清理结果和后续建议。报告不得包含完整对话、全量日志、令牌、账号或本机绝对路径；同一报告的脱敏摘要写入归档 `summary.md`。

## 临时旧版清理

`gkd-legacy-cleanup` 只在 main 明确指定老项目根目录和逐项删除授权时使用。它先只读盘点并按当前有效规则、明确遗留、普通业务、证据不足分类，再按授权删除旧 GKD 可执行入口、Skill、脚本、状态和引用；普通业务与 `.gkd/archive/` 历史记录默认保留，不触碰生产用户目录，不设计兼容模式。证据不足或共享活动记录时保留现场并报告阻塞。

## main 自动启动提示

用户明确选择自动模式后，main 先读取当前 Codex 配置中的 `.codex/agents/gkd_execute.toml`，确认 `agent_type=gkd_execute` 可用。main 使用当前原生 agents API 的对应配置字段调用一次 `spawn_agent`，传入 `agent_type=gkd_execute`、`fork_turns=none`、声明的 worktree 和下列提示。角色、模型与权限由当前配置决定，不在本协议中另行写死。

```text
读取声明 worktree 中的 .gkd/execution.md 和适用的 AGENTS.md；不要把 .gkd/plan.md 当作施工指令。
只在该 worktree 中施工；不要修改声明的非目标。
在重要判断、里程碑、阻塞和验证结果影响交接时更新 .gkd/progress.md。
完成后停止并通知 main。不要验收、合并、发布、清理 worktree 或启动其他施工代理。
```

同一 worktree 的同一施工轮次只允许这个子代理写实现文件。main 在其停止前不修改实现文件；若角色配置、spawn 调用或启动结果不可用，main 明确报告阻塞并保留 worktree，等待用户选择下一条路径。

## 主代理审查

主代理只需检查：

- diff 是否完成目标并保持在范围内；
- 施工前 PLAN 是否达到实现就绪，伪代码和文件级边界是否覆盖实际改动；
- 是否违反行为约束或项目规则；
- `.gkd/progress.md` 是否说明了实际完成情况和剩余风险；
- 必要的局部测试或手工验证是否足够。

通过后按 PLAN 中已经获授权的普通 Git 流程提交、推送、合并或发版；未授权的动作停在交付前，不临时追加确认来替代计划。不通过时先记录 `.gkd/review.md`，再修改 main 的 `.gkd/plan.md`，追加 `.gkd/plan-changes.md`，更新 worktree `.gkd/execution.md` 并明确通知下一轮 session；旧 execution session 不受 PLAN 修改的隐式影响。后一轮可以是用户手动启动或用户再次明确选择的自动启动，但不得与前一轮并行写入。delegated 审查通过后仍须按“归档 -> cleanup commit -> main 审查/合并（按授权） -> 活动记录和已合并分支清理 -> 恢复干净 main -> 详细报告”顺序收尾；远端分支状态不明时保留现场，条件不满足时不得宣称完成。

## 中断与恢复

新的执行 session 先读取同一个 worktree 的 `.gkd/execution.md` 和 `.gkd/progress.md`，再查看未提交 diff 与最近提交。需要理解计划为何变化时，由 main 提供 `.gkd/plan-changes.md`；报告不完整时以代码和 Git 历史为准，并把新的判断补回 `.gkd/progress.md`；不依赖旧对话线程。

## 边界

本协议是唯一正常人工工作流。执行代理不读取无关历史材料，也不调用其他 GKD 自动化入口。自动启动失败不会隐式降级为 `direct-main` 或伪装成手动交接成功。CI 等待失败、超时、目标漂移或认证错误不会触发重试或写操作。生产 `~/.codex`、AIO、GitHub settings、Secrets、付费 runner 和既有 release 资产不在本协议范围内。
