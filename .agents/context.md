# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；`GKD-M2-A` 在候选 worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-role-routing-core`、branch `task/m2-role-routing-core` 完成人工返工，implementation/evidence commit 为 `b64cab4e76f5ddd372a682531fe5802067a3c1c0`。F-001 迁移冻结保全、F-002 固定 activation provider/offer window、F-003 absolute deadline 已修复，M2 55、task-core 104、foundation 53、watcher core 47、live-negative 15 均通过；两份 M2 evidence 逐字节一致，bundle digest 为 `6e9cc8a73fa9e80e3a3061114f53c3daf152439a2886e40000e07d19b9c37a6b`，evidence digest 为 `5092c31dd1aaab13623e1131da84e248eb4af0018ce0c37f1a63ba85161b00b6`。唯一 fresh handshake 被宿主以 ChatGPT-account runtime 不支持 `gpt-5.6-sol` 拒绝，无 custom-role activation 或 child/parent terminal，因此 F-004 与 outcome 继续 `blocked`，PR #6 保持 Draft、未合并。M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
