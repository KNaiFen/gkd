# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-005 保持已整改且未变更。F-004 v4 在授权 head `26b8e9c185a0bdf365266efdb45f42260c8922b3` 通过四方 head、clean worktree、Codex digest、非 strict 静态 preflight、零调用计数和生产/AIO digest 启动门后，使用正常用户 provider/auth/model routing 执行唯一一次 live probe。Codex exit 0 且 parent turn/terminal 已观察，但 host JSONL 只有无 receiver/agent state 的 collab `wait`，没有 custom-role spawn/activation、child identity 或 child terminal；分类 `CUSTOM_ROLE_ACTIVATION_MISSING`，`modelInvocations=1`、`liveAttemptsConsumed=1`。原始 JSONL/临时 repo 已删除，保护面不变。F-004 与总体继续 `blocked`；M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
