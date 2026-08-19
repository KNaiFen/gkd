# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A fixed head `b579926aaff50d40b462e7f21cf91c9709eeb3a3` 已独立验收并以 merge commit `9351d628d198ec8638311901cf288abadc643a42` 进入 main，候选 worktree/分支已清理。F-004 离线归一化要求唯一 `agents.spawn_agent`、精确 `gkd_executor`/`gkd_executor_handshake`/`none` 参数、对应 activity child identity 和 exact child/parent terminal，downgrade/fallback 从实际事件计算；raw rollout 未复制进仓库。F-005 采用 trusted-main 工作流权限边界：`TrustedMainActivationAuthority` 生成 exact activation receipt 并桥接 claim/delivery，候选公开 CLI 与默认 library 路径继续 fail-closed；同 OS 用户 monkeypatch/private API/direct runtime tamper 为非目标，不引入签名、daemon、IPC 或密钥。M2-A outcome 为 `role_routing_core_ready`，route 仍 `manual_only`；下一步只有人工 M2-B fresh-runtime 一小时门，M2-B 通过前 auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。长会话复盘见 `tasks/m2-role-routing-core/retrospective.md`。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
