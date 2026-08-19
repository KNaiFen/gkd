# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；`GKD-M2-A` PR #6 最新交付 head `0c200bc9cfbdf6da62e53ed6eb7ff579b964f3da` 的 deterministic/L2 返工通过既有短合同，但独立验收发现安装态 `record_activation` 仍可被候选等权限进程直接调用并令 claim 成功（F-005）。用户于 2026-08-19 授权一次额外的本机登录态真实握手：使用正常 ChatGPT Codex 登录、临时 Git repo 的项目级 `.codex/agents`/`.codex/skills` 和 ephemeral parent，不设置 alternate `CODEX_HOME`，不读取/复制认证材料，不安装或修改生产 `~/.codex`。任务 requirements/plan/implementation 升为 v2，execution 回到 `awaiting_manual_rework`；F-004 待该唯一 probe，F-005 待修复。M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
