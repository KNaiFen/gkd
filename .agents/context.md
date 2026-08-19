# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-001 至 F-005 保持已整改且本轮未改动业务设计。用户在 fresh probe repo 的正常 Codex trust UI 中明确选择继续后，session rollout 记录证明 parent 通过 `agents.spawn_agent` 唯一启动 `gkd_executor`，child 与 parent 均有独立 `task_complete` terminal marker，Codex exit 0；stdout 的 wait-only 压缩不再作为完整 host 事实。F-004 与 M2-A outcome 已规范化为 `role_routing_core_ready`，仍保持 `manual_only`；M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。用户信任动作使生产 Codex 配置 digest 从 `db47d57e...` 变为 `f1b9cb27...`，execution session 未写入或回滚该配置；raw host rollout 保留在宿主 session 存储，未复制进仓库证据。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
