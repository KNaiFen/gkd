# Review

## 结论

主代理审查通过，已合并到 `refactor/manual-first-workflow`。

## 变更范围

- `McpServer` 与 live MCP adapter 共用显式协议版本 registry；已登记 `2025-06-18`、`2024-11-05` 保持原协商结果。
- 未知/缺失版本（含仍 under development 的 `mcp_2026_07_28`）返回固定 JSON-RPC `-32602` / `unsupported protocol version`，不选择首选版本、不回显未知值。
- correlation metadata 只消费既有历史 watcher 合同已经使用的字段；顶层或嵌套字段漂移 fail-closed，不把猜测字段归一化为身份事实。
- `tasks/mcp-negotiation-adapter/evidence.json` 仅保存版本/字段名和稳定 unsupported 结果，SHA-256 为 `9bb2c0552cb755bc097dd3c2fde0355de15c5762e2810dd48e6e9927785494c9`；没有原始 payload、身份值或路径。
- 仅修改 MCP 源文件、探针适配器、MCP/探针测试、contract catalog 和本任务文档；未修改 turn/steer、生产/AIO、GitHub 或发布资产。

## 验证

- watchdog 专项 26/26、watchdog 全量 55/55 通过。
- `gkd-verify --scope-internal watcher-core-and-live-negative`：55/55 通过。
- bundle generator 输出既有 development bundle `0.0.0-dev.1` / `9a683001…`，未改变 canonical manifest/lock。
- `git diff --check` 与 Python compileall 通过。

## 主代理复核

- 已核对源代码差异：未知版本和缺失版本均经过同一显式协商路径，不再静默选择首选版本。
- 已核对 `mcp_2026_07_28` 只作为负向夹具和 under-development 记录出现，没有被加入支持注册表。
- 已核对 live adapter 与服务端复用同一注册表，避免两套协议版本事实漂移。

## 剩余风险

- `mcp_2026_07_28` 没有被实现或宣称支持；未来 CLI/协议或 correlation metadata 发生变化时，需先取得真实脱敏 capture，再单独登记版本/字段并补验证。
