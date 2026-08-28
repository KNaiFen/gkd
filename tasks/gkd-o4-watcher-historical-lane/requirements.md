# GKD-O4 Requirements

## Goal

收窄默认 GKD verifier：默认路径只验证核心 task/role/bridge/CI/release 合同；watcher core、M-1C live probe 与其历史负向合同改为显式 historical lane。不得改变 watcher 行为、历史结论或核心 role/wait/bridge 合同。

## User Decisions

- O4 必须从 O3 accepted merge `9009b089fb811eceaf91ada8b60397b39a451f97` 之后的 trusted main 完整基线开始。
- 只允许一个精确 `gkd_executor` 交付，独立 `gkd_acceptor` 验收，trusted main 合并和清理。
- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。
- 不删除 `src/gkd_watchdog`、`scripts/gkd-watchdog-mcp`、`probes/app-server-watcher`、M-1B/M-1C 历史 evidence 或 watcher 行为测试。

## Scope

- 从 `scripts/gkd-verify` 的默认 `SCOPES` 移除 `watcher-core-and-live-negative`，使默认结果不再执行 watcher/probe 合同。
- 增加显式、可追溯的 historical watcher verifier 入口；它必须能独立运行 watcher core contracts，并明确是否运行真实 host-capability probe，不得静默把 live probe 混入默认路径。
- 为默认与 historical lane 提供稳定的 scope/result 标识、base/head 绑定和错误退出码；复用 O3 canonical result consumer 时必须完整校验 test IDs、manifest digest 和固定 head。
- 更新 README、测试入口、manifest/lock 和必要 schema，使安装包能发现两个 lane，且历史 lane 只在显式调用时加载。
- 保留现有 watcher tests、`tests/probes/test_native_probe.py`、M-1B evidence 读取和 M-1C `unsupported` 结论；若 live probe 需要真实宿主能力，默认只提供显式诊断入口，不把未运行解释为通过。

## Non-Goals

- 不重写 watcher 协议、MCP adapter、app-server 控制逻辑、native probe 或其安全/清理语义。
- 不删除历史 fixtures/evidence，不把 M-1C `unsupported` 改写为 supported，不启用 automatic route。
- 不拆 O5 runtime fixtures、O6 optional pack、O7 contract index，也不改变生产/AIO。

## Acceptance Criteria

1. `scripts/gkd-verify --base-sha <full-base-sha>` 默认结果不包含 watcher/probe scope，并成功生成 O3 canonical result manifest。
2. 显式 historical lane 能独立执行全部 watcher core contracts，或在缺少真实宿主能力时返回稳定、可追溯的 fail-closed 诊断；不能伪造 live success。
3. 默认与 historical lane 的 scope/test ID、base/head、verifier digest 和结果 manifest 均可验证；结果消费者对缺失、未知、篡改和 head/digest drift 继续拒绝。
4. watcher core、native probe、M-1B/M-1C 历史相关测试覆盖不下降；至少两次 historical evidence 生成结果逐字节一致。
5. candidate bundle、manifest/lock、README 和 task delivery 事实一致；固定头 `GKD Verify` 与独立 acceptor 通过。
6. 变更不引入绝对本机路径、用户名、凭据、新依赖或生产/AIO/GitHub settings 副作用。

