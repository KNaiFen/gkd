# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1、M2-A 与 M2-B 门禁已完成；M2-B 用户确认绑定执行 bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`。最后一次人工顶层 `GKD-M2-C automatic runtime bridge` 已登记在 worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-automatic-runtime-bridge`、branch `task/m2-automatic-runtime-bridge`、PR #7。初始 manual claim 因公开 CLI 固定 unavailable evidence provider 且 service 对 manual claim 仍要求 runtime evidence，返回 `RUNTIME_EVIDENCE_UNAVAILABLE`；main 已撤销 offer/envelope，当前候选 head `a7208f2d796ec62b3ddb300730d8e9b37be9a56e`、phase `planning`、epoch 1、revision 5。用户已批准一次性 bootstrap exception：固定任务文档、人工顶层 Session、独立 worktree/PR 和 fixed-head 验收作为权威，不运行或伪造 claim/deliver。该例外仅限 M2-C；M3 必须使用 M2-C 实现的正式自动桥。M3 已拆为 A fixed-head CI/policy、B 资源与防泄漏 core、C 两项新 Skill/review core。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
