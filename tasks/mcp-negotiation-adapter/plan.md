# MCP 协商适配

## 目标

根据当前 Codex CLI 运行时事实，收紧 GKD 的 MCP 协商适配：已登记版本明确协商，未知版本显式报告不支持，不再静默回退；适配器元数据必须来自实际协议字段或明确的历史证据。

## 范围

- `src/gkd_watchdog/mcp_server.py`
- `probes/app-server-watcher/mcp_adapter.py`
- MCP 相关单元测试、夹具与证据
- 本任务的 `progress.md`、`review.md` 以及必要的 `.agents/` 状态记录

## 约束

- 不虚构 Codex CLI 尚未提供的 MCP 2026 协议支持；当前 `mcp_2026_07_28` 仍是 under development。
- 保留现有已登记旧版本的历史行为及负向测试语义，必要时只将静默回退改为可观测的不支持结果。
- 不修改 `turn/steer`；该项是本修复计划的最后阶段。
- 不修改生产 `~/.codex`、AIO、GitHub 设置、Secrets、runner 或 release。
- 不记录原始敏感 payload；测试使用最小脱敏夹具。

## 完成标准

1. 已知协议版本仍能通过现有协商测试。
2. 未知请求版本不再选择首选版本静默响应，而是返回稳定、可断言的不支持结果。
3. 元数据版本/字段校验有测试覆盖，且不把推测字段当成真实事件。
4. 相关测试、仓库校验、bundle 生成和 `git diff --check` 通过，并在 `progress.md` 记录证据。
