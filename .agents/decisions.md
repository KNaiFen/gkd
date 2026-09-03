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
  - Why: 用户仍需要保留手动交接作为默认，同时可明确选择由 main 启动已配置角色，减少新开 session 的操作。
  - Impact: `delegated/manual` 保持默认；`delegated/automatic` 只以原生 `spawn_agent` 打开一个普通执行 session，继续使用 worktree 和 Markdown 交接，不恢复旧 automatic route 或机器生命周期。

- [2026-09-03] 以原生角色和 Skills 补齐工作流，而非恢复旧运行时。
  - Why: 需要 main 自动路由、执行/CI 监控/验收角色、需求问答和项目适配能力，但不需要合同、状态机、断点恢复或 watcher 平台。
  - Impact: 当时草案曾统一设为 `gpt-5.6-sol` / `xhigh`；该模型分配已由本文件后续决定修订为执行/验收 Sol-xhigh、CI 监控 Terra-high。

- [2026-09-03] GitHub 长流程采用复用的只读监控脚本。
  - Why: CI、Actions 和发布等待不应让每个 session 重复临时构造 `gh` 轮询命令。
  - Impact: 监控脚本负责明确目标的查询、轮询和终态报告；它不写 GitHub 状态，实际发布和其他远程写操作仍需用户授权。

- [2026-09-03] 角色配置放入项目 `.codex/agents/`。
  - Why: 角色提示词、模型和推理强度必须由可调用预设绑定，不能只依赖 main 每次转述或泛化子代理默认值。
  - Impact: `gkd_execute`、`gkd_accept` 固定为 `gpt-5.6-sol` / `xhigh`，`gkd_ci_monitor` 固定为 `gpt-5.6-terra` / `high`，并分别约束为 worktree 写入、只读监控、只读验收；main 只用命名 `agent_type` 调用。

- [2026-09-03] 施工前 PLAN 必须达到实现就绪。
  - Why: 原计划只有阶段目标，执行 session 仍需现场补设计，导致实际施工偏离用户需求。
  - Impact: 启动前必须有现状证据、文件/符号级变更、接口、关键路径伪代码、失败/停止条件、授权边界和验证矩阵；材料性偏差先停工，更新计划并重新确认。
