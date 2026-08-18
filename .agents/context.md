# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；`GKD-M2-A` 已在独立 worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-role-routing-core`、branch `task/m2-role-routing-core` 实现固定角色、路由、等待、activation receipt、安装迁移和五个 workflow Skills。PR #6 正在交付 fixed head，最终结论受可信 fresh host role handshake 阻塞。M2-A hermetic/L2 合同 51 项、task-core 104、foundation 53、watcher core 47、watcher live-negative 15 均通过；两次 M2 evidence 逐字节一致，bundle content digest 为 `943301005912c05bb137d6c44a597e4569e05e9f0e738adaec4a8b675f654649`，evidence digest 为 `efe08577c4eabfb91938d2d93473ed142ded4bbe4f651c591a8d830624fbec8c`，结论为 `blocked`。唯一一次短时握手仅观察到四类 host event、无 child/parent terminal，不能证明 custom role activation；不得用自报告升级。M2 拆为 M2-A 确定性角色/路由核心与 M2-B fresh-runtime 一小时 live gate；M2-A 不运行真实一小时等待，auto route 继续禁用；生产安装与 AIO 仍未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
