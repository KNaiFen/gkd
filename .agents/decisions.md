# Decisions

- [2026-09-01] 采用 manual-first 作为唯一工作流。
  - Why: 普通编码任务只需要目标、工作目录、行为约束和可审查交接，不需要自动生命周期。
  - Impact: 主代理维护计划和审查，执行代理维护进度，Git worktree 是代码事实源。

- [2026-09-02] 移除旧自动化合同实现。
  - Why: 旧脚本、JSON 合同、角色路由和固定验收会扩大上下文和入口选择，却不服务当前人工闭环。
  - Impact: 当前工作树只保留 `gkd-main` 与 Markdown 协作材料；历史从 Git 提交追溯。

- [2026-09-02] 验证遵循最少必要原则。
  - Why: 为无关变更运行完整旧合同会增加时间和上下文成本。
  - Impact: 只运行与计划目标和改动直接相关的局部检查，并把实际结果或未验证范围写入交接记录。

- [2026-09-03] 恢复执行 session 的双启动入口。
  - Why: 用户仍需要保留手动交接作为默认，同时可明确选择由 main 以命名 `agent_type=gkd_execute` 启动执行 session，减少新开 session 的操作。
  - Impact: `delegated/manual` 保持默认；`delegated/automatic` 只以原生 `spawn_agent` 打开一个普通执行 session，继续使用 worktree 和 Markdown 交接，不恢复旧 automatic route 或机器生命周期。

- [2026-09-03] 以原生角色和 Skills 补齐工作流，而非恢复旧运行时。
  - Why: 需要 main 自动路由、执行/CI 监控/验收角色、需求问答和项目适配能力，但不需要合同、状态机、断点恢复或 watcher 平台。
  - Impact: 当时草案曾统一设为 `gpt-5.6-sol` / `xhigh`；该模型分配已由本文件后续决定修订为执行/验收 Sol-xhigh、CI 监控 Terra-high。

- [2026-09-03] GitHub 长流程采用复用的只读监控脚本。
  - Why: CI、Actions 和发布等待不应让每个 session 重复临时构造 `gh` 轮询命令。
  - Impact: 监控脚本负责明确目标的查询、轮询和终态报告；它不写 GitHub 状态，实际发布和其他远程写操作仍需用户授权。

- [2026-09-03] 角色配置放入项目 `.codex/agents/`。
  - Why: 角色提示词、模型和推理强度必须由可调用预设绑定，不能只依赖 main 每次转述或泛化子代理默认值。
  - Impact: `gkd_execute`、`gkd_accept` 固定为 `gpt-5.6-sol` / `xhigh`，`gkd_ci_monitor` 固定为 `gpt-5.6-terra` / `high`，并分别约束为 worktree 写入、只读监控、只读验收；main 启动执行时只用命名 `agent_type=gkd_execute` 调用。

- [2026-09-03] PLAN 以具体实现方案指导 main，而非充当执行状态门禁。
  - Why: 原计划只有阶段目标，执行 session 仍需现场补设计；但固定 checklist、错误码和状态转换又会把 Markdown 工作流重新做成旧式合同。
  - Impact: PLAN 应写清技术栈、实现思路、文件/符号、验证和授权边界；复杂分支才写伪代码。main 根据事实灵活调整 PLAN，执行 session 只读取 worktree 的 `execution.md`。

- [2026-09-03] 分离 main 方案、执行交接和项目归档。
  - Why: 验收后的 PLAN 调整不应改变正在工作的 session，也需要让目标项目能回看自己做过什么。
  - Impact: main 维护目标项目 `.gkd/plan.md`、追加 `.gkd/plan-changes.md`、写 `.gkd/review.md`；worktree 内 `.gkd/execution.md` 是执行指令，`.gkd/progress.md` 记录执行事实。已批准 delegated 成功必须将这些材料和摘要归档至目标项目 `.gkd/archive/`，不新增运行时状态；direct-main 仅按需归档。

- [2026-09-03] GKD 的主旨是完整的项目开发工作流。
  - Why: 用户需要把需求澄清、方案确认、角色执行、CI/验收和按授权交付组织成一条连续流程；辅助 Skills 不能成为彼此割裂的工具箱。
  - Impact: `gkd-main` 负责编排完整主流程；需求问答、项目适配和 CI 优化只作为按需附属能力，不能绕过 PLAN、用户确认、worktree 施工或 main 审查。

- [2026-09-04] 将拟 PLAN 与批准后执行分为独立授权状态。
  - Why: 用户批准技术方向不应被推断为批准新增文件、代码、代理或外部交付动作。
  - Impact: `plan-only` 只允许调查、问答和写 PLAN；材料性变化追加 `plan-changes.md` 并重新确认，批准后才可创建 worktree、启动角色或写代码。

- [2026-09-04] CI 持续等待固定由专用只读角色承担。
  - Why: 避免 main 自行轮询和多个临时命令路径，保持单目标、可审查的终态。
  - Impact: `gkd_ci_monitor` 只能调用已安装 `gkd-ci-monitor` Skill 目录中的 `scripts/gkd-github-watch` 并显式传入 `--interval 30 --timeout 3600`；目标项目不需要提供同名脚本，改变任一参数须有 PLAN 授权，入口缺失、漂移、认证错误和超时均立即报告，不重试或写 GitHub。

- [2026-09-04] 收尾先验收和归档，再清理现场并恢复干净 main。
  - Why: 活动记录删除前必须保留可独立阅读的脱敏事实，失败路径必须可恢复。
  - Impact: 已批准 delegated 执行完成后才由 `gkd_accept` 验收；通过后依次 main review、归档、按授权 cleanup commit、审查/合并、活动记录和已确认合并的本轮任务分支清理、main 状态确认，最后输出详细报告；条件不满足或远端状态不明时保留现场。临时 `gkd-legacy-cleanup` 只按明确授权清理老项目旧活动机制。

- [2026-09-04] 将早期 r10 草案明确为 superseded 历史背景。
  - Why: 旧草案和旧审查可能保留在活动记录或归档中，不能与当前已批准 revision 混淆。
  - Impact: 早期草案只用于追溯；当前施工、审查和授权以最新 PLAN、execution、progress 和 review 记录为准。

- [2026-09-05] 将审查后的收尾流程拆出为 `gkd-closeout` Skill。
  - Why: main 需要保留路由、授权和最终判断，归档与现场清理的具体步骤应有单一维护位置。
  - Impact: main 审查通过后路由到 `gkd-closeout`；该 Skill 不推断提交、合并、发版或其他外部写操作的授权，条件不满足时保留现场。

- [2026-09-05] 调整三个角色的模型配置。
  - Why: 执行和验收需要统一使用 `gpt-6-astra` / `xhigh`；CI 监控按用户指定使用 `gpt-5.6-terra` / `medium`。
  - Impact: `.codex/agents/` 与 main 的角色边界同步更新，系统安装动作在本次改造交付阶段单独完成。
